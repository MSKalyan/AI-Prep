from datetime import date, timedelta

import pytest

from apps.analytics.services.roadmap_service import RoadmapService
from apps.roadmap.models import Roadmap, RoadmapTopic, Subject, Topic


@pytest.mark.django_db
def test_generate_adaptive_roadmap_returns_empty_when_no_items(user):
    assert RoadmapService.generate_adaptive_roadmap(user) == []


@pytest.mark.django_db
def test_generate_adaptive_roadmap_dedups_and_assigns_revisions(user, exam, monkeypatch):
    roadmap = Roadmap.objects.create(
        user=user,
        exam=exam,
        target_date=date.today() + timedelta(days=60),
        total_weeks=2,
        is_active=True,
    )
    subject = Subject.objects.create(exam=exam, name="Compiler", order=1)
    t1 = Topic.objects.create(name="Lex", subject=subject)
    t2 = Topic.objects.create(name="Parse", subject=subject)
    t3 = Topic.objects.create(name="Codegen", subject=subject)

    RoadmapTopic.objects.create(roadmap=roadmap, topic=t1, week_number=1, day_number=1, phase="study")
    RoadmapTopic.objects.create(roadmap=roadmap, topic=t2, week_number=1, day_number=2, phase="study")

    monkeypatch.setattr(
        "apps.analytics.services.roadmap_service.AdaptiveRoadmapService.generate_priority",
        lambda _user: [
            {"topic_id": t3.id, "topic_name": t3.name, "strength": "weak", "priority": 10},
            {"topic_id": t2.id, "topic_name": t2.name, "strength": "weak", "priority": 8},
        ],
    )

    out = RoadmapService.generate_adaptive_roadmap(user)
    assert len(out) == 2
    assert len(out[0]["learn_topics"]) == 1
    assert out[0]["learn_topics"][0]["topic_id"] == t1.id
    assert out[0]["revisions"][0]["topic_id"] == t3.id
    assert out[1]["revisions"][0]["topic_id"] == t2.id


@pytest.mark.django_db
def test_generate_adaptive_roadmap_falls_back_to_top3_when_no_weak(user, exam, monkeypatch):
    roadmap = Roadmap.objects.create(
        user=user,
        exam=exam,
        target_date=date.today() + timedelta(days=60),
        total_weeks=1,
        is_active=True,
    )
    subject = Subject.objects.create(exam=exam, name="DBMS", order=1)
    t1 = Topic.objects.create(name="T1", subject=subject)
    RoadmapTopic.objects.create(roadmap=roadmap, topic=t1, week_number=1, day_number=1, phase="study")

    monkeypatch.setattr(
        "apps.analytics.services.roadmap_service.AdaptiveRoadmapService.generate_priority",
        lambda _user: [
            {"topic_id": 101, "topic_name": "A", "strength": "moderate", "priority": 3},
            {"topic_id": 102, "topic_name": "B", "strength": "strong", "priority": 2},
            {"topic_id": 103, "topic_name": "C", "strength": "strong", "priority": 1},
        ],
    )
    out = RoadmapService.generate_adaptive_roadmap(user)
    assert out[0]["revisions"][0]["topic_id"] == 101


@pytest.mark.django_db
def test_get_today_plan_returns_empty_when_no_roadmap(user):
    assert RoadmapService.get_today_plan(user) == {}


@pytest.mark.django_db
def test_get_today_plan_returns_first_day_and_optional_revision(user, exam, monkeypatch):
    roadmap = Roadmap.objects.create(
        user=user,
        exam=exam,
        target_date=date.today() + timedelta(days=60),
        total_weeks=1,
        is_active=True,
    )
    subject = Subject.objects.create(exam=exam, name="CN", order=1)
    t1 = Topic.objects.create(name="TCP", subject=subject)
    t2 = Topic.objects.create(name="UDP", subject=subject)
    RoadmapTopic.objects.create(roadmap=roadmap, topic=t1, week_number=1, day_number=1, phase="study")
    RoadmapTopic.objects.create(roadmap=roadmap, topic=t2, week_number=1, day_number=2, phase="study")

    monkeypatch.setattr(
        "apps.analytics.services.roadmap_service.AdaptiveRoadmapService.generate_priority",
        lambda _user: [{"topic_id": t2.id, "topic_name": t2.name, "strength": "weak", "priority": 9}],
    )
    out = RoadmapService.get_today_plan(user)
    assert out["week"] == 1
    assert out["day"] == 1
    assert out["learn_topics"][0]["topic_id"] == t1.id
    assert out["revision"]["topic_id"] == t2.id
