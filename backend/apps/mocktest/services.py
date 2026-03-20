from django.utils import timezone
from django.db import transaction
from .models import Question, MockTest, TestAttempt, Answer


class MockTestService:
    """Service layer for mock test operations"""

    @staticmethod
    def create_mock_test(user, topic, num_questions=5, duration_minutes=60):
        """Create a new mock test using PYQs (source='pyq')"""

        # Fetch PYQs for topic
        questions = Question.objects.filter(
            topic=topic,
            source='pyq'
        )

        total_available = questions.count()

        if total_available == 0:
            raise ValueError("No PYQs available for this topic")

        if total_available < num_questions:
            num_questions = total_available

        # Random selection
        questions = questions.order_by('?')[:num_questions]

        # Create test inside transaction
        with transaction.atomic():

            mock_test = MockTest.objects.create(
                user=user,
                title=f"{topic.name} Practice Test",
                exam=questions.first().exam if questions else None,
                description=f"{topic.name} Topic Test",
                duration_minutes=duration_minutes,
                status='active'
            )

            total_marks = 0

            for question in questions:
                mock_test.questions.add(question)
                total_marks += question.marks

            mock_test.total_marks = total_marks
            mock_test.question_count = questions.count()
            mock_test.save()

        return mock_test

    @staticmethod
    def start_test_attempt(user, mock_test_id):
        """Start a new test attempt"""
        try:
            mock_test = MockTest.objects.get(id=mock_test_id)

            attempt = TestAttempt.objects.create(
                user=user,
                mock_test=mock_test,
                total_marks=mock_test.total_marks
            )

            if not mock_test.started_at:
                mock_test.started_at = timezone.now()
                mock_test.save()

            return attempt
        except MockTest.DoesNotExist:
            return None

    @staticmethod
    def submit_answer(attempt_id, question_id, user_answer, time_taken_seconds=0):
        """Submit an answer for a question"""
        try:
            attempt = TestAttempt.objects.get(id=attempt_id)
            question = Question.objects.get(id=question_id)

            is_correct = MockTestService._check_answer(question, user_answer)

            marks_obtained = 0
            if is_correct:
                marks_obtained = question.marks
            elif user_answer:
                marks_obtained = -question.negative_marks

            answer, created = Answer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    'user_answer': user_answer,
                    'is_correct': is_correct,
                    'marks_obtained': marks_obtained,
                    'time_taken_seconds': time_taken_seconds
                }
            )

            return answer,attempt
        except (TestAttempt.DoesNotExist, Question.DoesNotExist):
            return None, None

    @staticmethod
    def _check_answer(question, user_answer):
        """Check if the answer is correct"""
        if not user_answer:
            return False

        return question.correct_answer.strip().lower() == user_answer.strip().lower()

    @staticmethod
    def finalize_test(attempt_id):
        """Calculate final score and mark test as completed"""
        try:
            attempt = TestAttempt.objects.get(id=attempt_id)

            answers = attempt.answers.all()
            total_questions = answers.count()

            correct = answers.filter(is_correct=True).count()
            incorrect = answers.filter(
                is_correct=False,
                user_answer__isnull=False
            ).exclude(user_answer='').count()

            unanswered = total_questions - (correct + incorrect)

            total_score = sum(ans.marks_obtained for ans in answers)

            percentage = (
                (total_score / attempt.total_marks * 100)
                if attempt.total_marks > 0 else 0
            )

            time_taken = sum([
                ans.time_taken_seconds for ans in answers
            ]) / 60
            attempt.submitted_at = timezone.now()
            attempt.score = total_score
            attempt.percentage = max(0, percentage)
            attempt.correct_answers = correct
            attempt.incorrect_answers = incorrect
            attempt.unanswered = unanswered
            attempt.time_taken_minutes = int(time_taken)
            attempt.save()

            mock_test = attempt.mock_test
            mock_test.status = 'completed'
            mock_test.completed_at = timezone.now()
            mock_test.save()

            return attempt

        except TestAttempt.DoesNotExist:
            return None

    @staticmethod
    def generate_ai_questions(*args, **kwargs):
        """
        Deprecated for Sprint 6.
        Will be redesigned later with new Question schema.
        """
        return []