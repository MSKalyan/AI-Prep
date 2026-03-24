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

        active_roadmap = Roadmap.objects.filter(
            user=user,
            is_active=True
        ).first()

        # If no active roadmap
        if not active_roadmap:
            tests = TestAttempt.objects.filter(
                user=user,
                submitted_at__isnull=False
            )

            tests_taken = tests.count()

            avg_score = tests.aggregate(
                Avg("percentage")
            )["percentage__avg"] or 0

            return {
                "study_streak": study_streak,
                "topics_completed": 0,
                "roadmap_progress": 0,
                "tests_taken": tests_taken,
                "average_score": 0,
                "continue_studying": None,
                "weak_subject": None,
                "roadmaps": roadmaps
            }

        # ---------- Roadmap statistics ----------

        topics = RoadmapTopic.objects.filter(
            roadmap=active_roadmap
        )

        total_topics = topics.count()

        completed_topics = topics.filter(
            is_completed=True
        ).count()

        progress = 0
        if total_topics > 0:
            progress = (completed_topics / total_topics) * 100

        # ---------- Continue studying ----------

        next_topic = topics.filter(
            is_completed=False
        ).select_related("topic").order_by(
            "week_number",
            "day_number"
        ).first()

        continue_topic = None

        if next_topic:
            continue_topic = {
                "topic_id": next_topic.id,
                "topic_name": next_topic.topic.name
            }

        # ---------- Test statistics ----------

        tests = TestAttempt.objects.filter(
            user=user,
            submitted_at__isnull=False
        )

        tests_taken = tests.count()

        avg_score = tests.aggregate(
            Avg("percentage")
        )["percentage__avg"] or 0

        return {
            "study_streak": study_streak,
            "topics_completed": completed_topics,
            "roadmap_progress": round(progress, 2),
            "tests_taken": tests_taken,
            "average_score": round(avg_score, 2),
            "continue_studying": continue_topic,
            "weak_subject": weak_subject,
            "roadmaps": roadmaps
        }


    @staticmethod
    def _calculate_streak(user):

        progress_dates = set(
            DailyProgress.objects.filter(
                user=user,
                study_time_minutes__gt=0
            ).values_list("date", flat=True)
        )

        today = timezone.now().date()

        streak = 0
        current_date = today

        while current_date in progress_dates:
            streak += 1
            current_date -= timedelta(days=1)

        return streak
    

    