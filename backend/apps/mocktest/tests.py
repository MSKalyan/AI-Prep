import os
from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from apps.users.models import User
from apps.roadmap.models import Exam, Subject, Topic, Roadmap, RoadmapTopic
from apps.mocktest.models import Question, MockTest, TestAttempt, Answer
from apps.mocktest.serializers import (
    QuestionSerializer,
    MockTestSerializer,
    SubmitAnswerSerializer,
)
from apps.mocktest.services import MockTestService

# Tests should be hermetic: don't require env vars to be set in CI.
TEST_PASSWORD = os.environ.get("TEST_PASSWORD", "testpass123!")  # noqa: S2068


class TestQuestionModel(TestCase):
    def test_create_question(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        question = Question.objects.create(
            topic=topic,
            exam=exam,
            question_text="What is an array?",
            question_type="mcq",
            options={"A": "Data structure", "B": "Function"},
            correct_answer="A",
            explanation="Arrays are fundamental data structures",
            difficulty="easy",
            marks=1,
            source="llm",
        )
        self.assertEqual(question.question_text, "What is an array?")
        self.assertEqual(question.correct_answer, "A")
        self.assertEqual(question.difficulty, "easy")
        self.assertEqual(question.marks, 1)
        self.assertEqual(question.source, "llm")

    def test_question_string_representation(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        question = Question.objects.create(
            topic=topic,
            exam=exam,
            question_text="Sample question",
            correct_answer="A",
        )

    def test_extract_correct_answer_string(self):
        self.assertEqual(
            MockTestService._extract_correct_answer("A", {"A": "one", "B": "two"}), "A"
        )
        self.assertEqual(
            MockTestService._extract_correct_answer("b", {"A": "one", "B": "two"}), "B"
        )
        self.assertEqual(MockTestService._extract_correct_answer("", {"A": "one"}), "")
        self.assertEqual(
            MockTestService._extract_correct_answer(["C", "D"], {"C": "three"}), "C"
        )
        self.assertEqual(
            MockTestService._extract_correct_answer(
                "Paris", {"A": "London", "B": "Paris", "C": "Rome"}
            ),
            "B",
        )

    def test_get_topic_stats_empty(self):
        stats = MockTestService.get_topic_stats([])
        self.assertIsNone(stats["topic_name"])
        self.assertEqual(stats["pyq_available"], 0)

    def test_question_string_representation_with_source(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        question = Question.objects.create(
            topic=topic,
            exam=exam,
            question_text="Sample",
            correct_answer="Answer",
            source="pyq",
            difficulty="medium",
        )
        self.assertEqual(str(question), "{} (pyq) - medium".format(topic))

    def test_question_default_values(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        question = Question.objects.create(
            topic=topic,
            exam=exam,
            question_text="Test",
            correct_answer="A",
            source="llm",
        )
        self.assertEqual(question.question_type, "mcq")
        self.assertEqual(question.difficulty, "medium")
        self.assertEqual(question.marks, 1)
        self.assertEqual(question.negative_marks, 0.0)
        self.assertEqual(question.tags, [])
        self.assertIsNone(question.options)
        self.assertEqual(question.explanation, "")


class TestMockTestModel(TestCase):
    def test_build_mock_test_title_with_subject_and_topic(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        title = MockTestService._build_mock_test_title(subject.name, topic)
        self.assertEqual(title, "Data Structures - Arrays")

    def test_build_mock_test_title_topic_only(self):
        topic = Topic.objects.create(name="Arrays")
        title = MockTestService._build_mock_test_title("", topic)
        self.assertEqual(title, "Arrays")

    def test_build_mock_test_title_default(self):
        title = MockTestService._build_mock_test_title("", None)
        self.assertEqual(title, "Mock Test")

    def test_create_mock_test(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        roadmap = Roadmap.objects.create(
            user=user, exam=exam, target_date=date.today() + timedelta(days=90)
        )
        mock_test = MockTest.objects.create(
            user=user,
            roadmap=roadmap,
            title="DSA Practice Test",
            description="Practice questions for data structures",
            exam=exam,
            total_marks=50,
            question_count=10,
            duration_minutes=60,
            status="active",
        )
        self.assertEqual(mock_test.title, "DSA Practice Test")
        self.assertEqual(mock_test.user, user)
        self.assertEqual(mock_test.status, "active")

    def test_mock_test_string_representation(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        mock_test = MockTest.objects.create(user=user, title="Test Title")
        self.assertEqual(str(mock_test), f"Test Title - {user}")

    def test_mock_test_default_values(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        mock_test = MockTest.objects.create(user=user, title="Default Test")
        self.assertEqual(mock_test.status, "draft")
        self.assertEqual(mock_test.total_marks, 0)
        self.assertEqual(mock_test.question_count, 0)
        self.assertEqual(mock_test.duration_minutes, 60)
        self.assertEqual(mock_test.generation_reason, "topic_practice")
        self.assertEqual(mock_test.generation_topics, [])


class TestTestAttemptModel(TestCase):
    def test_create_test_attempt(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
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
            score=40.0,
            total_marks=50,
            percentage=80.0,
            correct_answers=8,
            incorrect_answers=2,
            time_taken_minutes=45,
        )
        self.assertEqual(attempt.user, user)
        self.assertEqual(attempt.mock_test, mock_test)
        self.assertEqual(attempt.score, 40.0)
        self.assertEqual(attempt.percentage, 80.0)

    def test_test_attempt_string_representation(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        mock_test = MockTest.objects.create(user=user, title="Test", exam=exam)
        attempt = TestAttempt.objects.create(
            user=user, mock_test=mock_test, percentage=75.5
        )
        self.assertEqual(str(attempt), f"{mock_test.title} - {user} - 75.5%")

    def test_test_attempt_default_values(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        mock_test = MockTest.objects.create(user=user, title="Test", exam=exam)
        attempt = TestAttempt.objects.create(user=user, mock_test=mock_test)
        self.assertEqual(attempt.score, 0.0)
        self.assertEqual(attempt.total_marks, 0)
        self.assertEqual(attempt.percentage, 0.0)
        self.assertEqual(attempt.correct_answers, 0)
        self.assertEqual(attempt.incorrect_answers, 0)
        self.assertEqual(attempt.unanswered, 0)
        self.assertEqual(attempt.time_taken_minutes, 0)
        self.assertIsNone(attempt.submitted_at)


class TestAnswerModel(TestCase):
    def test_create_answer(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        question = Question.objects.create(
            topic=topic,
            exam=exam,
            question_text="What is an array?",
            correct_answer="A data structure",
            source="llm",
        )
        mock_test = MockTest.objects.create(user=user, title="Test", exam=exam)
        attempt = TestAttempt.objects.create(user=user, mock_test=mock_test)
        answer = Answer.objects.create(
            attempt=attempt,
            question=question,
            user_answer="A data structure",
            is_correct=True,
            marks_obtained=1.0,
            time_taken_seconds=30,
        )
        self.assertEqual(answer.attempt, attempt)
        self.assertEqual(answer.question, question)
        self.assertTrue(answer.is_correct)
        self.assertEqual(answer.marks_obtained, 1.0)

    def test_answer_string_representation(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        question = Question.objects.create(
            topic=topic,
            exam=exam,
            question_text="What is an array?",
            correct_answer="A",
            source="llm",
        )
        mock_test = MockTest.objects.create(user=user, title="Test", exam=exam)
        attempt = TestAttempt.objects.create(user=user, mock_test=mock_test)
        answer = Answer.objects.create(
            attempt=attempt, question=question, is_correct=False
        )
        self.assertEqual(str(answer), f"Q{question.id} - Incorrect")

    def test_answer_unique_together(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        question = Question.objects.create(
            topic=topic,
            exam=exam,
            question_text="What is an array?",
            correct_answer="A",
            source="llm",
        )
        mock_test = MockTest.objects.create(user=user, title="Test", exam=exam)
        attempt = TestAttempt.objects.create(user=user, mock_test=mock_test)
        Answer.objects.create(
            attempt=attempt, question=question, user_answer="Answer 1"
        )
        with self.assertRaises(Exception):
            Answer.objects.create(
                attempt=attempt, question=question, user_answer="Answer 2"
            )

    def test_answer_default_values(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        question = Question.objects.create(
            topic=topic,
            exam=exam,
            question_text="What is an array?",
            correct_answer="A",
            source="llm",
        )
        mock_test = MockTest.objects.create(user=user, title="Test", exam=exam)
        attempt = TestAttempt.objects.create(user=user, mock_test=mock_test)
        answer = Answer.objects.create(attempt=attempt, question=question)
        self.assertFalse(answer.is_correct)
        self.assertEqual(answer.marks_obtained, 0.0)
        self.assertEqual(answer.time_taken_seconds, 0)
        self.assertEqual(answer.user_answer, "")


class TestQuestionSerializer(TestCase):
    def test_serialize_question(self):
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        question = Question.objects.create(
            topic=topic,
            exam=exam,
            question_text="What is an array?",
            correct_answer="A",
            source="llm",
        )
        serializer = QuestionSerializer(question)
        self.assertEqual(serializer.data["question_text"], "What is an array?")
        self.assertEqual(serializer.data["topic"], "Arrays")
        self.assertNotIn("correct_answer", serializer.data)
        self.assertNotIn("explanation", serializer.data)


class TestMockTestSerializer(TestCase):
    def test_serialize_mock_test(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        mock_test = MockTest.objects.create(
            user=user, title="Test", exam=exam, total_marks=50, duration_minutes=60
        )
        serializer = MockTestSerializer(mock_test)
        self.assertEqual(serializer.data["title"], "Test")
        self.assertEqual(serializer.data["total_marks"], 50)
        self.assertEqual(serializer.data["duration_minutes"], 60)
        self.assertEqual(serializer.data["questions_count"], 0)


class TestSubmitAnswerSerializer(TestCase):
    def test_valid_submit(self):
        serializer = SubmitAnswerSerializer(
            data={
                "attempt_id": 1,
                "question_id": 1,
                "user_answer": "A",
                "time_taken_seconds": 30,
            }
        )
        self.assertTrue(serializer.is_valid())

    def test_missing_fields(self):
        serializer = SubmitAnswerSerializer(
            data={
                "attempt_id": 1,
            }
        )
        self.assertFalse(serializer.is_valid())


class TestQuestionListView(TestCase):
    def test_list_questions(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        Question.objects.create(
            topic=topic,
            exam=exam,
            question_text="Q1",
            correct_answer="A",
            source="llm",
            difficulty="easy",
        )
        Question.objects.create(
            topic=topic,
            exam=exam,
            question_text="Q2",
            correct_answer="B",
            source="llm",
            difficulty="hard",
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get("/api/questions/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_filter_by_difficulty(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        Question.objects.create(
            topic=topic,
            exam=exam,
            question_text="Easy Q",
            correct_answer="A",
            source="llm",
            difficulty="easy",
        )
        Question.objects.create(
            topic=topic,
            exam=exam,
            question_text="Hard Q",
            correct_answer="B",
            source="llm",
            difficulty="hard",
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get("/api/questions/?difficulty=easy")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["question_text"], "Easy Q")

    def test_list_questions_unauthenticated(self):
        client = APIClient()
        response = client.get("/api/questions/")
        self.assertEqual(response.status_code, 401)


class TestMockTestDetailView(TestCase):
    def test_get_mock_test_detail(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        question = Question.objects.create(
            topic=topic,
            exam=exam,
            question_text="What is an array?",
            options={"A": "Data structure", "B": "Function"},
            correct_answer="A",
            source="llm",
        )
        mock_test = MockTest.objects.create(
            user=user,
            title="Test",
            exam=exam,
            total_marks=10,
            duration_minutes=30,
            status="active",
        )
        mock_test.questions.add(question)
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get(f"/api/mocktest/{mock_test.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Test")
        self.assertIn("questions", response.data)
        self.assertIn("remaining_seconds", response.data)

    def test_get_mock_test_not_found(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get("/api/mocktest/9999/")
        self.assertEqual(response.status_code, 404)

    def test_get_mock_test_unauthorized(self):
        user1 = User.objects.create_user(
            email="user1@example.com", password=TEST_PASSWORD
        )
        user2 = User.objects.create_user(
            email="user2@example.com", password=TEST_PASSWORD
        )
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        mock_test = MockTest.objects.create(user=user1, title="Test", exam=exam)
        client = APIClient()
        client.force_authenticate(user=user2)
        response = client.get(f"/api/mocktest/{mock_test.id}/")
        self.assertEqual(response.status_code, 404)


class TestStartTestView(TestCase):
    def test_start_test(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        mock_test = MockTest.objects.create(user=user, title="Test", exam=exam)
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post(f"/api/mocktest/start/{mock_test.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Test started")
        mock_test.refresh_from_db()
        self.assertIsNotNone(mock_test.started_at)

    def test_start_test_not_found(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post("/api/mocktest/start/9999/")
        self.assertEqual(response.status_code, 404)


class TestSubmitAnswerView(TestCase):
    def test_submit_answer(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        question = Question.objects.create(
            topic=topic,
            exam=exam,
            question_text="What is an array?",
            options={"A": "Data structure", "B": "Function"},
            correct_answer="A",
            source="llm",
        )
        mock_test = MockTest.objects.create(
            user=user, title="Test", exam=exam, total_marks=10
        )
        mock_test.questions.add(question)
        attempt = TestAttempt.objects.create(
            user=user, mock_test=mock_test, total_marks=10
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post(
            "/api/mocktest/submit-answer/",
            {
                "attempt_id": attempt.id,
                "question_id": question.id,
                "user_answer": "A",
                "time_taken_seconds": 30,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["is_correct"])
        self.assertEqual(response.data["selected_option"], "A")

    def test_submit_answer_invalid_attempt(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        question = Question.objects.create(
            topic=topic,
            exam=exam,
            question_text="What is an array?",
            correct_answer="A",
            source="llm",
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post(
            "/api/mocktest/submit-answer/",
            {
                "attempt_id": 9999,
                "question_id": question.id,
                "user_answer": "A",
                "time_taken_seconds": 30,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_submit_answer_missing_fields(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post(
            "/api/mocktest/submit-answer/",
            {
                "attempt_id": 1,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)


class TestTestResultView(TestCase):
    def test_get_test_results(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        question = Question.objects.create(
            topic=topic,
            exam=exam,
            question_text="What is an array?",
            options={"A": "DS", "B": "Func"},
            correct_answer="A",
            explanation="Arrays are DS",
            source="llm",
        )
        mock_test = MockTest.objects.create(
            user=user, title="Test", exam=exam, total_marks=10
        )
        mock_test.questions.add(question)
        attempt = TestAttempt.objects.create(
            user=user, mock_test=mock_test, total_marks=10
        )
        Answer.objects.create(
            attempt=attempt,
            question=question,
            user_answer="A",
            is_correct=True,
            marks_obtained=1.0,
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post(
            "/api/mocktest/results/", {"attempt_id": attempt.id}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("score", response.data)

    def test_get_test_results_list(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        mock_test = MockTest.objects.create(user=user, title="Test", exam=exam)
        TestAttempt.objects.create(
            user=user,
            mock_test=mock_test,
            score=40,
            percentage=80.0,
            submitted_at=timezone.now(),
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get("/api/mocktest/results/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_get_test_results_missing_attempt_id(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post("/api/mocktest/results/", {}, format="json")
        self.assertEqual(response.status_code, 400)


class TestTestResultDetailView(TestCase):
    def test_get_test_result_detail(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        question = Question.objects.create(
            topic=topic,
            exam=exam,
            question_text="What is an array?",
            correct_answer="A",
            source="llm",
        )
        mock_test = MockTest.objects.create(user=user, title="Test", exam=exam)
        mock_test.questions.add(question)
        attempt = TestAttempt.objects.create(
            user=user,
            mock_test=mock_test,
            score=10,
            total_marks=10,
            percentage=100.0,
            correct_answers=1,
            submitted_at=timezone.now(),
        )
        Answer.objects.create(
            attempt=attempt,
            question=question,
            user_answer="A",
            is_correct=True,
            marks_obtained=1.0,
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get(f"/api/mocktest/results/{attempt.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["score"], 10)
        self.assertEqual(len(response.data["questions"]), 1)

    def test_get_test_result_detail_not_found(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get("/api/mocktest/results/9999/")
        self.assertEqual(response.status_code, 404)


class TestGenerateMockTestView(TestCase):
    def test_generate_mock_test(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        exam = Exam.objects.create(
            name="GATE CS",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=180),
        )
        subject = Subject.objects.create(exam=exam, name="Data Structures")
        topic = Topic.objects.create(name="Arrays", subject=subject)
        roadmap = Roadmap.objects.create(
            user=user, exam=exam, target_date=date.today() + timedelta(days=90)
        )
        RoadmapTopic.objects.create(
            roadmap=roadmap, topic=topic, week_number=1, day_number=1, phase="coverage"
        )
        Question.objects.create(
            topic=topic,
            exam=exam,
            question_text="What is an array?",
            options={"A": "Data structure", "B": "Function"},
            correct_answer="A",
            source="llm",
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post(
            "/api/mocktest/generate/",
            {"roadmap_id": roadmap.id, "day": 1, "num_questions": 1},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("mock_test", response.data)
        self.assertIn("attempt", response.data)

    def test_evaluate_test_not_found(self):
        from apps.mocktest.services import MockTestService
        result = MockTestService.evaluate_test(9999, [])
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Attempt not found")

    def test_normalize_options_dict(self):
        from apps.mocktest.views import MockTestDetailView
        opts = MockTestDetailView._normalize_options({"A": "a", "B": "b"})
        self.assertEqual(opts, {"A": "a", "B": "b"})

    def test_normalize_options_none(self):
        from apps.mocktest.views import MockTestDetailView
        opts = MockTestDetailView._normalize_options(None)
        self.assertEqual(opts, {})

    def test_normalize_options_list(self):
        from apps.mocktest.views import MockTestDetailView
        opts = MockTestDetailView._normalize_options(["opt1", "opt2"])
        self.assertEqual(opts, {"A": "opt1", "B": "opt2"})

    def test_generate_mock_test_missing_params(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post("/api/mocktest/generate/", {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_generate_mock_test_invalid_roadmap(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASSWORD
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post(
            "/api/mocktest/generate/", {"roadmap_id": 9999, "day": 1}, format="json"
        )
        self.assertEqual(response.status_code, 400)


# ---------------- Service Helper Tests ----------------
class TestServiceHelpers(TestCase):
    def test_clean_markdown(self):
        content = "```json\n[{\"question\": \"test\"}]\n```"
        result = MockTestService._clean_markdown(content)
        self.assertIn("[{", result)

    def test_clean_markdown_no_fence(self):
        content = '{"question": "test"}'
        result = MockTestService._clean_markdown(content)
        self.assertEqual(result, '{"question": "test"}')

    def test_extract_json_array(self):
        content = '[{"question": "test"}]extra'
        result = MockTestService._extract_json_array(content, 0)
        self.assertIn('{"question', result)

    def test_parse_json_content_valid(self):
        content = '[{"question": "test", "options": {"A": "a"}}]'
        result = MockTestService._parse_json_content(content)
        self.assertEqual(len(result), 1)

    def test_parse_json_content_invalid(self):
        result = MockTestService._parse_json_content("invalid")
        self.assertEqual(result, [])

    def test_build_llm_prompt(self):
        result = MockTestService._build_llm_prompt("Arrays", 5)
        self.assertIn("Arrays", result)

    def test_finalize_test_counts_all_questions(self):
        user = User.objects.create_user(
            email="fin@example.com", password=TEST_PASSWORD
        )
        exam = Exam.objects.create(
            name="GATE CE",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=120),
        )
        subject = Subject.objects.create(exam=exam, name="Structures")
        topic = Topic.objects.create(name="Beam", subject=subject)

        q1 = Question.objects.create(
            topic=topic,
            exam=exam,
            question_text="Q1",
            options={"A": "1", "B": "2"},
            correct_answer="A",
            source="llm",
        )
        q2 = Question.objects.create(
            topic=topic,
            exam=exam,
            question_text="Q2",
            options={"A": "3", "B": "4"},
            correct_answer="B",
            source="llm",
        )

        mock_test = MockTest.objects.create(user=user, title="T1", exam=exam)
        mock_test.questions.add(q1, q2)
        attempt = TestAttempt.objects.create(user=user, mock_test=mock_test)

        Answer.objects.create(
            attempt=attempt,
            question=q1,
            user_answer="A",
            is_correct=True,
            marks_obtained=1.0,
        )

        result = MockTestService.finalize_test(attempt.id)
        self.assertIsNotNone(result)
        self.assertEqual(result.correct_answers, 1)
        self.assertEqual(result.incorrect_answers, 0)
        self.assertEqual(result.unanswered, 1)

    def test_submit_answer_matches_textual_correct_answer(self):
        user = User.objects.create_user(
            email="submit-text@example.com", password=TEST_PASSWORD
        )
        exam = Exam.objects.create(
            name="GATE EE",
            category="Engineering",
            total_marks=100,
            exam_date=date.today() + timedelta(days=120),
        )
        subject = Subject.objects.create(exam=exam, name="Network")
        topic = Topic.objects.create(name="Basics", subject=subject)
        q = Question.objects.create(
            topic=topic,
            exam=exam,
            question_text="Capital of France?",
            options={"A": "London", "B": "Paris"},
            correct_answer="Paris",
            source="llm",
        )
        test = MockTest.objects.create(user=user, title="T2", exam=exam)
        test.questions.add(q)
        attempt = TestAttempt.objects.create(user=user, mock_test=test)

        answer, _ = MockTestService.submit_answer(
            user=user,
            attempt_id=attempt.id,
            question_id=q.id,
            user_answer="B",
            time_taken_seconds=5,
        )
        self.assertIsNotNone(answer)
        self.assertTrue(answer.is_correct)

    def test_process_llm_response_empty(self):
        result = MockTestService._process_llm_response("", [])
        self.assertEqual(result, [])

    def test_generate_llm_questions_with_retry_no_topics(self):
        result = MockTestService._generate_llm_questions_with_retry([], 1, max_retries=1)
        self.assertEqual(result, [])
