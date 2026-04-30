from datetime import datetime, timedelta
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from ..models import (
    StudySession,
    PerformanceMetrics,
    TopicPerformance,
    WeakArea,
    DailyProgress,
    PerformanceSnapshot,
)

from django.db.models import Count, Sum, Case, When, IntegerField
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


class AnalyticsService:
    """Service layer for analytics calculations"""

    @staticmethod
    def get_user_analytics(user):
        return {
            "overall_stats": AnalyticsService._calculate_overall_stats(user),
            "subject_performance": AnalyticsService._get_subject_performance(user),
            "weak_areas": AnalyticsService._get_weak_areas(user),
            "recent_progress": AnalyticsService._get_recent_progress(user),
            "study_streak": AnalyticsService._calculate_study_streak(user),
            "total_study_time": AnalyticsService._get_total_study_time(user),
            "total_mocktests": AnalyticsService._get_total_mocktests(user),
            "total_questions_attempted": AnalyticsService._get_total_questions(user),
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
        return (
            StudySession.objects.filter(user=user).aggregate(
                total=Sum("duration_minutes")
            )["total"]
            or 0
        )
    
    @staticmethod
    def _calculate_overall_stats(user):
        test_attempts = AnalyticsService._get_test_attempts(user)

        stats = AnalyticsService._get_test_stats(test_attempts)
        ai_queries = AnalyticsService._get_ai_queries(user)
        completed_topics = AnalyticsService._get_completed_topics(user)

        return {
            **stats,
            "ai_queries": ai_queries,
            "completed_topics": completed_topics,
        }
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
        return RoadmapTopic.objects.filter(
            roadmap__user=user, is_completed=True
        ).count()
    
    @staticmethod
    def _calculate_study_streak(user):
        """Calculate current study streak in days"""

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
    def update_performance_metrics(user, subject, test_attempt):
        metrics = AnalyticsService._get_or_create_metrics(user, subject)

        AnalyticsService._update_basic_metrics(metrics, test_attempt)
        AnalyticsService._update_accuracy(metrics)
        AnalyticsService._update_average_score(metrics, user, test_attempt)
        AnalyticsService._update_time_metrics(metrics, test_attempt)

        metrics.last_activity = timezone.now()
        metrics.save()

        return metrics
    @staticmethod
    def _get_or_create_metrics(user, subject):
        return PerformanceMetrics.objects.get_or_create(
            user=user,
            subject=subject,
            defaults={
                "total_attempts": 0,
                "total_questions": 0,
                "correct_answers": 0,
                "incorrect_answers": 0,
            },
        )[0]


    @staticmethod
    def _update_basic_metrics(metrics, test_attempt):
        metrics.total_attempts += 1
        metrics.total_questions += (
            test_attempt.correct_answers
            + test_attempt.incorrect_answers
            + test_attempt.unanswered
        )
        metrics.correct_answers += test_attempt.correct_answers
        metrics.incorrect_answers += test_attempt.incorrect_answers


    @staticmethod
    def _update_accuracy(metrics):
        total_answered = metrics.correct_answers + metrics.incorrect_answers
        metrics.accuracy_percentage = (
            (metrics.correct_answers / total_answered * 100)
            if total_answered else 0
        )


    @staticmethod
    def _update_average_score(metrics, user, test_attempt):
        from apps.mocktest.models import TestAttempt

        all_attempts = TestAttempt.objects.filter(
            user=user,
            mock_test__exam_type=test_attempt.mock_test.exam_type
        )

        metrics.average_score = all_attempts.aggregate(Avg("score"))["score__avg"] or 0


    @staticmethod
    def _update_time_metrics(metrics, test_attempt):
        metrics.total_time_minutes += test_attempt.time_taken_minutes

        metrics.average_time_per_question = (
            (metrics.total_time_minutes * 60) / metrics.total_questions
            if metrics.total_questions else 0
        )
    @staticmethod
    def update_weak_areas(user, test_attempt):
        """Identify and update weak areas based on test performance"""
        from apps.mocktest.models import Answer

        topic_stats = AnalyticsService._collect_topic_stats(test_attempt)
        AnalyticsService._update_weak_areas_from_stats(user, topic_stats)

    @staticmethod
    def _collect_topic_stats(test_attempt):
        from apps.mocktest.models import Answer

        topic_stats = {}
        for is_correct in [False, True]:
            answers = Answer.objects.filter(
                attempt=test_attempt, is_correct=is_correct
            ).select_related("question")
            for answer in answers:
                topic = answer.question.topic
                subject = answer.question.subject
                key = f"{subject}:{topic}"
                if key not in topic_stats:
                    topic_stats[key] = {
                        "subject": subject,
                        "topic": topic,
                        "attempts": 0,
                        "correct": 0,
                    }
                topic_stats[key]["attempts"] += 1
                if is_correct:
                    topic_stats[key]["correct"] += 1
        return topic_stats

    @staticmethod
    def _update_weak_areas_from_stats(user, topic_stats):
        for stats in topic_stats.values():
            weak_area, created = WeakArea.objects.get_or_create(
                user=user,
                subject=stats["subject"],
                topic=stats["topic"],
                defaults={"attempts": 0, "correct": 0},
            )
            AnalyticsService._update_weak_area(weak_area, stats, created)

    @staticmethod
    def _update_weak_area(weak_area, stats, created):
        old_accuracy = weak_area.accuracy
        weak_area.attempts += stats["attempts"]
        weak_area.correct += stats["correct"]
        weak_area.accuracy = (
            (weak_area.correct / weak_area.attempts * 100)
            if weak_area.attempts > 0
            else 0
        )
        if not created and weak_area.accuracy > old_accuracy:
            weak_area.is_improving = True
        weak_area.priority = AnalyticsService._calculate_priority(weak_area.accuracy)
        weak_area.save()

    @staticmethod
    def _calculate_priority(accuracy):
        if accuracy < 40:
            return 1
        elif accuracy < 70:
            return 2
        return 3

    @staticmethod
    def update_daily_progress(user, activity_data):
        """Update daily progress tracking"""
        today = timezone.now().date()
        progress, _ = DailyProgress.objects.get_or_create(
            user=user,
            date=today,
            defaults={
                "study_time_minutes": 0,
                "questions_attempted": 0,
                "questions_correct": 0,
                "mock_tests_taken": 0,
                "ai_queries": 0,
                "topics_covered": [],
            },
        )
        if "study_time" in activity_data:
            progress.study_time_minutes += activity_data["study_time"]
        if "questions_attempted" in activity_data:
            progress.questions_attempted += activity_data["questions_attempted"]
        if "questions_correct" in activity_data:
            progress.questions_correct += activity_data["questions_correct"]
        if "mock_test" in activity_data and activity_data["mock_test"]:
            progress.mock_tests_taken += 1
        if "ai_query" in activity_data and activity_data["ai_query"]:
            progress.ai_queries += 1
        if "topic" in activity_data and activity_data["topic"]:
            if activity_data["topic"] not in progress.topics_covered:
                progress.topics_covered.append(activity_data["topic"])
        progress.streak_days = AnalyticsService._calculate_study_streak(user)
        target_minutes = user.study_hours_per_day * 60
        progress.goals_met = progress.study_time_minutes >= target_minutes
        progress.save()
        return progress

    @staticmethod
    def rebuild_performance_metrics(user, subject):

        snapshots = PerformanceSnapshot.objects.filter(user=user, subject=subject)

        total_attempts = snapshots.count()

        aggregates = snapshots.aggregate(
            total_score=Sum("score"),
            avg_accuracy=Avg("accuracy"),
            total_marks=Sum("total_marks"),
        )

        total_score = aggregates["total_score"] or 0
        total_marks = aggregates["total_marks"] or 0
        avg_accuracy = aggregates["avg_accuracy"] or 0

        metrics, _ = PerformanceMetrics.objects.get_or_create(
            user=user, subject=subject
        )

        metrics.total_attempts = total_attempts
        metrics.total_questions = total_marks
        metrics.correct_answers = total_score
        metrics.accuracy_percentage = avg_accuracy

        metrics.save()

        return metrics

    @staticmethod
    def create_performance_snapshot(test_attempt):

        user = test_attempt.user
        subject = (
            test_attempt.mock_test.exam.name
            if test_attempt.mock_test.exam
            else "Unknown"
        )
        if test_attempt.total_marks == 0:
            accuracy = 0
        else:
            accuracy = (test_attempt.score / test_attempt.total_marks) * 100

        snapshot = PerformanceSnapshot.objects.get_or_create(
            test_attempt=test_attempt,
            defaults={
                "user": user,
                "subject": subject,
                "score": test_attempt.score,
                "total_marks": test_attempt.total_marks,
                "accuracy": accuracy,
            },
        )
        AnalyticsService.rebuild_performance_metrics(user, subject)
        return snapshot

    @staticmethod
    def get_weak_subject(user):
        weak = (
            PerformanceMetrics.objects.filter(user=user, total_attempts__gt=0)
            .order_by("accuracy_percentage")
            .first()
        )
        if not weak:
            return None
        return {
            "subject": weak.subject,
            "accuracy": round(weak.accuracy_percentage, 2),
            "attempts": weak.total_attempts,
        }
