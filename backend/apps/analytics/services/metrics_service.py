from django.db.models import Sum, Avg
from django.utils import timezone

from ..models import PerformanceMetrics, DailyProgress, PerformanceSnapshot


class MetricsService:
    @staticmethod
    def update_performance_metrics(user, subject, test_attempt):
        metrics = MetricsService._get_or_create_metrics(user, subject)
        MetricsService._update_basic_metrics(metrics, test_attempt)
        MetricsService._update_accuracy(metrics)
        MetricsService._update_average_score(metrics, user, test_attempt)
        MetricsService._update_time_metrics(metrics, test_attempt)
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
        topic_stats = MetricsService._collect_topic_stats(test_attempt)
        MetricsService._update_weak_areas_from_stats(user, topic_stats)

    @staticmethod
    def _collect_topic_stats(test_attempt):
        from apps.mocktest.models import Answer
        from ..models import WeakArea

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
        from ..models import WeakArea

        for stats in topic_stats.values():
            weak_area, created = WeakArea.objects.get_or_create(
                user=user,
                subject=stats["subject"],
                topic=stats["topic"],
                defaults={"attempts": 0, "correct": 0},
            )
            MetricsService._update_weak_area(weak_area, stats, created)

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
        weak_area.priority = MetricsService._calculate_priority(weak_area.accuracy)
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

        from .user_analytics_service import UserAnalyticsService
        progress.streak_days = UserAnalyticsService._calculate_study_streak(user)
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

        metrics, _ = PerformanceMetrics.objects.get_or_create(user=user, subject=subject)
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
        MetricsService.rebuild_performance_metrics(user, subject)
        return snapshot