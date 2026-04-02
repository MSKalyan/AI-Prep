from django.test import TestCase
from django.utils import timezone
from apps.mocktest.models import Question, MockTest, TestAttempt, Answer
from apps.roadmap.models import Topic, Exam, Subject, Roadmap
from apps.users.models import User


class QuestionModelTest(TestCase):

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
            name="Arrays",
            subject=self.subject
        )

    def test_create_question(self):
        question = Question.objects.create(
            topic=self.topic,
            exam=self.exam,
            question_text="What is an array?",
            question_type="mcq",
            options=["A data structure", "A function", "A loop"],
            correct_answer="A data structure",
            explanation="Arrays are fundamental data structures",
            difficulty="easy",
            marks=1,
            source="llm"
        )
        self.assertEqual(question.question_text, "What is an array?")
        self.assertEqual(question.correct_answer, "A data structure")
        self.assertEqual(question.difficulty, "easy")

    def test_question_string_representation(self):
        question = Question.objects.create(
            topic=self.topic,
            exam=self.exam,
            question_text="Sample question",
            correct_answer="Answer",
            source="pyq",
            difficulty="medium"
        )
        self.assertEqual(str(question), f"{self.topic} (pyq) - medium")


class MockTestModelTest(TestCase):

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
        self.roadmap = Roadmap.objects.create(
            user=self.user,
            exam=self.exam,
            target_date=timezone.now().date()
        )

    def test_create_mock_test(self):
        mock_test = MockTest.objects.create(
            user=self.user,
            roadmap=self.roadmap,
            title="DSA Practice Test",
            description="Practice questions for data structures",
            exam=self.exam,
            total_marks=50,
            question_count=10,
            duration_minutes=60,
            status="active"
        )
        self.assertEqual(mock_test.title, "DSA Practice Test")
        self.assertEqual(mock_test.user, self.user)
        self.assertEqual(mock_test.status, "active")

    def test_mock_test_string_representation(self):
        mock_test = MockTest.objects.create(
            user=self.user,
            title="Test Title"
        )
        self.assertEqual(str(mock_test), f"Test Title - {self.user}")


class TestAttemptModelTest(TestCase):

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
        self.mock_test = MockTest.objects.create(
            user=self.user,
            title="Test",
            exam=self.exam
        )

    def test_create_test_attempt(self):
        attempt = TestAttempt.objects.create(
            user=self.user,
            mock_test=self.mock_test,
            score=40.0,
            total_marks=50,
            percentage=80.0,
            correct_answers=8,
            incorrect_answers=2,
            time_taken_minutes=45
        )
        self.assertEqual(attempt.user, self.user)
        self.assertEqual(attempt.mock_test, self.mock_test)
        self.assertEqual(attempt.score, 40.0)
        self.assertEqual(attempt.percentage, 80.0)

    def test_test_attempt_string_representation(self):
        attempt = TestAttempt.objects.create(
            user=self.user,
            mock_test=self.mock_test,
            percentage=75.5
        )
        self.assertEqual(str(attempt), f"{self.mock_test.title} - {self.user} - 75.5%")


class AnswerModelTest(TestCase):

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
        self.question = Question.objects.create(
            topic=self.topic,
            exam=self.exam,
            question_text="What is an array?",
            correct_answer="A data structure",
            source="llm"
        )
        self.mock_test = MockTest.objects.create(
            user=self.user,
            title="Test",
            exam=self.exam
        )
        self.attempt = TestAttempt.objects.create(
            user=self.user,
            mock_test=self.mock_test
        )

    def test_create_answer(self):
        answer = Answer.objects.create(
            attempt=self.attempt,
            question=self.question,
            user_answer="A data structure",
            is_correct=True,
            marks_obtained=1.0,
            time_taken_seconds=30
        )
        self.assertEqual(answer.attempt, self.attempt)
        self.assertEqual(answer.question, self.question)
        self.assertTrue(answer.is_correct)
        self.assertEqual(answer.marks_obtained, 1.0)

    def test_answer_string_representation(self):
        answer = Answer.objects.create(
            attempt=self.attempt,
            question=self.question,
            is_correct=False
        )
        self.assertEqual(str(answer), f"Q{self.question.id} - Incorrect")

    def test_unique_answer_per_attempt_question(self):
        # Create first answer
        Answer.objects.create(
            attempt=self.attempt,
            question=self.question,
            user_answer="Answer 1"
        )
        # Try to create another for same attempt-question - should fail
        with self.assertRaises(Exception):
            Answer.objects.create(
                attempt=self.attempt,
                question=self.question,
                user_answer="Answer 2"
            )