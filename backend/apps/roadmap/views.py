from django.utils import timezone

from urllib3 import request

from apps.roadmap.services.progress_service import ProgressService
from apps.ai_service.services.llm_service import LLMService
from apps.roadmap.services.study_service import StudyService
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from worker.tasks import generate_roadmap_async

from .models import Roadmap, RoadmapGenerationJob, Exam, RoadmapTopic
from .serializers import (
    # RoadmapGenerateSerializer,
    RoadmapSerializer,
    RoadmapTopicSerializer,
    ExamSerializer,
    DeterministicRoadmapGenerateSerializer
)
from .services.roadmap_service import RoadmapService



class ExamListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        exams = Exam.objects.all()

        serializer = ExamSerializer(exams, many=True)

        return Response(serializer.data)


# # ==================================================
# # GENERATE ROADMAP (ASYNC)
# # ==================================================

# class RoadmapGenerateView(APIView):

#     permission_classes = [IsAuthenticated]

#     def post(self, request):

#         serializer = RoadmapGenerateSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         data = serializer.validated_data

#         # Create async job record
#         job = RoadmapGenerationJob.objects.create(
#             user=request.user,
#             status="pending"
#         )

#         # Send async celery task
#         generate_roadmap_async.delay(
#             job.id,
#             request.user.id,
#             data["exam_id"],
#             str(data["target_date"]),
#             data["difficulty_level"],
#             data["study_hours_per_day"],
#             data.get("current_knowledge", ""),
#             data.get("target_marks", None),
#         )

#         return Response(
#             {
#                 "job_id": job.id,
#                 "status": "pending"
#             },
#             status=status.HTTP_202_ACCEPTED
#         )


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

        roadmaps = (
            Roadmap.objects
            .filter(user=request.user)
            .select_related("exam")      # if serializer includes exam
            .prefetch_related("topics__topic__parent")  # reverse FK
        )
        serializer = RoadmapSerializer(roadmaps, many=True)

        return Response(serializer.data)


# ==================================================
# ROADMAP DETAIL + ACTIONS
# ==================================================

class RoadmapDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):

        return get_object_or_404(
            Roadmap.objects
        .select_related("exam")
        .prefetch_related("topics__topic__parent"),
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
class DeterministicRoadmapGenerateView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("DETERMINISTIC VIEW HIT")
        serializer = DeterministicRoadmapGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        exam = get_object_or_404(Exam, id=data["exam_id"])

        roadmap = RoadmapService.generate_deterministic_roadmap(
            user=request.user,
            exam_id=exam.id,
            target_date=data["target_date"],
            study_hours_per_day=data["study_hours_per_day"]
        )

        return Response(
            {
                "roadmap_id": roadmap.id,
                "total_weeks": roadmap.total_weeks,
                "message": "Roadmap generated successfully"
            },
            status=status.HTTP_201_CREATED
        )
    
class WeekPlanView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, roadmap_id, week_number):

        topics = RoadmapTopic.objects.filter(
            roadmap_id=roadmap_id,
            week_number=week_number
        ).order_by("day_number")

        data = [
            {
                "id": t.id,
                "day": t.day_number,
                "topic": t.topic.name,
                "hours": t.estimated_hours,
                "completed": t.is_completed
            }
            for t in topics
        ]

        return Response(data)
    

class TopicCompleteView(APIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, topic_id):

        topic = get_object_or_404(RoadmapTopic, id=topic_id)

        # toggle completion
        topic.is_completed = not topic.is_completed

        if topic.is_completed:
            topic.completed_at = timezone.now()
        else:
            topic.completed_at = None

        topic.save()

        return Response({
            "topic_id": topic.id,
            "completed": topic.is_completed
        })
    
class WeekProgressView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, roadmap_id, week_number):

        progress = ProgressService.get_week_progress(
            roadmap_id,
            week_number
        )

        return Response(progress)
    

class RoadmapProgressView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, roadmap_id):

        progress = ProgressService.get_overall_progress(roadmap_id)

        return Response(progress)
    
class TopicExplanationView(APIView):

    permission_classes = [IsAuthenticated]

  
    def get(self, request, topic_id):

        topic = get_object_or_404(RoadmapTopic, id=topic_id)
        hours = topic.estimated_hours
        topic_name = topic.topic.name

        prompt = f"""
        You are an AI tutor helping students prepare for technical exams.

        Explain the topic briefly and clearly.

        Topic: {topic}
        Recommended Study Time: {hours} hours

        Instructions:
        - Write a concise explanation suitable for exam preparation.
        - Focus on the core concept and its importance.
        - Avoid storytelling, analogies, or casual examples.
        - Do not mention study time in the explanation.
        - Use simple technical language.

        Output requirements:
        - 2–3 sentences only.
        - Do not include headings, markdown, or bullet points.
"""
        llm = LLMService()

        explanation = llm.generate_response(prompt)

        return Response({
            "topic": topic_name,
            "explanation": explanation
        })
    
class TopicStudyView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, topic_id):

        data = StudyService.get_topic_study_data(topic_id)

        return Response(data)
    
class RoadmapTopicsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, roadmap_id):

        topics = StudyService.get_roadmap_topics(roadmap_id)

        return Response(topics)