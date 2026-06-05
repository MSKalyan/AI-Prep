import logging

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.roadmap.models import Roadmap

from .models import Question, MockTest, TestAttempt
from .utils.mocktest_utils import (
    get_mock_test_detail,
    start_test,
    submit_answer,
    get_recent_results,
    finalize_test,
    get_test_result_detail,
    validate_generate_request,
    get_roadmap_topics,
    create_mock_test,
    explain_question,
)

logger = logging.getLogger(__name__)

class GenerateMockTestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data, error, status_code = validate_generate_request(request)
        if error:
            return Response(error, status=status_code)

        try:
            roadmap, topics = get_roadmap_topics(data["roadmap_id"], data["day"], data.get("topic_id"))
            if not topics:
                return Response({"error": "No topics found"}, status=400)

            result = create_mock_test(request.user, roadmap, data, topics)
            return Response(result)
        except Roadmap.DoesNotExist:
            return Response({"error": "Invalid roadmap_id"}, status=400)
        except Exception as e:
            logger.error("Mock test generation failed", exc_info=True)
            return Response({"error": str(e)}, status=500)
        
class StartTestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            data, _, _ = start_test(pk, request.user)
            return Response(data)
        except MockTest.DoesNotExist:
            return Response({"error": "Test not found"}, status=404)

class SubmitAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        result, error, status_code = submit_answer(request)
        if error:
            return Response(error, status=status_code)
        return Response(result)

class MockTestDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            data, _, _ = get_mock_test_detail(pk, request.user)
            return Response(data)
        except MockTest.DoesNotExist:
            return Response({"error": "Mock test not found"}, status=404)

class TestResultView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            data, _, _ = get_recent_results(request.user)
            return Response(data)
        except Exception as e:
            logger.error("Failed to fetch test results", exc_info=True)
            return Response({"error": "Internal error"}, status=500)

    def post(self, request):
        attempt_id = request.data.get("attempt_id")
        if not attempt_id:
            return Response({"error": "attempt_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        result, error, status_code = finalize_test(attempt_id, request.user)
        if error:
            return Response(error, status=status_code)
        return Response(result)


class TestResultDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, attempt_id):
        try:
            data, _, _ = get_test_result_detail(attempt_id, request.user)
            return Response(data)
        except TestAttempt.DoesNotExist:
            return Response({"error": "Not found"}, status=404)


class ExplainQuestionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        question_id = request.data.get("question_id")
        try:
            explanation, error, _ = explain_question(question_id)
            if error:
                return Response({"error": error}, status=400)
            return Response({"explanation": explanation})
        except Question.DoesNotExist:
            return Response({"error": "Invalid question"}, status=400)
        except Exception as e:
            logger.error("Explain failed", exc_info=True)
            return Response({"error": str(e)}, status=500)