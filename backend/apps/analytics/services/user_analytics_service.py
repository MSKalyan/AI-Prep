from datetime import timedelta
from django.db.models import Sum, Avg
from django.utils import timezone

from ..models import (
    StudySession,
    PerformanceMetrics,
    TopicPerformance,
    WeakArea,
    DailyProgress,
    PerformanceSnapshot,
)
from apps.mocktest.models import MockTest, TestAttempt
from apps.ai_service.models import Message
from apps.roadmap.models import RoadmapTopic


class UserAnalyticsService:
    @staticmethod
    def get_user_analytics(user):
        return {
            "overall_stats": UserAnalyticsService._calculate_overall_stats(user),
            "subject_performance": UserAnalyticsService._get_subject_performance(user),
            "weak_areas": UserAnalyticsService._get_weak_areas(user),
            "recent_progress": UserAnalyticsService._get_recent_progress(user),
            "study_streak": UserAnalyticsService._calculate_study_streak(user),
            "total_study_time": UserAnalyticsService._get_total_study_time(user),
            "total_mocktests": UserAnalyticsService._get_total_mocktests(user),
            "total_questions_attempted": UserAnalyticsService._get_total_questions(user),
        }

    @staticmethod
    def _get_subject_performance(user):
        return PerformanceMetrics.objects.filter(user=user)

    @staticmethod
    def _get_total_mocktests(user):
        return MockTest.objects.filter(user=user).count()

    @staticmethod
    def _get_total_questions(user):
        return TopicPerformance.objects.filter(user=user).aggregate(
            total=Sum("total_attempts")
        )["total"]

    @staticmethod
    def _get_weak_areas(user):
        return WeakArea.objects.filter(user=user)[:10]

    @staticmethod
    def _get_recent_progress(user):
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        return DailyProgress.objects.filter(
            user=user, date__gte=thirty_days_ago
        ).order_by("-date")

    @staticmethod
    def _get_total_study_time(user):
        return StudySession.objects.filter(user=user).aggregate(
            total=Sum("duration_minutes")
        )["total"] or 0

    @staticmethod
    def _calculate_overall_stats(user):
        test_attempts = UserAnalyticsService._get_test_attempts(user)
        stats = UserAnalyticsService._get_test_stats(test_attempts)
        ai_queries = UserAnalyticsService._get_ai_queries(user)
        completed_topics = UserAnalyticsService._get_completed_topics(user)
        return {**stats, "ai_queries": ai_queries, "completed_topics": completed_topics}

    @staticmethod
    def _get_test_attempts(user):
        return TestAttempt.objects.filter(user=user, submitted_at__isnull=False)

    @staticmethod
    def _get_test_stats(test_attempts):
        total_tests = test_attempts.count()
        avg_score = test_attempts.aggregate(Avg("percentage"))["percentage__avg"] or 0
        total_correct = test_attempts.aggregate(Sum("correct_answers"))["correct_answers__sum"] or 0
        total_incorrect = test_attempts.aggregate(Sum("incorrect_answers"))["incorrect_answers__sum"] or 0
        total_questions = total_correct + total_incorrect
        accuracy = (total_correct / total_questions * 100) if total_questions else 0

        return {
            "total_tests": total_tests,
            "average_score": round(avg_score, 2),
            "total_questions": total_questions,
            "correct_answers": total_correct,
            "incorrect_answers": total_incorrect,
            "accuracy": round(accuracy, 2),
        }

    @staticmethod
    def _get_ai_queries(user):
        return Message.objects.filter(conversation__user=user, role="user").count()

    @staticmethod
    def _get_completed_topics(user):
        return RoadmapTopic.objects.filter(roadmap__user=user, is_completed=True).count()

    @staticmethod
    def _calculate_study_streak(user):
        today = timezone.now().date()
        streak = 0
        current_date = today

        while True:
            has_activity = DailyProgress.objects.filter(
                user=user, date=current_date, study_time_minutes__gt=0
            ).exists()

            if has_activity:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
            if streak >= 365:
                break
        return streak

    @staticmethod
    def get_weak_subject(user):
        weak = PerformanceMetrics.objects.filter(user=user, total_attempts__gt=0).order_by("accuracy_percentage").first()
        if not weak:
            return None
        return {
            "subject": weak.subject,
            "accuracy": round(weak.accuracy_percentage, 2),
            "attempts": weak.total_attempts,
        }