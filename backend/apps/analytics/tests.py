from django.test import TestCase
from django.utils import timezone
from apps.analytics.models import TopicPerformance, StudyContentCache
from apps.analytics.services.study_content_service import StudyContentService
from apps.roadmap.models import Topic, Exam, Subject
from apps.users.models import User


class TopicPerformanceModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='pass'
        )
        self.exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=timezone.now().date()
        )
        self.subject = Subject.objects.create(
            exam=self.exam,
            name="Data Structures"
        )
        self.topic = Topic.objects.create(
            name="Arrays",
            subject=self.subject
        )

    def test_create_topic_performance(self):
        performance = TopicPerformance.objects.create(
            user=self.user,
            topic=self.topic,
            accuracy=85.5,
            avg_time=120.0,
            total_attempts=10,
            strength="strong"
        )
        self.assertEqual(performance.user, self.user)
        self.assertEqual(performance.topic, self.topic)
        self.assertEqual(performance.accuracy, 85.5)
        self.assertEqual(performance.strength, "strong")

    def test_unique_topic_performance_per_user(self):
        # Create first performance record
        TopicPerformance.objects.create(
            user=self.user,
            topic=self.topic,
            accuracy=80.0,
            avg_time=100.0,
            total_attempts=5,
            strength="moderate"
        )
        # Try to create another for same user-topic - should fail
        with self.assertRaises(Exception):
            TopicPerformance.objects.create(
                user=self.user,
                topic=self.topic,
                accuracy=90.0,
                avg_time=110.0,
                total_attempts=8,
                strength="strong"
            )

    def test_topic_performance_update(self):
        performance = TopicPerformance.objects.create(
            user=self.user,
            topic=self.topic,
            accuracy=70.0,
            avg_time=150.0,
            total_attempts=3,
            strength="weak"
        )
        performance.accuracy = 85.0
        performance.strength = "moderate"
        performance.save()
        updated = TopicPerformance.objects.get(id=performance.id)
        self.assertEqual(updated.accuracy, 85.0)
        self.assertEqual(updated.strength, "moderate")


class StudyContentCacheModelTest(TestCase):

    def setUp(self):
        self.exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=timezone.now().date()
        )
        self.subject = Subject.objects.create(
            exam=self.exam,
            name="Data Structures"
        )
        self.topic = Topic.objects.create(
            name="Graphs",
            subject=self.subject
        )

    def test_create_study_content_cache(self):
        cache = StudyContentCache.objects.create(
            topic=self.topic,
            description="Graph algorithms are fundamental...",
            youtube_links=["https://youtube.com/watch?v=1", "https://youtube.com/watch?v=2"]
        )
        self.assertEqual(cache.topic, self.topic)
        self.assertIn("Graph algorithms", cache.description)
        self.assertEqual(len(cache.youtube_links), 2)


class StudyContentServiceTest(TestCase):

    def setUp(self):
        self.exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=timezone.now().date()
        )
        self.subject = Subject.objects.create(
            exam=self.exam,
            name="Data Structures"
        )
        self.topic = Topic.objects.create(
            name="Binary Search",
            subject=self.subject
        )

    def test_generate_queries_safe(self):
        queries = StudyContentService.generate_queries(self.topic.name)
        self.assertEqual(len(queries), 3)
        self.assertIsInstance(queries, list)

    def test_get_study_content(self):
        result = StudyContentService.get_study_content(self.topic.id)
        self.assertIsNotNone(result)
        self.assertEqual(result["topic_name"], "Binary Search")
        self.assertIn("description", result)
        self.assertIn("youtube_links", result)

    def test_invalid_topic(self):
        result = StudyContentService.get_study_content(999)
        self.assertIsNone(result)