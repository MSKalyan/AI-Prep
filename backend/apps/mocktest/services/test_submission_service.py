import logging
from django.utils import timezone

from ..models import Question, TestAttempt, Answer

logger = logging.getLogger(__name__)


class TestSubmissionService:
    @staticmethod
    def submit_answer(user, attempt_id, question_id, user_answer, time_taken_seconds=0):
        logger.debug("=== SUBMIT ANSWER DEBUG ===")
        logger.debug("user: %s, attempt_id: %s, question_id: %s", user, attempt_id, question_id)
        logger.debug("user_answer: %s", user_answer)

        try:
            attempt = TestAttempt.objects.select_related("mock_test").get(id=attempt_id, user=user)
            logger.debug("Attempt found: %s", attempt.id)
        except TestAttempt.DoesNotExist:
            logger.warning("TestAttempt not found for attempt_id=%s and user_id=%s", attempt_id, getattr(user, "id", None))
            return None, None

        try:
            question = Question.objects.get(id=question_id)
            logger.debug("Question found: %s, correct_answer: %s", question.id, question.correct_answer)
        except Question.DoesNotExist:
            logger.warning("Question not found for question_id=%s", question_id)
            return None, attempt

        from .question_utils import QuestionUtils
        normalized_user_answer, _, is_correct = QuestionUtils.resolve_answer_values(question, user_answer)

        logger.debug("normalized_user_answer: %s, is_correct: %s", normalized_user_answer, is_correct)

        try:
            answer, created = Answer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    "user_answer": normalized_user_answer,
                    "is_correct": is_correct,
                    "marks_obtained": question.marks if is_correct else 0,
                    "time_taken_seconds": time_taken_seconds,
                },
            )
            logger.info("Answer saved: answer_id=%s, created=%s, user_answer=%s, is_correct=%s", 
                        answer.id, created, answer.user_answer, answer.is_correct)
        except Exception as e:
            logger.error("Failed to save answer: %s", e)
            raise

        logger.debug("===========================")

        return answer, attempt

    @staticmethod
    def finalize_test(attempt_id):
        try:
            attempt = TestAttempt.objects.select_related("mock_test").get(id=attempt_id)
        except TestAttempt.DoesNotExist:
            logger.warning("Finalize: TestAttempt not found for id=%s", attempt_id)
            return None

        questions = list(attempt.mock_test.questions.all())
        answers_list = list(attempt.answers.all())
        answers_by_question_id = {a.question_id: a for a in answers_list}

        logger.info("Finalize: attempt_id=%s, questions_count=%s, answers_count=%s", 
                    attempt_id, len(questions), len(answers_list))

        total_marks = 0
        obtained_marks = 0
        correct = 0
        incorrect = 0
        unanswered = 0

        for question in questions:
            total_marks += question.marks
            answer = answers_by_question_id.get(question.id)
            if not answer or not (answer.user_answer or "").strip():
                unanswered += 1
                continue

            obtained_marks += answer.marks_obtained

            if answer.is_correct:
                correct += 1
            else:
                incorrect += 1

        logger.info("Finalize result: total_marks=%s, obtained=%s, correct=%s, incorrect=%s, unanswered=%s",
                    total_marks, obtained_marks, correct, incorrect, unanswered)

        attempt.score = obtained_marks
        attempt.total_marks = total_marks
        attempt.percentage = round((obtained_marks / total_marks * 100) if total_marks > 0 else 0, 2)
        attempt.correct_answers = correct
        attempt.incorrect_answers = incorrect
        attempt.unanswered = unanswered
        attempt.submitted_at = timezone.now()
        attempt.save()

        return attempt

    @staticmethod
    def evaluate_test(attempt_id, answers):
        try:
            attempt = TestAttempt.objects.get(id=attempt_id)
        except TestAttempt.DoesNotExist:
            return {"error": "Attempt not found"}

        correct = 0
        wrong = 0
        unanswered = 0
        total_marks = 0
        obtained_marks = 0
        detailed_results = []

        from .question_utils import QuestionUtils
        for answer in answers:
            evaluated = TestSubmissionService._evaluate_single_answer(attempt, answer, QuestionUtils)
            if not evaluated:
                continue

            question = evaluated["question"]
            total_marks += question.marks
            obtained_marks += evaluated["obtained_marks"]

            if evaluated["status"] == "correct":
                correct += 1
            elif evaluated["status"] == "wrong":
                wrong += 1
            else:
                unanswered += 1

            detailed_results.append({
                "question_id": question.id,
                "user_answer": evaluated["user_answer"],
                "correct_answer": evaluated["correct_answer"],
                "is_correct": evaluated["is_correct"],
                "marks": question.marks,
                "explanation": question.explanation,
            })

        attempt.score = obtained_marks
        attempt.completed_at = timezone.now()
        attempt.save()

        return {
            "attempt_id": attempt_id,
            "total_questions": correct + wrong + unanswered,
            "correct": correct,
            "wrong": wrong,
            "unanswered": unanswered,
            "total_marks": total_marks,
            "obtained_marks": obtained_marks,
            "percentage": round((obtained_marks / total_marks * 100) if total_marks > 0 else 0, 2),
            "results": detailed_results,
        }

    @staticmethod
    def _evaluate_single_answer(attempt, answer_payload, QuestionUtils):
        question_id = answer_payload.get("question_id")
        raw_user_answer = answer_payload.get("answer", "")

        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return None

        normalized_user_answer, normalized_correct_answer, is_correct = QuestionUtils.resolve_answer_values(question, raw_user_answer)
        marks_obtained = question.marks if is_correct else 0

        Answer.objects.create(
            attempt=attempt,
            question=question,
            user_answer=normalized_user_answer,
            is_correct=is_correct,
            marks_obtained=marks_obtained,
        )

        if is_correct:
            status = "correct"
        elif raw_user_answer:
            status = "wrong"
        else:
            status = "unanswered"

        return {
            "question": question,
            "user_answer": normalized_user_answer,
            "correct_answer": normalized_correct_answer,
            "is_correct": is_correct,
            "obtained_marks": marks_obtained,
            "status": status,
        }