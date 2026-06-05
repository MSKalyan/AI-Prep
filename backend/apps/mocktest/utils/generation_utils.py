import logging

from apps.roadmap.models import Roadmap, Topic, RoadmapTopic
from ..services.test_creation_service import TestCreationService
from ..serializers import MockTestDetailSerializer, TestAttemptSerializer

logger = logging.getLogger(__name__)


def validate_generate_request(request):
    roadmap_id = request.data.get("roadmap_id")
    day = request.data.get("day")
    if not roadmap_id or day is None:
        return None, {"error": "roadmap_id and day required"}, 400

    return {
        "roadmap_id": roadmap_id,
        "day": day,
        "topic_id": request.data.get("topic_id"),
        "num_questions": request.data.get("num_questions", 10),
    }, None, None


def get_roadmap_topics(roadmap_id, day, topic_id=None):
    roadmap = Roadmap.objects.get(id=roadmap_id)
    queryset = Topic.objects.filter(
        roadmap_entries__roadmap=roadmap,
        roadmap_entries__day_number=day
    )

    if topic_id:
        topic_match = queryset.filter(id=topic_id).distinct()
        if topic_match.exists():
            return roadmap, list(topic_match)

        roadmap_entry = (
            RoadmapTopic.objects.filter(
                id=topic_id,
                roadmap=roadmap,
            )
            .select_related("topic")
            .first()
        )
        if roadmap_entry and roadmap_entry.topic_id:
            return roadmap, list(
                Topic.objects.filter(
                    id=roadmap_entry.topic_id,
                    roadmap_entries__roadmap=roadmap,
                ).distinct()
            )
        return roadmap, []

    return roadmap, list(queryset.distinct())


def create_mock_test(user, roadmap, data, topics):
    result = TestCreationService.create_mock_test(
        user=user,
        roadmap=roadmap,
        day=data["day"],
        topics=topics,
        num_questions=data["num_questions"],
    )
    return {
        "mock_test": MockTestDetailSerializer(result["mock_test"]).data,
        "attempt": TestAttemptSerializer(result["attempt"]).data,
    }