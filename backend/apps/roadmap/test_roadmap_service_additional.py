from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from apps.roadmap.models import Exam, Roadmap, RoadmapTopic, Subject, Topic
from apps.roadmap.services.roadmap_service import RoadmapService


@pytest.mark.django_db
def test_generate_deterministic_roadmap_orchestrates_dependencies(user, monkeypatch):
    exam = Exam.objects.create(
        name="GATE ME",
        category="Engineering",
        total_marks=100,
        exam_date=date.today() + timedelta(days=120),
    )
    called = {}

    monkeypatch.setattr("apps.roadmap.services.roadmap_service.Exam.objects.get", lambda id: exam)
    monkeypatch.setattr(
        "apps.roadmap.services.roadmap_service.WeightageService.compute_weightage",
        lambda arg_exam: called.setdefault("weightage", arg_exam.id),
    )
    monkeypatch.setattr(
        "apps.roadmap.services.roadmap_service.TimeDistributionService.generate_plan",
        lambda *_a, **_k: {"total_weeks": 1, "plan": []},
    )
    monkeypatch.setattr(
        "apps.roadmap.services.roadmap_service.RoadmapService._create_roadmap",
        lambda *_a, **_k: "roadmap-created",
    )

    result = RoadmapService.generate_deterministic_roadmap(
        user=user,
        exam_id=exam.id,
        target_date=date.today() + timedelta(days=90),
        study_hours_per_day=4,
    )
    assert result == "roadmap-created"
    assert called["weightage"] == exam.id


@pytest.mark.django_db
def test_create_week_topics_with_empty_items_uses_fallback(user, exam):
    roadmap = Roadmap.objects.create(
        user=user,
        exam=exam,
        target_date=date.today() + timedelta(days=30),
        total_weeks=1,
        is_active=True,
    )
    subject = Subject.objects.create(exam=exam, name="DSA", order=1)
    fallback = Topic.objects.create(name="Fallback", subject=subject)

    RoadmapService._create_week_topics(
        roadmap=roadmap,
        week_data={"week_number": 1, "items": []},
        global_fallback=fallback,
        daily_limit=3.0,
    )

    entries = list(RoadmapTopic.objects.filter(roadmap=roadmap).order_by("day_number"))
    assert len(entries) == 2
    assert entries[0].day_number == 6 and entries[0].topic == fallback
    assert entries[1].day_number == 7 and entries[1].topic == fallback


@pytest.mark.django_db
def test_create_week_topics_splits_study_items_across_days(user, exam):
    roadmap = Roadmap.objects.create(
        user=user,
        exam=exam,
        target_date=date.today() + timedelta(days=30),
        total_weeks=1,
        is_active=True,
    )
    subject = Subject.objects.create(exam=exam, name="OS", order=1)
    t1 = Topic.objects.create(name="T1", subject=subject)
    t2 = Topic.objects.create(name="T2", subject=subject)

    RoadmapService._create_week_topics(
        roadmap=roadmap,
        week_data={
            "week_number": 1,
            "items": [{"topic": t1, "hours": 4.0}, {"topic": t2, "hours": 1.0}],
        },
        global_fallback=t1,
        daily_limit=2.0,
    )

    week_entries = RoadmapTopic.objects.filter(roadmap=roadmap, week_number=1)
    assert week_entries.filter(day_number=6, phase="revision").exists()
    assert week_entries.filter(day_number=7, phase="practice").exists()
    assert week_entries.filter(day_number=1, phase="study").exists()
    assert week_entries.filter(day_number=2, phase="study").exists()


@pytest.mark.django_db
def test_get_user_roadmap_returns_empty_when_no_active_items(user):
    assert RoadmapService.get_user_roadmap(user) == []


@pytest.mark.django_db
def test_get_user_roadmap_builds_sorted_adaptive_output(user, exam, monkeypatch):
    roadmap = Roadmap.objects.create(
        user=user,
        exam=exam,
        target_date=date.today() + timedelta(days=45),
        total_weeks=1,
        is_active=True,
    )
    subject = Subject.objects.create(exam=exam, name="Math", order=1)
    weak_topic = Topic.objects.create(name="Weak Topic", subject=subject)
    strong_topic = Topic.objects.create(name="Strong Topic", subject=subject)

    RoadmapTopic.objects.create(
        roadmap=roadmap, topic=strong_topic, week_number=1, day_number=1, phase="study"
    )
    RoadmapTopic.objects.create(
        roadmap=roadmap, topic=weak_topic, week_number=1, day_number=1, phase="study"
    )

    monkeypatch.setattr(
        "apps.roadmap.services.roadmap_service.AdaptiveRoadmapService.get_revision_map",
        lambda _user: {
            weak_topic.id: {"strength": "weak", "priority": 9},
            strong_topic.id: {"strength": "strong", "priority": 1},
        },
    )

    data = RoadmapService.get_user_roadmap(user)
    assert len(data) == 1
    assert data[0]["week"] == 1
    assert data[0]["day"] == 1
    assert data[0]["topics"][0]["topic_id"] == weak_topic.id
    assert data[0]["topics"][0]["adaptive"]["is_revision"] is True


def test_build_topic_item_without_adaptive_map_defaults():
    item = SimpleNamespace(
        topic=SimpleNamespace(id=11, name="A"),
        estimated_hours=3,
        phase="study",
    )
    out = RoadmapService._build_topic_item(item, revision_map={})
    assert out["adaptive"]["strength"] == "unknown"
    assert out["adaptive"]["priority"] == 0
    assert out["adaptive"]["is_revision"] is False

