import logging
from django.db.models import Sum

from ..models import TopicPerformance
from ..services.performance_service import PerformanceService
from ..services.roadmap_service import RoadmapService
from ..services.study_content_service import StudyContentService
from ..services.services import AnalyticsService
from apps.mocktest.models import MockTest, Answer
from ..serializers import (
    PerformanceMetricsSerializer,
    WeakAreaSerializer,
    DailyProgressSerializer,
)

logger = logging.getLogger(__name__)


def get_topic_performance(user):
    topics = PerformanceService.compute_and_store(user)
    total_mocktests = MockTest.objects.filter(user=user).count()
    total_questions = TopicPerformance.objects.filter(user=user).aggregate(
        total=Sum('total_attempts')
    )['total'] or 0

    return {
        "status": "success",
        "data": {
            "topics": topics,
            "total_mocktests": total_mocktests,
            "total_questions_attempted": total_questions
        }
    }, None, None


def get_adaptive_study_plan(user):
    data = RoadmapService.generate_adaptive_roadmap(user)
    return {"status": "success", "data": data}, None, None


def get_study_content(topic_name):
    if not topic_name:
        return None, {"error": "topic_name is required"}, 400

    data = StudyContentService.get_study_content(topic_name)
    if not data:
        return None, {"error": "Topic not found"}, 404

    return {"status": "success", "data": data}, None, None


def get_user_analytics(user):
    try:
        analytics_data = AnalyticsService.get_user_analytics(user)
        total_mocktests = MockTest.objects.filter(user=user).count()
        total_questions = Answer.objects.filter(attempt__user=user).count()

        response_data = {
            'overall_stats': analytics_data['overall_stats'],
            'subject_performance': PerformanceMetricsSerializer(
                analytics_data['subject_performance'], many=True
            ).data,
            'weak_areas': WeakAreaSerializer(
                analytics_data['weak_areas'], many=True
            ).data,
            'recent_progress': DailyProgressSerializer(
                analytics_data['recent_progress'], many=True
            ).data,
            'study_streak': analytics_data['study_streak'],
            'total_study_time': analytics_data['total_study_time'],
            'total_mocktests': total_mocktests,
            'total_questions_attempted': total_questions
        }

        return response_data, None, None

    except Exception as e:
        logger.error("Failed to fetch user analytics", exc_info=True)
        return None, {'error': f'Failed to fetch analytics: {str(e)}'}, 500