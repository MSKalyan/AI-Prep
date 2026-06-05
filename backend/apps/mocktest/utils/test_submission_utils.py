import logging
from django.utils import timezone

from ..serializers import SubmitAnswerSerializer
from ..services.test_submission_service import TestSubmissionService

logger = logging.getLogger(__name__)


def submit_answer(request):
    serializer = SubmitAnswerSerializer(data=request.data)
    if not serializer.is_valid():
        return None, serializer.errors, 400

    attempt_id = serializer.validated_data["attempt_id"]
    question_id = serializer.validated_data["question_id"]
    user_answer = serializer.validated_data["user_answer"]
    time_taken = serializer.validated_data.get("time_taken_seconds", 0)

    answer, attempt = TestSubmissionService.submit_answer(
        user=request.user,
        attempt_id=attempt_id,
        question_id=question_id,
        user_answer=user_answer,
        time_taken_seconds=time_taken,
    )

    if not answer or not attempt:
        return None, {"error": "Invalid attempt or question"}, 400

    if attempt.user != request.user:
        return None, {"error": "Unauthorized"}, 403

    if attempt.submitted_at:
        return None, {"error": "Test already submitted"}, 400

    total_questions = attempt.mock_test.questions.count()
    answered = attempt.answers.exclude(user_answer__isnull=True).count()

    return {
        "question_id": question_id,
        "selected_option": answer.user_answer,
        "is_correct": answer.is_correct,
        "marks_obtained": answer.marks_obtained,
        "progress": {"answered": answered, "total": total_questions},
    }, None, None


def start_test(pk, user):
    from ..models import MockTest

    try:
        mock_test = MockTest.objects.get(pk=pk, user=user)
    except MockTest.DoesNotExist:
        return None, {"error": "Test not found"}, 404

    if not mock_test.started_at:
        mock_test.started_at = timezone.now()
        mock_test.save(update_fields=["started_at"])

    return {"message": "Test started"}, None, None