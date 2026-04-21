from django.test import TestCase
from datetime import date, timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from django.db import IntegrityError, transaction
import os

from apps.users.models import User
from apps.roadmap.models import Exam, Subject, Topic
from apps.mocktest.models import MockTest, TestAttempt, Question, Answer
from apps.analytics.models import (
    TopicPerformance,
    StudyContentCache,
    StudySession,
    PerformanceMetrics,
    WeakArea,
    DailyProgress,
    PerformanceSnapshot,
)
from apps.analytics.services.study_content_service import StudyContentService
from apps.analytics.services.services import AttemptAggregationService
from apps.analytics.services.performance_service import PerformanceService
from apps.analytics.services.adaptive_service import AdaptiveRoadmapService


class BaseTestCase(TestCase):
    def create_user(self):
        test_password = os.environ.get("TEST_PASSWORD", "testpass123!")  # noqa: S2068
        return User.objects.create_user(
            email="test@example.com", password=test_password
        )

    def create_topic(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        return Topic.objects.create(name="Arrays", subject=subject)

    def create_question(self, topic, exam):
        return Question.objects.create(
            topic=topic,
            exam=exam,
            question_text="What is an array?",
            question_type="mcq",
            options={"A": "Data structure", "B": "Function", "C": "Loop"},
            correct_answer="A",
            explanation="Arrays store elements",
            difficulty="easy",
            marks=1,
            source="llm",
        )


# ---------------- Topic Performance ----------------
class TestTopicPerformanceModel(BaseTestCase):
    def test_create(self):
        user = self.create_user()
        topic = self.create_topic()

        performance = TopicPerformance.objects.create(
            user=user,
            topic=topic,
            accuracy=85.5,
            avg_time=120.0,
            total_attempts=10,
            strength="strong",
        )

        self.assertEqual(performance.user, user)
        self.assertEqual(performance.topic, topic)

    def test_unique_constraint(self):
        user = self.create_user()
        topic = self.create_topic()

        TopicPerformance.objects.create(
            user=user, topic=topic, accuracy=0.0, avg_time=0.0, total_attempts=0
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                TopicPerformance.objects.create(
                    user=user, topic=topic, accuracy=0.0, avg_time=0.0, total_attempts=0
                )


# ---------------- Study Content Cache ----------------
class TestStudyContentCacheModel(BaseTestCase):
    def test_create(self):
        topic = self.create_topic()

        cache = StudyContentCache.objects.create(
            topic=topic, description="Graph content", youtube_links=["link1"]
        )

        self.assertEqual(cache.topic, topic)

    def test_unique(self):
        topic = self.create_topic()
        StudyContentCache.objects.create(
            topic=topic, description="test", youtube_links=[]
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                StudyContentCache.objects.create(
                    topic=topic, description="test", youtube_links=[]
                )


# ---------------- Study Session ----------------
class TestStudySessionModel(BaseTestCase):
    def test_create(self):
        user = self.create_user()

        session = StudySession.objects.create(
            user=user, activity_type="mock_test", duration_minutes=45
        )

        self.assertEqual(session.duration_minutes, 45)

    def test_duration_property(self):
        user = self.create_user()

        session = StudySession.objects.create(user=user)
        session.started_at = timezone.now() - timezone.timedelta(minutes=30)
        session.ended_at = timezone.now()
        session.save()

        self.assertTrue(abs(session.duration - 30) < 1)


# ---------------- Performance Metrics ----------------
class TestPerformanceMetricsModel(BaseTestCase):
    def test_create(self):
        user = self.create_user()

        metrics = PerformanceMetrics.objects.create(
            user=user, subject="DSA", total_questions=100, correct_answers=80
        )

        self.assertEqual(metrics.calculated_accuracy, 80.0)

    def test_unique(self):
        user = self.create_user()
        PerformanceMetrics.objects.create(user=user, subject="DSA")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PerformanceMetrics.objects.create(user=user, subject="DSA")


# ---------------- Weak Area ----------------
class TestWeakAreaModel(BaseTestCase):
    def test_create(self):
        user = self.create_user()

        weak = WeakArea.objects.create(user=user, subject="DSA", topic="Graphs")

        self.assertEqual(weak.topic, "Graphs")

    def test_unique(self):
        user = self.create_user()
        WeakArea.objects.create(user=user, subject="DSA", topic="Graphs")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WeakArea.objects.create(user=user, subject="DSA", topic="Graphs")


# ---------------- Daily Progress ----------------
class TestDailyProgressModel(BaseTestCase):
    def test_create(self):
        user = self.create_user()

        progress = DailyProgress.objects.create(user=user, date=date.today())

        self.assertEqual(progress.study_time_minutes, 0)

    def test_unique(self):
        user = self.create_user()
        DailyProgress.objects.create(user=user, date=date.today())

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                DailyProgress.objects.create(user=user, date=date.today())


# ---------------- Performance Snapshot ----------------
class TestPerformanceSnapshotModel(BaseTestCase):
    def test_create(self):
        user = self.create_user()

        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )

        mock = MockTest.objects.create(user=user, title="Test", exam=exam)
        attempt = TestAttempt.objects.create(user=user, mock_test=mock)

        snapshot = PerformanceSnapshot.objects.create(
            user=user,
            subject="DSA",
            test_attempt=attempt,
            score=40,
            total_marks=50,
            accuracy=80.0,
        )

        self.assertEqual(snapshot.user, user)


# ---------------- Study Content Service ----------------
class TestStudyContentService(TestCase):
    def test_generate_queries(self):
        queries = StudyContentService.generate_queries("Arrays")
        self.assertEqual(len(queries), 3)

    def test_is_good_video_filter(self):
        self.assertFalse(StudyContentService.is_good_video("Funny Meme Trailer"))
        self.assertTrue(
            StudyContentService.is_good_video("Arrays tutorial for beginners")
        )

    def test_get_study_content_missing_topic_returns_none(self):
        result = StudyContentService.get_study_content("does-not-exist")
        self.assertIsNone(result)

    def test_get_study_content_uses_cache(self):
        exam = Exam.objects.create(
            name="GATE EE",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        subject = Subject.objects.create(exam=exam, name="Basics")
        topic = Topic.objects.create(name="Graphs", subject=subject)

        StudyContentCache.objects.create(
            topic=topic,
            description="Cached description",
            youtube_links=["https://www.youtube.com/watch?v=abc123"],
        )

        data = StudyContentService.get_study_content("Graphs")
        self.assertEqual(data["topic_name"], "Graphs")
        self.assertEqual(data["description"], "Cached description")
        self.assertEqual(len(data["youtube_links"]), 1)


# ---------------- API Views ----------------
class TestAnalyticsViews(BaseTestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = self.create_user()
        self.client.force_authenticate(user=self.user)

    def test_performance(self):
        response = self.client.get("/api/analytics/performance/")
        self.assertEqual(response.status_code, 200)

    def test_study_content_not_found(self):
        response = self.client.get(
            "/api/analytics/study-content/", {"topic_name": "missing"}
        )
        self.assertEqual(response.status_code, 404)

    def test_study_content_requires_param(self):
        response = self.client.get("/api/analytics/study-content/")
        self.assertEqual(response.status_code, 400)

    def test_study_content_success(self):
        topic = self.create_topic()
        response = self.client.get(
            "/api/analytics/study-content/", {"topic_name": topic.name}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["data"]["topic_name"], topic.name)

    def test_user_analytics(self):
        response = self.client.get("/api/analytics/")
        self.assertEqual(response.status_code, 200)

    def test_stats(self):
        response = self.client.get("/api/analytics/stats/")
        self.assertEqual(response.status_code, 200)

    def test_adaptive_endpoints(self):
        endpoints = [
            "/api/analytics/adaptive-roadmap/",
            "/api/analytics/adaptive-study-plan/",
            "/api/analytics/adaptive-revision/",
            "/api/analytics/aggregation/",
        ]

        for url in endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)


# ---------------- Service Layer ----------------
class TestAnalyticsServices(BaseTestCase):
    def test_attempt_aggregation_empty(self):
        user = self.create_user()
        self.assertEqual(AttemptAggregationService.get_topic_wise_aggregation(user), [])

    def test_attempt_aggregation_with_answers(self):
        user = self.create_user()

        exam = Exam.objects.create(
            name="GATE ME",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        subject = Subject.objects.create(exam=exam, name="Math")
        topic = Topic.objects.create(name="Probability", subject=subject)
        question = self.create_question(topic, exam)

        mock_test = MockTest.objects.create(user=user, title="Agg Test", exam=exam)
        attempt = TestAttempt.objects.create(user=user, mock_test=mock_test)

        Answer.objects.create(
            attempt=attempt,
            question=question,
            is_correct=True,
            time_taken_seconds=12,
        )

        data = AttemptAggregationService.get_topic_wise_aggregation(user)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["topic_id"], topic.id)
        self.assertEqual(data[0]["total_attempts"], 1)
        self.assertEqual(data[0]["correct_answers"], 1)

    def test_performance_classify_topic(self):
        self.assertEqual(
            PerformanceService.classify_topic(accuracy=0.9, attempts=10), "strong"
        )
        self.assertEqual(
            PerformanceService.classify_topic(accuracy=0.6, attempts=10), "moderate"
        )
        self.assertEqual(
            PerformanceService.classify_topic(accuracy=0.2, attempts=10), "weak"
        )
        self.assertEqual(
            PerformanceService.classify_topic(accuracy=0.2, attempts=2), "insufficient"
        )

    def test_adaptive_priority_new_user(self):
        user = self.create_user()
        topic = self.create_topic()

        results = AdaptiveRoadmapService.generate_priority(user)
        self.assertTrue(any(r["topic_id"] == topic.id for r in results))


# ---------------- Dashboard Service Tests ----------------
class TestDashboardService(BaseTestCase):
    def test_get_user_roadmaps_empty(self):
        user = self.create_user()
        from apps.analytics.services.dashboard_service import DashboardService

        result = DashboardService.get_user_roadmaps(user)
        self.assertEqual(result, [])

    def test_dashboard_summary_no_roadmap(self):
        user = self.create_user()
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        mock_test = MockTest.objects.create(user=user, title="Test", exam=exam)
        attempt = TestAttempt.objects.create(
            user=user,
            mock_test=mock_test,
            score=40,
            percentage=80.0,
            submitted_at=timezone.now(),
        )
        from apps.analytics.services.dashboard_service import DashboardService

        result = DashboardService.get_dashboard_summary(user)
        self.assertEqual(result["tests_taken"], 1)
        self.assertEqual(result["average_score"], 80.0)

    def test_calculate_streak_no_progress(self):
        user = self.create_user()
        from apps.analytics.services.dashboard_service import DashboardService

        streak = DashboardService._calculate_streak(user)
        self.assertEqual(streak, 0)

    def test_calculate_streak_with_progress(self):
        user = self.create_user()
        yesterday = date.today() - timedelta(days=1)
        DailyProgress.objects.create(user=user, date=yesterday, study_time_minutes=30)
        from apps.analytics.services.dashboard_service import DashboardService

        streak = DashboardService._calculate_streak(user)
        self.assertGreaterEqual(streak, 1)


# ---------------- Analytics Service Tests ----------------
class TestAnalyticsService(BaseTestCase):
    def test_get_weak_subject_no_data(self):
        user = self.create_user()
        from apps.analytics.services.services import AnalyticsService

        result = AnalyticsService.get_weak_subject(user)
        self.assertIsNone(result)
