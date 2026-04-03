from django.test import TestCase
from datetime import date, timedelta
from django.utils import timezone
from rest_framework.test import APIClient

from apps.users.models import User
from apps.roadmap.models import Exam, Subject, Topic
from apps.mocktest.models import MockTest, TestAttempt
from apps.analytics.models import (
    TopicPerformance, StudyContentCache, StudySession,
    PerformanceMetrics, WeakArea, DailyProgress, PerformanceSnapshot
)
from apps.analytics.services.study_content_service import StudyContentService


class BaseTestCase(TestCase):
    def create_user(self):
        return User.objects.create_user(email='test@example.com', password='pass')

    def create_topic(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        return Topic.objects.create(name="Arrays", subject=subject)


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
            strength="strong"
        )

        self.assertEqual(performance.user, user)
        self.assertEqual(performance.topic, topic)

    def test_unique_constraint(self):
        user = self.create_user()
        topic = self.create_topic()

        TopicPerformance.objects.create(
            user=user,
            topic=topic,
            accuracy=0.0,
            avg_time=0.0,
            total_attempts=0
        )
        with self.assertRaises(Exception):
            TopicPerformance.objects.create(
                user=user,
                topic=topic,
                accuracy=0.0,
                avg_time=0.0,
                total_attempts=0
            )

# ---------------- Study Content Cache ----------------
class TestStudyContentCacheModel(BaseTestCase):

    def test_create(self):
        topic = self.create_topic()

        cache = StudyContentCache.objects.create(
            topic=topic,
            description="Graph content",
            youtube_links=["link1"]
        )

        self.assertEqual(cache.topic, topic)

    def test_unique(self):
        topic = self.create_topic()
        StudyContentCache.objects.create(
            topic=topic,
            description="test",
            youtube_links=[]
        )
        with self.assertRaises(Exception):
            StudyContentCache.objects.create(
                topic=topic,
                description="test",
                youtube_links=[]
            )

# ---------------- Study Session ----------------
class TestStudySessionModel(BaseTestCase):

    def test_create(self):
        user = self.create_user()

        session = StudySession.objects.create(
            user=user,
            activity_type='mock_test',
            duration_minutes=45
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
            user=user,
            subject="DSA",
            total_questions=100,
            correct_answers=80
        )

        self.assertEqual(metrics.calculated_accuracy, 80.0)

    def test_unique(self):
        user = self.create_user()
        PerformanceMetrics.objects.create(user=user, subject="DSA")

        with self.assertRaises(Exception):
            PerformanceMetrics.objects.create(user=user, subject="DSA")


# ---------------- Weak Area ----------------
class TestWeakAreaModel(BaseTestCase):

    def test_create(self):
        user = self.create_user()

        weak = WeakArea.objects.create(
            user=user,
            subject="DSA",
            topic="Graphs"
        )

        self.assertEqual(weak.topic, "Graphs")

    def test_unique(self):
        user = self.create_user()
        WeakArea.objects.create(user=user, subject="DSA", topic="Graphs")

        with self.assertRaises(Exception):
            WeakArea.objects.create(user=user, subject="DSA", topic="Graphs")


# ---------------- Daily Progress ----------------
class TestDailyProgressModel(BaseTestCase):

    def test_create(self):
        user = self.create_user()

        progress = DailyProgress.objects.create(
            user=user,
            date=date.today()
        )

        self.assertEqual(progress.study_time_minutes, 0)

    def test_unique(self):
        user = self.create_user()
        DailyProgress.objects.create(user=user, date=date.today())

        with self.assertRaises(Exception):
            DailyProgress.objects.create(user=user, date=date.today())


# ---------------- Performance Snapshot ----------------
class TestPerformanceSnapshotModel(BaseTestCase):

    def test_create(self):
        user = self.create_user()

        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )

        mock = MockTest.objects.create(user=user, title="Test", exam=exam)
        attempt = TestAttempt.objects.create(user=user, mock_test=mock)

        snapshot = PerformanceSnapshot.objects.create(
            user=user,
            subject="DSA",
            test_attempt=attempt,
            score=40,
            total_marks=50,
            accuracy=80.0
        )

        self.assertEqual(snapshot.user, user)


# ---------------- Study Content Service ----------------
class TestStudyContentService(TestCase):

    def test_generate_queries(self):
        queries = StudyContentService.generate_queries("Arrays")
        self.assertEqual(len(queries), 3)

    def test_invalid_topic(self):
        result = StudyContentService.get_study_content(999)
        self.assertIsNone(result)


# ---------------- API Views ----------------
class TestAnalyticsViews(BaseTestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = self.create_user()
        self.client.force_authenticate(user=self.user)

    def test_performance(self):
        response = self.client.get('/api/analytics/performance/')
        self.assertEqual(response.status_code, 200)

    def test_study_content_not_found(self):
        response = self.client.get('/api/analytics/study-content/999/')
        self.assertIn(response.status_code, [404, 200])

    def test_user_analytics(self):
        response = self.client.get('/api/analytics/')
        self.assertEqual(response.status_code, 200)

    def test_stats(self):
        response = self.client.get('/api/analytics/stats/')
        self.assertEqual(response.status_code, 200)

    def test_adaptive_endpoints(self):
        endpoints = [
            '/api/analytics/adaptive-roadmap/',
            '/api/analytics/adaptive-study-plan/',
            '/api/analytics/adaptive-revision/',
            '/api/analytics/aggregation/'
        ]

        for url in endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)