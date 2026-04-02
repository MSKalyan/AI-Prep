from django.test import TestCase
from django.utils import timezone
from apps.roadmap.models import Exam, Subject, Topic, Subtopic, Roadmap
from apps.users.models import User


class ExamModelTest(TestCase):

    def test_create_exam(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=timezone.now().date()
        )
        self.assertEqual(exam.name, "GATE CS")
        self.assertEqual(exam.total_marks, 100)

    def test_exam_string_representation(self):
        exam = Exam.objects.create(
            name="GATE ME",
            category="Engineering",
            total_marks=100,
            exam_date=timezone.now().date()
        )
        self.assertEqual(str(exam), "GATE ME")


class SubjectModelTest(TestCase):

    def setUp(self):
        self.exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=timezone.now().date()
        )

    def test_create_subject(self):
        subject = Subject.objects.create(
            exam=self.exam,
            name="Data Structures",
            order=1
        )
        self.assertEqual(subject.name, "Data Structures")
        self.assertEqual(subject.exam, self.exam)

    def test_subject_string_representation(self):
        subject = Subject.objects.create(
            exam=self.exam,
            name="Algorithms"
        )
        self.assertEqual(str(subject), "GATE CS - Algorithms")


class TopicModelTest(TestCase):

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

    def test_create_topic(self):
        topic = Topic.objects.create(
            name="Graphs",
            subject=self.subject,
            weightage=5.0,
            pyq_count=10,
            is_core=True
        )
        self.assertEqual(topic.name, "Graphs")
        self.assertEqual(topic.subject, self.subject)

    def test_topic_string_representation(self):
        topic = Topic.objects.create(name="Arrays", subject=self.subject)
        self.assertEqual(str(topic), "GATE CS - Arrays")

    def test_topic_without_subject(self):
        topic = Topic.objects.create(name="General Topic")
        self.assertEqual(str(topic), "General Topic")

    def test_topic_hierarchy(self):
        parent_topic = Topic.objects.create(
            name="Data Structures",
            subject=self.subject
        )
        child_topic = Topic.objects.create(
            name="Trees",
            subject=self.subject,
            parent=parent_topic
        )
        self.assertEqual(child_topic.parent, parent_topic)
        self.assertIn(child_topic, parent_topic.child_topics.all())


class SubtopicModelTest(TestCase):

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

    def test_create_subtopic(self):
        subtopic = Subtopic.objects.create(
            topic=self.topic,
            name="DFS",
            order=1
        )
        self.assertEqual(subtopic.name, "DFS")
        self.assertEqual(subtopic.topic, self.topic)

    def test_subtopic_string_representation(self):
        subtopic = Subtopic.objects.create(
            topic=self.topic,
            name="BFS"
        )
        self.assertEqual(str(subtopic), "Graphs - BFS")


class RoadmapModelTest(TestCase):

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

    def test_create_roadmap(self):
        roadmap = Roadmap.objects.create(
            user=self.user,
            exam=self.exam,
            target_date=timezone.now().date(),
            total_weeks=12,
            description="Study plan for GATE"
        )
        self.assertEqual(roadmap.user, self.user)
        self.assertEqual(roadmap.exam, self.exam)
        self.assertEqual(roadmap.total_weeks, 12)

    def test_roadmap_string_representation(self):
        roadmap = Roadmap.objects.create(
            user=self.user,
            exam=self.exam,
            target_date=timezone.now().date()
        )
        self.assertEqual(str(roadmap), "GATE CS - test@example.com")

    def test_roadmap_without_exam(self):
        roadmap = Roadmap.objects.create(
            user=self.user,
            target_date=timezone.now().date()
        )
        self.assertEqual(str(roadmap), "No Exam - test@example.com")

    def test_unique_active_roadmap_per_user(self):
        # Create first active roadmap
        Roadmap.objects.create(
            user=self.user,
            exam=self.exam,
            target_date=timezone.now().date(),
            is_active=True
        )
        # Try to create another active roadmap - should fail
        with self.assertRaises(Exception):
            Roadmap.objects.create(
                user=self.user,
                exam=self.exam,
                target_date=timezone.now().date(),
                is_active=True
            )