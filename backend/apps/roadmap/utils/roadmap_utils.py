import logging

from django.utils import timezone
from django.shortcuts import get_object_or_404

from ..models import Roadmap, RoadmapTopic, Exam
from ..serializers import RoadmapSerializer, RoadmapTopicSerializer, ExamSerializer
from ..services.roadmap_service import RoadmapService
from ..services.progress_service import ProgressService
from ..services.study_service import StudyService
from apps.analytics.services.adaptive_service import AdaptiveRoadmapService

logger = logging.getLogger(__name__)


def get_exams():
    exams = Exam.objects.all()
    return ExamSerializer(exams, many=True).data, None, None


def get_roadmaps(user):
    roadmaps = (
        Roadmap.objects.filter(user=user)
        .select_related("exam")
        .prefetch_related("topics__topic__parent")
    )
    return RoadmapSerializer(roadmaps, many=True).data, None, None


def get_roadmap_detail(user, pk):
    roadmap = get_object_or_404(
        Roadmap.objects.select_related("exam").prefetch_related(
            "topics__topic__parent"
        ),
        pk=pk,
        user=user,
    )
    return RoadmapSerializer(roadmap).data, None, None


def update_roadmap(user, pk, request_data):
    roadmap = get_object_or_404(
        Roadmap.objects.select_related("exam").prefetch_related(
            "topics__topic__parent"
        ),
        pk=pk,
        user=user,
    )

    if request_data.get("action") == "complete" and "topic_id" in request_data:
        topic = RoadmapService.mark_topic_completed(
            request_data["topic_id"], user
        )
        if not topic:
            return None, {"error": "Topic not found"}
        return RoadmapTopicSerializer(topic).data, None

    serializer = RoadmapSerializer(roadmap, data=request_data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return serializer.data, None


def delete_roadmap(user, pk):
    roadmap = get_object_or_404(
        Roadmap.objects.select_related("exam").prefetch_related(
            "topics__topic__parent"
        ),
        pk=pk,
        user=user,
    )
    roadmap.delete()


def serialize_topics(topics):
    return [
        {
            "id": t.id,
            "day": t.day_number,
            "topic": t.topic.name,
            "hours": t.estimated_hours,
            "completed": t.is_completed,
            "subject": t.topic.parent.name if t.topic.parent else None,
            "phase": t.phase,
        }
        for t in topics
    ]


def group_topics_by_day(topics):
    day_groups = {}
    for t in topics:
        day_groups.setdefault(t.day_number, []).append(t)
    return day_groups


def find_current_day(day_groups):
    if not day_groups:
        return 1
    for day in sorted(day_groups.keys()):
        if not all(t.is_completed for t in day_groups[day]):
            return day
    return max(day_groups.keys())


def get_revision_topics(user, roadmap_id, current_day, day_groups):
    if current_day == 1:
        return []
    priority_topics = AdaptiveRoadmapService.generate_priority(user)
    weak_topics = [t for t in priority_topics if t["strength"] == "weak"]
    today_topic_ids = {t.topic_id for t in day_groups.get(current_day, [])}
    roadmap_topics_map = {
        t.topic_id: t.id for t in RoadmapTopic.objects.filter(roadmap_id=roadmap_id)
    }

    revision = []
    for t in weak_topics:
        if t["topic_id"] in today_topic_ids:
            continue
        roadmap_topic_id = roadmap_topics_map.get(t["topic_id"])
        if roadmap_topic_id:
            revision.append(
                {
                    "topic_id": t["topic_id"],
                    "topic_name": t["topic_name"],
                    "priority": t["priority"],
                    "roadmap_topic_id": roadmap_topic_id,
                }
            )
    return revision[:3]


def get_week_plan(roadmap_id, week_number):
    from apps.analytics.services.adaptive_service import AdaptiveRoadmapService

    topics = (
        RoadmapTopic.objects.select_related("topic", "topic__parent", "roadmap__user")
        .filter(roadmap_id=roadmap_id, week_number=week_number)
        .order_by("day_number")
    )

    data = serialize_topics(topics)
    day_groups = group_topics_by_day(topics)
    current_day = find_current_day(day_groups)

    revision = []
    if topics:
        user = topics[0].roadmap.user
        if current_day > 1:
            priority_topics = AdaptiveRoadmapService.generate_priority(user)
            weak_topics = [t for t in priority_topics if t["strength"] == "weak"]
            today_topic_ids = {t.topic_id for t in day_groups.get(current_day, [])}
            roadmap_topics_map = {
                t.topic_id: t.id for t in RoadmapTopic.objects.filter(roadmap_id=roadmap_id)
            }
            for t in weak_topics:
                if t["topic_id"] in today_topic_ids:
                    continue
                roadmap_topic_id = roadmap_topics_map.get(t["topic_id"])
                if roadmap_topic_id:
                    revision.append(
                        {
                            "topic_id": t["topic_id"],
                            "topic_name": t["topic_name"],
                            "priority": t["priority"],
                            "roadmap_topic_id": roadmap_topic_id,
                        }
                    )
            revision = revision[:3]

    return {"status": "success", "data": data, "today_revision": revision}, None, None


def toggle_topic_completion(topic_id):
    topic = get_object_or_404(RoadmapTopic, id=topic_id)
    topic.is_completed = not topic.is_completed

    if topic.is_completed:
        topic.completed_at = timezone.now()
    else:
        topic.completed_at = None

    topic.save()
    return {"topic_id": topic.id, "completed": topic.is_completed}, None, None


def get_week_progress(roadmap_id, week_number):
    return ProgressService.get_week_progress(roadmap_id, week_number), None, None


def get_overall_progress(roadmap_id):
    return ProgressService.get_overall_progress(roadmap_id), None, None


def get_topic_study_data(topic_id):
    return StudyService.get_topic_study_data(topic_id), None, None


def get_roadmap_topics(roadmap_id):
    return StudyService.get_roadmap_topics(roadmap_id), None, None


def activate_roadmap(user, roadmap_id):
    from django.db import transaction

    roadmap = Roadmap.objects.filter(id=roadmap_id, user=user).first()
    if not roadmap:
        return None, {"error": "Roadmap not found"}, 404

    with transaction.atomic():
        Roadmap.objects.filter(user=user, is_active=True).update(is_active=False)
        roadmap.is_active = True
        roadmap.save()

    return {"message": "Roadmap activated"}, None, None


def generate_roadmap(user, exam_id, target_date, study_hours_per_day):
    try:
        exam = Exam.objects.get(id=exam_id)
    except Exam.DoesNotExist:
        return None, {"error": "Exam not found"}, 404

    try:
        roadmap = RoadmapService.generate_deterministic_roadmap(
            user=user,
            exam_id=exam.id,
            target_date=target_date,
            study_hours_per_day=study_hours_per_day,
        )
    except Exception as e:
        logger.error(f"Roadmap generation failed: {e}", exc_info=True)
        return None, {"error": f"Failed to generate roadmap: {str(e)}"}, 500

    return {
        "roadmap_id": roadmap.id,
        "total_weeks": roadmap.total_weeks,
        "message": "Roadmap generated successfully",
    }, None, None