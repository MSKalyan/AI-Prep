from collections import deque
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from apps.roadmap.models import PYQ, RoadmapTopic, Subject, Topic
from apps.roadmap.services.adaptive_service import AdaptiveRoadmapService
from apps.roadmap.services.pyq.time_distribution_service import (
    DayDistributionService,
    TimeDistributionService,
)
from apps.roadmap.services.pyq.weightage_service import WeightageService


def test_compute_topic_accuracy_handles_correct_incorrect_and_missing_topic(monkeypatch):
    topic_a = object()
    topic_b = object()

    answers = [
        SimpleNamespace(question=SimpleNamespace(topic_obj=topic_a), is_correct=True),
        SimpleNamespace(question=SimpleNamespace(topic_obj=topic_a), is_correct=False),
        SimpleNamespace(question=SimpleNamespace(topic_obj=topic_b), is_correct=True),
        SimpleNamespace(question=SimpleNamespace(topic_obj=None), is_correct=True),
    ]

    class FakeQuerySet:
        def select_related(self, *_args, **_kwargs):
            return answers

    class FakeManager:
        def filter(self, **_kwargs):
            return FakeQuerySet()

    monkeypatch.setattr(
        "apps.roadmap.services.adaptive_service.Answer",
        SimpleNamespace(objects=FakeManager()),
    )

    result = AdaptiveRoadmapService.compute_topic_accuracy(user=object(), roadmap=object())

    assert result[topic_a] == 50.0
    assert result[topic_b] == 100.0


@pytest.mark.django_db
def test_get_today_revision_filters_today_topics_and_applies_limit(user, exam, roadmap):
    subject = Subject.objects.create(exam=exam, name="OS", order=2)
    topic_today = Topic.objects.create(name="Scheduling", subject=subject)
    topic_weak_1 = Topic.objects.create(name="Paging", subject=subject)
    topic_weak_2 = Topic.objects.create(name="Deadlock", subject=subject)
    topic_strong = Topic.objects.create(name="Threads", subject=subject)

    RoadmapTopic.objects.create(
        roadmap=roadmap,
        topic=topic_today,
        week_number=1,
        day_number=1,
        phase="coverage",
    )

    priorities = [
        {"topic_id": topic_today.id, "strength": "weak"},
        {"topic_id": topic_weak_1.id, "strength": "weak"},
        {"topic_id": topic_strong.id, "strength": "strong"},
        {"topic_id": topic_weak_2.id, "strength": "weak"},
    ]

    service = AdaptiveRoadmapService
    original = getattr(service, "generate_priority", None)
    service.generate_priority = staticmethod(lambda _user: priorities)
    try:
        result = service.get_today_revision(user=user, limit=1)
    finally:
        if original is None:
            delattr(service, "generate_priority")
        else:
            service.generate_priority = original

    assert result == [{"topic_id": topic_weak_1.id, "strength": "weak"}]


@pytest.mark.parametrize(
    "topics,expected_keys",
    [
        ([SimpleNamespace(subject_id=1), SimpleNamespace(subject_id=1)], {1}),
        ([SimpleNamespace(subject_id=None), SimpleNamespace(subject_id=3)], {0, 3}),
    ],
)
def test_group_topics_by_subject_handles_null_subject_ids(topics, expected_keys):
    grouped = TimeDistributionService._group_topics_by_subject(topics)
    assert set(grouped.keys()) == expected_keys


def test_allocate_from_topic_skips_tiny_allocation_under_half_hour():
    queue = deque([SimpleNamespace(weightage=1)])
    items, current_hours = TimeDistributionService._allocate_from_topic(queue, target_h=0.4)
    assert items == []
    assert current_hours == 0


def test_build_plan_with_single_subject_allocates_without_crashing():
    topic = SimpleNamespace(weightage=4.0, name="T1")
    subj_map = {11: deque([topic])}
    plan = TimeDistributionService._build_plan(total_weeks=1, subj_map=subj_map, weekly_study_h=10.0)
    assert plan["total_weeks"] == 1
    assert plan["plan"][0]["week_number"] == 1
    assert len(plan["plan"][0]["items"]) >= 1


def test_day_distribution_splits_hours_across_days_and_stops_after_day5():
    week_items = [{"topic": "A", "hours": 7.0}, {"topic": "B", "hours": 6.0}]
    days = DayDistributionService.distribute_week(week_items, daily_limit=2.0)
    assert all(1 <= item["day"] <= 5 for item in days)
    assert sum(item["hours"] for item in days) == 10.0


@pytest.mark.django_db
def test_compute_weightage_zero_total_marks_exits_early_with_message(exam, capsys):
    WeightageService.compute_weightage(exam)
    out = capsys.readouterr().out
    assert "No PYQs found for weightage computation" in out


@pytest.mark.django_db
def test_compute_weightage_updates_parent_and_projects_children(exam):
    subject = Subject.objects.create(exam=exam, name="Math", order=1)
    parent = Topic.objects.create(name="Linear Algebra", subject=subject, parent=None)
    child1 = Topic.objects.create(name="Vectors", subject=subject, parent=parent)
    child2 = Topic.objects.create(name="Matrices", subject=subject, parent=parent)

    PYQ.objects.create(
        exam=exam,
        topic=parent,
        year=date.today().year - 1,
        marks=10,
        question_type="mcq",
        question_text="q1",
        source_url="https://example.com/1",
    )
    PYQ.objects.create(
        exam=exam,
        topic=parent,
        year=date.today().year - 2,
        marks=10,
        question_type="mcq",
        question_text="q2",
        source_url="https://example.com/2",
    )

    WeightageService.compute_weightage(exam)
    parent.refresh_from_db()
    child1.refresh_from_db()
    child2.refresh_from_db()

    assert parent.pyq_total_marks == 20
    assert parent.pyq_count == 2
    assert parent.weightage == 100
    assert child1.weightage == 50
    assert child2.weightage == 50


def test_project_children_weightage_no_children_no_bulk_update(monkeypatch):
    bulk_update = Mock()
    monkeypatch.setattr("apps.roadmap.services.pyq.weightage_service.Topic.objects.bulk_update", bulk_update)
    WeightageService._project_children_weightage(SimpleNamespace(weightage=80), [])
    bulk_update.assert_not_called()
