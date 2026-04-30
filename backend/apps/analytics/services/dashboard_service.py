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

    @staticmethod
    def _get_roadmap_stats(active_roadmap):
        total_topics = RoadmapTopic.objects.filter(roadmap=active_roadmap).count()
        completed_topics = RoadmapTopic.objects.filter(
            roadmap=active_roadmap, is_completed=True
        ).count()
        pending_topics = max(total_topics - completed_topics, 0)
        progress_percentage = (
            round((completed_topics / total_topics) * 100, 2) if total_topics else 0
        )

        return {
            "roadmap_id": active_roadmap.id,
            "roadmap_exam": active_roadmap.exam.name if active_roadmap.exam else None,
            "target_date": active_roadmap.target_date,
            "total_topics": total_topics,
            "completed_topics": completed_topics,
            "pending_topics": pending_topics,
            "progress_percentage": progress_percentage,
        }

    @staticmethod
    def _build_no_roadmap_response(study_streak, roadmaps, test_stats):
        return {
            "study_streak": study_streak,
            "weak_subject": None,
            "roadmaps": roadmaps,
            "active_roadmap": None,
            "tests_taken": test_stats["tests_taken"],
            "average_score": test_stats["average_score"],
            "total_topics": 0,
            "completed_topics": 0,
            "pending_topics": 0,
            "progress_percentage": 0,
        }

    @staticmethod
    def _build_dashboard_response(
        study_streak, weak_subject, roadmaps, test_stats, roadmap_stats
    ):
        return {
            "study_streak": study_streak,
            "weak_subject": weak_subject,
            "roadmaps": roadmaps,
            "active_roadmap": roadmap_stats,
            "tests_taken": test_stats["tests_taken"],
            "average_score": test_stats["average_score"],
            "total_topics": roadmap_stats["total_topics"],
            "completed_topics": roadmap_stats["completed_topics"],
            "pending_topics": roadmap_stats["pending_topics"],
            "progress_percentage": roadmap_stats["progress_percentage"],
        }
