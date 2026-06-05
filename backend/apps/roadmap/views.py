import logging

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Roadmap, RoadmapTopic
from .serializers import (
    RoadmapSerializer,
    ExamSerializer,
    DeterministicRoadmapGenerateSerializer,
)
from .utils.roadmap_utils import (
    get_exams,
    get_roadmaps,
    get_roadmap_detail,
    update_roadmap,
    delete_roadmap,
    get_week_plan,
    toggle_topic_completion,
    get_week_progress,
    get_overall_progress,
    get_topic_study_data,
    get_roadmap_topics,
    activate_roadmap,
    generate_roadmap,
)

logger = logging.getLogger(__name__)


class ExamListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data, _, _ = get_exams()
        return Response(data)


class RoadmapListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data, _, _ = get_roadmaps(request.user)
        return Response(data)


class RoadmapDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        data, _, _ = get_roadmap_detail(request.user, pk)
        return Response(data)

    def patch(self, request, pk):
        data, error, _ = update_roadmap(request.user, pk, request.data)
        if error:
            return Response(error, status=status.HTTP_404_NOT_FOUND)
        return Response(data)

    def delete(self, request, pk):
        delete_roadmap(request.user, pk)
        return Response({"message": "Roadmap deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class DeterministicRoadmapGenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.info("DETERMINISTIC VIEW HIT")
        serializer = DeterministicRoadmapGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result, _, _ = generate_roadmap(
            user=request.user,
            exam_id=data["exam_id"],
            target_date=data["target_date"],
            study_hours_per_day=data["study_hours_per_day"],
        )
        return Response(result, status=status.HTTP_201_CREATED)


class WeekPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, roadmap_id, week_number):
        data, _, _ = get_week_plan(roadmap_id, week_number)
        return Response(data)


class TopicCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, topic_id):
        data, _, _ = toggle_topic_completion(topic_id)
        return Response(data)


class WeekProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, roadmap_id, week_number):
        data, _, _ = get_week_progress(roadmap_id, week_number)
        return Response(data)


class RoadmapProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, roadmap_id):
        data, _, _ = get_overall_progress(roadmap_id)
        return Response(data)


class TopicStudyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, topic_id):
        data, _, _ = get_topic_study_data(topic_id)
        return Response(data)


class RoadmapTopicsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, roadmap_id):
        data, _, _ = get_roadmap_topics(roadmap_id)
        return Response(data)


class ActivateRoadmapView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, roadmap_id):
        result, error, _ = activate_roadmap(request.user, roadmap_id)
        if error:
            return Response(error, status=404)
        return Response(result)