from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from apps.users.models import User
from apps.roadmap.models import Exam, Subject, Topic, Subtopic, Roadmap, RoadmapTopic, RoadmapGenerationJob, PYQ, UserPYQAttempt
from apps.roadmap.serializers import ExamSerializer, RoadmapSerializer, DeterministicRoadmapGenerateSerializer


class TestExamModel(TestCase):

    def test_create_exam(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        self.assertEqual(exam.name, "GATE CS")
        self.assertEqual(exam.total_marks, 100)

    def test_exam_string_representation(self):
        exam = Exam.objects.create(
            name="GATE ME",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        self.assertEqual(str(exam), "GATE ME")

    def test_exam_unique_name(self):
        Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        with self.assertRaises(Exception):
            Exam.objects.create(
                name="GATE CS",
                category="Engineering",
                total_marks=100,
                exam_date=date.today() + timedelta(days=180)
            )

    def test_exam_ordering(self):
        Exam.objects.create(name="GATE ME", category="Eng", total_marks=100, exam_date=date.today())
        Exam.objects.create(name="GATE CS", category="Eng", total_marks=100, exam_date=date.today())
        exams = Exam.objects.all()
        self.assertEqual(exams[0].name, "GATE CS")
        self.assertEqual(exams[1].name, "GATE ME")


class TestSubjectModel(TestCase):

    def test_create_subject(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        subject = Subject.objects.create(
            exam=exam,
            name="Data Structures",
            order=1
        )
        self.assertEqual(subject.name, "Data Structures")
        self.assertEqual(subject.exam, exam)

    def test_subject_string_representation(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        subject = Subject.objects.create(
            exam=exam,
            name="Algorithms"
        )
        self.assertEqual(str(subject), "GATE CS - Algorithms")

    def test_subject_unique_together(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        Subject.objects.create(exam=exam, name="DS", order=1)
        with self.assertRaises(Exception):
            Subject.objects.create(exam=exam, name="DS", order=2)

    def test_subject_cascade_delete(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        subject = Subject.objects.create(exam=exam, name="DS")
        exam.delete()
        self.assertEqual(Subject.objects.filter(id=subject.id).count(), 0)


class TestTopicModel(TestCase):

    def test_create_topic(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(
            name="Graphs",
            subject=subject,
            weightage=5.0,
            pyq_count=10,
            is_core=True
        )
        self.assertEqual(topic.name, "Graphs")
        self.assertEqual(topic.subject, subject)
        self.assertEqual(topic.weightage, 5.0)
        self.assertEqual(topic.pyq_count, 10)
        self.assertTrue(topic.is_core)

    def test_topic_string_representation(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        self.assertEqual(str(topic), "GATE CS - Arrays")

    def test_topic_without_subject(self):
        topic = Topic.objects.create(name="General Topic")
        self.assertEqual(str(topic), "General Topic")

    def test_topic_hierarchy(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        parent_topic = Topic.objects.create(
            name="Data Structures",
            subject=subject
        )
        child_topic = Topic.objects.create(
            name="Trees",
            subject=subject,
            parent=parent_topic
        )
        self.assertEqual(child_topic.parent, parent_topic)
        self.assertIn(child_topic, parent_topic.child_topics.all())

    def test_topic_default_values(self):
        topic = Topic.objects.create(name="Default Topic")
        self.assertEqual(topic.weightage, 1.0)
        self.assertEqual(topic.pyq_total_marks, 0.0)
        self.assertEqual(topic.pyq_count, 0)
        self.assertTrue(topic.is_core)
        self.assertEqual(topic.order, 0)


class TestSubtopicModel(TestCase):

    def test_create_subtopic(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Graphs", subject=subject)
        subtopic = Subtopic.objects.create(
            topic=topic,
            name="DFS",
            order=1
        )
        self.assertEqual(subtopic.name, "DFS")
        self.assertEqual(subtopic.topic, topic)

    def test_subtopic_string_representation(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Graphs", subject=subject)
        subtopic = Subtopic.objects.create(
            topic=topic,
            name="BFS"
        )
        self.assertEqual(str(subtopic), "Graphs - BFS")

    def test_subtopic_unique_together(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Graphs", subject=subject)
        Subtopic.objects.create(topic=topic, name="DFS")
        with self.assertRaises(Exception):
            Subtopic.objects.create(topic=topic, name="DFS")


class TestRoadmapModel(TestCase):

    def test_create_roadmap(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        roadmap = Roadmap.objects.create(
            user=user,
            exam=exam,
            target_date=date.today() + timedelta(days=90),
            total_weeks=12,
            description="Study plan for GATE"
        )
        self.assertEqual(roadmap.user, user)
        self.assertEqual(roadmap.exam, exam)
        self.assertEqual(roadmap.total_weeks, 12)

    def test_roadmap_string_representation(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        roadmap = Roadmap.objects.create(
            user=user,
            exam=exam,
            target_date=date.today() + timedelta(days=90)
        )
        self.assertEqual(str(roadmap), "GATE CS - test@example.com")

    def test_roadmap_without_exam(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        roadmap = Roadmap.objects.create(
            user=user,
            target_date=date.today() + timedelta(days=90)
        )
        self.assertEqual(str(roadmap), "No Exam - test@example.com")

    def test_unique_active_roadmap_per_user(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        Roadmap.objects.create(
            user=user,
            exam=exam,
            target_date=date.today() + timedelta(days=90),
            is_active=True
        )
        with self.assertRaises(Exception):
            Roadmap.objects.create(
                user=user,
                exam=exam,
                target_date=date.today() + timedelta(days=90),
                is_active=True
            )

    def test_roadmap_default_values(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        roadmap = Roadmap.objects.create(
            user=user,
            target_date=date.today() + timedelta(days=90)
        )
        self.assertEqual(roadmap.total_weeks, 1)
        self.assertEqual(roadmap.version, 1)
        self.assertFalse(roadmap.is_active)
        self.assertEqual(roadmap.description, "")


class TestRoadmapTopicModel(TestCase):

    def test_create_roadmap_topic(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        roadmap = Roadmap.objects.create(
            user=user,
            exam=exam,
            target_date=date.today() + timedelta(days=90)
        )
        roadmap_topic = RoadmapTopic.objects.create(
            roadmap=roadmap,
            topic=topic,
            week_number=1,
            day_number=1,
            estimated_hours=2,
            priority=1,
            phase="coverage"
        )
        self.assertEqual(roadmap_topic.roadmap, roadmap)
        self.assertEqual(roadmap_topic.topic, topic)
        self.assertEqual(roadmap_topic.week_number, 1)
        self.assertEqual(roadmap_topic.day_number, 1)
        self.assertEqual(roadmap_topic.phase, "coverage")

    def test_roadmap_topic_string_representation(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        roadmap = Roadmap.objects.create(
            user=user,
            exam=exam,
            target_date=date.today() + timedelta(days=90)
        )
        roadmap_topic = RoadmapTopic.objects.create(
            roadmap=roadmap,
            topic=topic,
            week_number=1,
            day_number=1,
            phase="coverage"
        )
        self.assertEqual(str(roadmap_topic), "Week 1: Arrays")


class TestRoadmapGenerationJobModel(TestCase):

    def test_create_job(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        job = RoadmapGenerationJob.objects.create(
            user=user,
            status="pending"
        )
        self.assertEqual(job.user, user)
        self.assertEqual(job.status, "pending")
        self.assertEqual(job.error_message, "")
        self.assertEqual(job.input_payload, {})

    def test_job_string_representation(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        job = RoadmapGenerationJob.objects.create(
            user=user,
            status="processing"
        )
        self.assertEqual(str(job), f"Job {job.id} - processing")


class TestPYQModel(TestCase):

    def test_create_pyq(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        pyq = PYQ.objects.create(
            exam=exam,
            topic=topic,
            year=2023,
            marks=2.0,
            question_type="mcq",
            question_text="What is an array?",
            options={"A": "DS", "B": "Func"},
            correct_answer="A",
            explanation="Arrays are DS",
            source_url="https://example.com/pyq"
        )
        self.assertEqual(pyq.exam, exam)
        self.assertEqual(pyq.topic, topic)
        self.assertEqual(pyq.year, 2023)
        self.assertEqual(pyq.marks, 2.0)
        self.assertEqual(pyq.question_type, "mcq")


class TestUserPYQAttemptModel(TestCase):

    def test_create_pyq_attempt(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        pyq = PYQ.objects.create(
            exam=exam,
            topic=topic,
            year=2023,
            marks=2.0,
            question_type="mcq",
            question_text="What is an array?",
            correct_answer="A",
            source_url="https://example.com/pyq"
        )
        attempt = UserPYQAttempt.objects.create(
            user=user,
            pyq=pyq,
            answer={"selected": "A"},
            is_correct=True,
            time_taken=30
        )
        self.assertEqual(attempt.user, user)
        self.assertEqual(attempt.pyq, pyq)
        self.assertTrue(attempt.is_correct)
        self.assertEqual(attempt.time_taken, 30)


class TestExamSerializer(TestCase):

    def test_serialize_exam(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        serializer = ExamSerializer(exam)
        self.assertEqual(serializer.data['name'], "GATE CS")
        self.assertEqual(serializer.data['category'], "Engineering")
        self.assertEqual(serializer.data['total_marks'], 100)


class TestRoadmapSerializer(TestCase):

    def test_serialize_roadmap(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        roadmap = Roadmap.objects.create(
            user=user,
            exam=exam,
            target_date=date.today() + timedelta(days=90),
            total_weeks=12
        )
        serializer = RoadmapSerializer(roadmap)
        self.assertEqual(serializer.data['total_weeks'], 12)
        self.assertIn('exam', serializer.data)
        self.assertEqual(serializer.data['exam']['name'], "GATE CS")


class TestDeterministicRoadmapGenerateSerializer(TestCase):

    def test_valid_data(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        serializer = DeterministicRoadmapGenerateSerializer(data={
            'exam_id': exam.id,
            'target_date': (date.today() + timedelta(days=90)).isoformat(),
            'study_hours_per_day': 6
        })
        self.assertTrue(serializer.is_valid())

    def test_invalid_target_date_past(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        serializer = DeterministicRoadmapGenerateSerializer(data={
            'exam_id': exam.id,
            'target_date': (date.today() - timedelta(days=1)).isoformat(),
            'study_hours_per_day': 6
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('target_date', serializer.errors)

    def test_study_hours_out_of_range(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        serializer = DeterministicRoadmapGenerateSerializer(data={
            'exam_id': exam.id,
            'target_date': (date.today() + timedelta(days=90)).isoformat(),
            'study_hours_per_day': 25
        })
        self.assertFalse(serializer.is_valid())

    def test_target_date_exceeds_exam_date(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=60)
        )
        serializer = DeterministicRoadmapGenerateSerializer(data={
            'exam_id': exam.id,
            'target_date': (date.today() + timedelta(days=90)).isoformat(),
            'study_hours_per_day': 6
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('target_date', serializer.errors)


class TestExamListView(TestCase):

    def test_list_exams(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        Exam.objects.create(
            name="GATE ME",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get('/api/exams/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_list_exams_unauthenticated(self):
        client = APIClient()
        response = client.get('/api/exams/')
        self.assertEqual(response.status_code, 401)


class TestRoadmapListView(TestCase):

    def test_list_user_roadmaps(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        Roadmap.objects.create(
            user=user,
            exam=exam,
            target_date=date.today() + timedelta(days=90)
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get('/api/roadmaps/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_list_roadmaps_only_returns_user_roadmaps(self):
        user1 = User.objects.create_user(email='user1@example.com', password='pass')
        user2 = User.objects.create_user(email='user2@example.com', password='pass')
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        Roadmap.objects.create(user=user1, exam=exam, target_date=date.today() + timedelta(days=90))
        Roadmap.objects.create(user=user2, exam=exam, target_date=date.today() + timedelta(days=90))
        client = APIClient()
        client.force_authenticate(user=user1)
        response = client.get('/api/roadmaps/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)


class TestRoadmapDetailView(TestCase):

    def test_get_roadmap_detail(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        roadmap = Roadmap.objects.create(
            user=user,
            exam=exam,
            target_date=date.today() + timedelta(days=90),
            total_weeks=12
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get(f'/api/roadmap/{roadmap.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total_weeks'], 12)

    def test_get_roadmap_detail_unauthorized(self):
        user1 = User.objects.create_user(email='user1@example.com', password='pass')
        user2 = User.objects.create_user(email='user2@example.com', password='pass')
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        roadmap = Roadmap.objects.create(
            user=user1,
            exam=exam,
            target_date=date.today() + timedelta(days=90)
        )
        client = APIClient()
        client.force_authenticate(user=user2)
        response = client.get(f'/api/roadmap/{roadmap.id}/')
        self.assertEqual(response.status_code, 404)

    def test_delete_roadmap(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        roadmap = Roadmap.objects.create(
            user=user,
            exam=exam,
            target_date=date.today() + timedelta(days=90)
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.delete(f'/api/roadmap/{roadmap.id}/')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Roadmap.objects.filter(id=roadmap.id).count(), 0)

    def test_patch_roadmap(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        roadmap = Roadmap.objects.create(
            user=user,
            exam=exam,
            target_date=date.today() + timedelta(days=90),
            description="Old desc"
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.patch(
            f'/api/roadmap/{roadmap.id}/',
            {'description': 'New desc'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['description'], 'New desc')


class TestRoadmapJobStatusView(TestCase):

    def test_get_job_status(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        job = RoadmapGenerationJob.objects.create(
            user=user,
            status="pending"
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get(f'/api/roadmap/job/{job.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], "pending")
        self.assertEqual(response.data['job_id'], job.id)

    def test_get_job_status_unauthorized(self):
        user1 = User.objects.create_user(email='user1@example.com', password='pass')
        user2 = User.objects.create_user(email='user2@example.com', password='pass')
        job = RoadmapGenerationJob.objects.create(
            user=user1,
            status="pending"
        )
        client = APIClient()
        client.force_authenticate(user=user2)
        response = client.get(f'/api/roadmap/job/{job.id}/')
        self.assertEqual(response.status_code, 404)


class TestWeekPlanView(TestCase):

    def test_get_week_plan(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        roadmap = Roadmap.objects.create(
            user=user,
            exam=exam,
            target_date=date.today() + timedelta(days=90)
        )
        RoadmapTopic.objects.create(
            roadmap=roadmap,
            topic=topic,
            week_number=1,
            day_number=1,
            estimated_hours=2,
            phase="coverage"
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get(f'/api/roadmap/{roadmap.id}/week/1/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('data', response.data)
        self.assertIn('today_revision', response.data)


class TestTopicCompleteView(TestCase):

    def test_toggle_topic_completion(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        roadmap = Roadmap.objects.create(
            user=user,
            exam=exam,
            target_date=date.today() + timedelta(days=90)
        )
        roadmap_topic = RoadmapTopic.objects.create(
            roadmap=roadmap,
            topic=topic,
            week_number=1,
            day_number=1,
            phase="coverage"
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.patch(f'/api/roadmap/topic/{roadmap_topic.id}/complete/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['completed'])


class TestWeekProgressView(TestCase):

    def test_get_week_progress(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        roadmap = Roadmap.objects.create(
            user=user,
            exam=exam,
            target_date=date.today() + timedelta(days=90)
        )
        RoadmapTopic.objects.create(
            roadmap=roadmap,
            topic=topic,
            week_number=1,
            day_number=1,
            phase="coverage"
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get(f'/api/roadmap/{roadmap.id}/week/1/progress/')
        self.assertEqual(response.status_code, 200)


class TestRoadmapProgressView(TestCase):

    def test_get_overall_progress(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        roadmap = Roadmap.objects.create(
            user=user,
            exam=exam,
            target_date=date.today() + timedelta(days=90)
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get(f'/api/roadmap/{roadmap.id}/progress/')
        self.assertEqual(response.status_code, 200)


class TestActivateRoadmapView(TestCase):

    def test_activate_roadmap(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180)
        )
        roadmap = Roadmap.objects.create(
            user=user,
            exam=exam,
            target_date=date.today() + timedelta(days=90),
            is_active=False
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post(f'/api/roadmap/activate/{roadmap.id}/')
        self.assertEqual(response.status_code, 200)
        roadmap.refresh_from_db()
        self.assertTrue(roadmap.is_active)

    def test_activate_nonexistent_roadmap(self):
        user = User.objects.create_user(email='test@example.com', password='pass')
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post('/api/roadmap/activate/9999/')
        self.assertEqual(response.status_code, 404)
