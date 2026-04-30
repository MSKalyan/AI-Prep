from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta

from apps.roadmap.models import Roadmap, RoadmapTopic
from apps.mocktest.models import TestAttempt
from apps.analytics.models import DailyProgress
from .services import AnalyticsService


class DashboardService:
    @staticmethod
    def get_user_roadmaps(user):

        roadmaps = Roadmap.objects.filter(user=user).select_related("exam")

        return [
            {
                "id": r.id,
                "exam_name": r.exam.name if r.exam else "No Exam",
                "is_active": r.is_active,
            }
            for r in roadmaps
        ]

    @staticmethod
    def get_dashboard_summary(user):
        study_streak = DashboardService._calculate_streak(user)
        weak_subject = AnalyticsService.get_weak_subject(user)
        roadmaps = DashboardService.get_user_roadmaps(user)

        active_roadmap = Roadmap.objects.filter(user=user, is_active=True).first()
        test_stats = DashboardService._get_test_stats(user)

        if not active_roadmap:
            return DashboardService._build_no_roadmap_response(
                study_streak, roadmaps, test_stats
            )

        roadmap_stats = DashboardService._get_roadmap_stats(active_roadmap)

        return DashboardService._build_dashboard_response(
            study_streak,
            weak_subject,
            roadmaps,
            test_stats,
            roadmap_stats,
        )
    @staticmethod
    def _get_test_stats(user):
        tests = TestAttempt.objects.filter(user=user, submitted_at__isnull=False)

        return {
            "tests_taken": tests.count(),
            "average_score": tests.aggregate(Avg("percentage"))["percentage__avg"] or 0,
        }

    @staticmethod
    def _calculate_streak(user):

        progress_dates = set(
            DailyProgress.objects.filter(
                user=user, study_time_minutes__gt=0
            ).values_list("date", flat=True)
        )

        today = timezone.now().date()

        # allow streak even if today missed
        current_date = today if today in progress_dates else today - timedelta(days=1)

        streak = 0

        while current_date in progress_dates:
            streak += 1
            current_date -= timedelta(days=1)

        return streak
