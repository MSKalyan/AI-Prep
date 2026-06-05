import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .utils.analytics_utils import (
    get_topic_performance,
    get_adaptive_study_plan,
    get_study_content,
    get_user_analytics,
)

logger = logging.getLogger(__name__)


class TopicPerformanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        data, error, status_code = get_topic_performance(request.user)
        if error:
            return Response(error, status=status_code)
        return Response(data)


class AdaptiveStudyPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        data, error, status_code = get_adaptive_study_plan(request.user)
        if error:
            return Response(error, status=status_code)
        return Response(data)


class UserAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        result, error, status_code = get_user_analytics(request.user)
        if error:
            return Response(error, status=status_code)
        return Response(result)


class StudyContentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        topic_name = request.query_params.get("topic_name")
        result, error, status_code = get_study_content(topic_name)
        if error:
            return Response(error, status=status_code)
        return Response(result)