import logging

from ..models import TestAttempt
from ..services.test_submission_service import TestSubmissionService
from apps.analytics.services.services import AnalyticsService

logger = logging.getLogger(__name__)


def get_recent_results(user):
    attempts = (
        TestAttempt.objects.filter(user=user, submitted_at__isnull=False)
        .select_related("mock_test")
        .order_by("-submitted_at")[:20]
    )

    results = []
    for attempt in attempts:
        answers = list(attempt.answers.select_related("question__topic", "question__topic__parent").all())
        
        topic_name = None
        subject = None
        
        if answers:
            first = answers[0]
            if first and first.question:
                topic = getattr(first.question, 'topic', None)
                if topic:
                    topic_name = topic.name
                    parent = getattr(topic, 'parent', None)
                    if parent:
                        subject = parent.name

        results.append({
            "attempt_id": attempt.id,
            "mock_test_id": attempt.mock_test.id,
            "title": f"{subject} - {topic_name}" if topic_name else attempt.mock_test.title,
            "topic": topic_name,
            "subject": subject,
            "score": attempt.score or 0,
            "percentage": attempt.percentage or 0,
            "correct": attempt.correct_answers or 0,
            "incorrect": attempt.incorrect_answers or 0,
            "date": attempt.submitted_at,
        })

    return results, None, None


def finalize_test(attempt_id, user):
    attempt = TestSubmissionService.finalize_test(attempt_id)

    if not attempt or attempt.user != user:
        return None, {"error": "Test attempt not found"}, 404

    AnalyticsService.create_performance_snapshot(attempt)

    questions_result = []
    answers = attempt.answers.select_related("question")
    for ans in answers:
        q = ans.question
        questions_result.append({
            "question_id": q.id,
            "question_text": q.question_text,
            "your_answer": ans.user_answer,
            "correct_answer": q.correct_answer,
            "is_correct": ans.is_correct,
            "marks_obtained": ans.marks_obtained,
            "explanation": q.explanation,
        })

    return {
        "attempt_id": attempt.id,
        "mock_test_id": attempt.mock_test.id,
        "mock_test_title": attempt.mock_test.title,
        "score": attempt.score,
        "total_marks": attempt.total_marks,
        "percentage": attempt.percentage,
        "correct": attempt.correct_answers,
        "incorrect": attempt.incorrect_answers,
        "unanswered": attempt.unanswered,
        "time_taken_minutes": attempt.time_taken_minutes,
        "questions": questions_result,
    }, None, None


def get_test_result_detail(attempt_id, user):
    attempt = TestAttempt.objects.get(id=attempt_id, user=user)
    answers = attempt.answers.select_related("question")
    topic = getattr(attempt.mock_test, "topic", None)

    topic_name = topic.name if topic else None
    subject = topic.parent.name if topic and topic.parent else None
    questions = []

    for ans in answers:
        q = ans.question
        questions.append({
            "question_id": q.id,
            "question_text": q.question_text,
            "options": q.options,
            "your_answer": ans.user_answer,
            "correct_answer": q.correct_answer,
            "is_correct": ans.is_correct,
            "marks_obtained": ans.marks_obtained,
            "explanation": q.explanation,
        })

    return {
        "attempt_id": attempt.id,
        "topic": topic_name,
        "subject": subject,
        "score": attempt.score,
        "total_marks": attempt.total_marks,
        "percentage": attempt.percentage,
        "correct": attempt.correct_answers,
        "incorrect": attempt.incorrect_answers,
        "unanswered": attempt.unanswered,
        "time_taken": attempt.time_taken_minutes,
        "questions": questions,
    }, None, None