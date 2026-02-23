from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from worker.tasks import generate_roadmap_async

from .models import Roadmap, RoadmapGenerationJob, Exam
from .serializers import (
    RoadmapGenerateSerializer,
    RoadmapSerializer,
    RoadmapTopicSerializer,
    ExamSerializer
)
from .services import RoadmapService, Exam



class ExamListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        exams = Exam.objects.all()

        serializer = ExamSerializer(exams, many=True)

        return Response(serializer.data)


# ==================================================
# GENERATE ROADMAP (ASYNC)
# ==================================================

class RoadmapGenerateView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = RoadmapGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Create async job record
        job = RoadmapGenerationJob.objects.create(
            user=request.user,
            status="pending"
        )

        # Send async celery task
        generate_roadmap_async.delay(
            job.id,
            request.user.id,
            data["exam_id"],
            str(data["target_date"]),
            data["difficulty_level"],
            data["study_hours_per_day"],
            data.get("current_knowledge", ""),
            data.get("target_marks", None),
        )

        return Response(
            {
                "job_id": job.id,
                "status": "pending"
            },
            status=status.HTTP_202_ACCEPTED
        )


# ==================================================
# JOB STATUS (POLLING ENDPOINT)
# ==================================================

class RoadmapJobStatusView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):

        job = get_object_or_404(
            RoadmapGenerationJob,
            id=job_id,
            user=request.user
        )

        return Response({
            "job_id": job.id,
            "status": job.status,
            "roadmap_id": job.roadmap.id if job.roadmap else None,
            "error": getattr(job, "error_message", None)
        })


# ==================================================
# LIST USER ROADMAPS
# ==================================================

class RoadmapListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        roadmaps = Roadmap.objects.filter(user=request.user)

        serializer = RoadmapSerializer(roadmaps, many=True)

        return Response(serializer.data)


# ==================================================
# ROADMAP DETAIL + ACTIONS
# ==================================================

class RoadmapDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):

        return get_object_or_404(
            Roadmap,
            pk=pk,
            user=request.user
        )

    # ---------- GET SINGLE ROADMAP ----------

    def get(self, request, pk):

        roadmap = self.get_object(request, pk)

        serializer = RoadmapSerializer(roadmap)

        return Response(serializer.data)

    # ---------- PATCH (UPDATE / COMPLETE TOPIC) ----------

    def patch(self, request, pk):

        roadmap = self.get_object(request, pk)

        # Topic completion action

        if request.data.get("action") == "complete" and "topic_id" in request.data:

            topic = RoadmapService.mark_topic_completed(
                request.data["topic_id"],
                request.user
            )

            if not topic:
                return Response(
                    {"error": "Topic not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(
                RoadmapTopicSerializer(topic).data
            )

        # Normal update

        serializer = RoadmapSerializer(
            roadmap,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    # ---------- DELETE ----------

    def delete(self, request, pk):

        roadmap = self.get_object(request, pk)

        roadmap.delete()

        return Response(
            {"message": "Roadmap deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
