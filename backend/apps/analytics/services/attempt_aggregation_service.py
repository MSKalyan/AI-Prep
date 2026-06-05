from datetime import datetime, timedelta
from django.db.models import Sum, Avg, Count, Q, Case, When, IntegerField
from django.utils import timezone
from ..models import (
    StudySession,
    PerformanceMetrics,
    TopicPerformance,
    WeakArea,
    DailyProgress,
    PerformanceSnapshot,
)
from apps.mocktest.models import Answer, MockTest, TestAttempt
from apps.ai_service.models import Message
from apps.roadmap.models import RoadmapTopic


class AttemptAggregationService:
    @staticmethod
    def get_topic_wise_aggregation(user):
        qs = Answer.objects.filter(attempt__user=user)

        if not qs.exists():
            return []

        aggregated = qs.values("question__topic_id").annotate(
            total_attempts=Count("id"),
            correct_answers=Sum(
                Case(
                    When(is_correct=True, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
            total_time=Sum("time_taken_seconds"),
        )

        return [
            {
                "topic_id": item["question__topic_id"],
                "total_attempts": item["total_attempts"] or 0,
                "correct_answers": item["correct_answers"] or 0,
                "total_time": item["total_time"] or 0,
            }
            for item in aggregated
        ]