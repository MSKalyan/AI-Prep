import logging

from django.utils import timezone

from ..models import MockTest, TestAttempt
from ..serializers import MockTestDetailSerializer, TestAttemptSerializer

logger = logging.getLogger(__name__)


def get_mock_test_detail(pk, user):
    try:
        mock_test = MockTest.objects.get(pk=pk, user=user)
    except MockTest.DoesNotExist:
        return None, {"error": "Mock test not found"}, 404

    attempt = get_or_create_attempt(mock_test, user)

    if not mock_test.started_at:
        mock_test.started_at = timezone.now()
        mock_test.save(update_fields=["started_at"])

    remaining_seconds = calculate_remaining_time(mock_test)
    questions_data = build_questions(mock_test, attempt)

    data = build_response(mock_test, attempt, questions_data, remaining_seconds)
    return data, None, None


def get_or_create_attempt(mock_test, user):
    attempt = TestAttempt.objects.filter(
        mock_test=mock_test, user=user, submitted_at__isnull=True
    ).first()

    if not attempt:
        attempt = TestAttempt.objects.create(
            user=user,
            mock_test=mock_test,
            total_marks=mock_test.total_marks,
        )
    return attempt


def calculate_remaining_time(mock_test):
    now = timezone.now()
    total_seconds = mock_test.duration_minutes * 60

    if not mock_test.started_at:
        return total_seconds

    elapsed = (now - mock_test.started_at).total_seconds()
    return max(0, int(total_seconds - elapsed))


def build_questions(mock_test, attempt):
    from .question_utils import format_options, get_selected_answer

    data = []

    for idx, q in enumerate(mock_test.questions.all(), start=1):
        options = format_options(q)
        selected = get_selected_answer(attempt, q)

        data.append({
            "id": q.id,
            "question_text": q.question_text,
            "options": options,
            "selected_option": selected,
            "is_answered": selected is not None,
            "question_number": idx,
            "topic": q.topic.name if q.topic else None,
        })

    return data


def build_response(mock_test, attempt, questions_data, remaining):
    return {
        "id": mock_test.id,
        "topics": list(
            mock_test.questions.values_list("topic__name", flat=True).distinct()
        ),
        "title": mock_test.title,
        "description": mock_test.description,
        "duration_minutes": mock_test.duration_minutes,
        "remaining_seconds": remaining,
        "total_marks": mock_test.total_marks,
        "question_count": mock_test.questions.count(),
        "attempt_id": attempt.id,
        "questions": questions_data,
        "answers": [
            {"question": a.question.id, "user_answer": a.user_answer}
            for a in attempt.answers.all()
        ],
    }