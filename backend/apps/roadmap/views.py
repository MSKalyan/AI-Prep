from pydoc_data.topics import topics
import re

from django.utils import timezone

from urllib3 import request

from apps.roadmap.services.progress_service import ProgressService
from apps.ai_service.services.rag.llm_service import LLMService
from apps.roadmap.services.study_service import StudyService
from apps.analytics.services.adaptive_service import AdaptiveRoadmapService
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from django.db import transaction

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


    def get(self, request, pk):

        roadmap = self.get_object(request, pk)

        serializer = RoadmapSerializer(roadmap)

        return Response(serializer.data)


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


        serializer = RoadmapSerializer(
            roadmap,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


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

        # ---------- FETCH TOPICS ----------
        topics = RoadmapTopic.objects.select_related("topic", "topic__parent").filter(
            roadmap_id=roadmap_id,
            week_number=week_number
        ).order_by("day_number")

        # ---------- SERIALIZE ----------
        data = [
            {
                "id": t.id,
                "day": t.day_number,
                "topic": t.topic.name,
                "hours": t.estimated_hours,
                "completed": t.is_completed,
                "subject": t.topic.parent.name if t.topic.parent else None,
                "phase": t.phase
            }
            for t in topics
        ]

        # ---------- GROUP BY DAY ----------
        day_groups = {}

        for t in topics:
            day_groups.setdefault(t.day_number, []).append(t)

        # ---------- FIND CURRENT DAY ----------
        current_day = None

        if day_groups:
            for day in sorted(day_groups.keys()):
                day_items = day_groups[day]
                if not all(t.is_completed for t in day_items):
                    current_day = day
                    break

            if current_day is None:
                current_day = max(day_groups.keys())
        else:
            current_day = 1  # fallback

        # ---------- PRIORITY TOPICS ----------
        priority_topics = AdaptiveRoadmapService.generate_priority(request.user)

        # ---------- REVISION ----------
        revision = []

        if current_day != 1:

            weak_topics = [
                t for t in priority_topics
                if t["strength"] == "weak"
            ]

            today_topic_ids = set(
                t.topic_id for t in day_groups.get(current_day, [])
            )

            # 🔥 Avoid N+1 query
            roadmap_topics_map = {
                t.topic_id: t.id
                for t in RoadmapTopic.objects.filter(roadmap_id=roadmap_id)
            }

            for t in weak_topics:
                if t["topic_id"] in today_topic_ids:
                    continue

                roadmap_topic_id = roadmap_topics_map.get(t["topic_id"])

                if roadmap_topic_id:
                    revision.append({
                        "topic_id": t["topic_id"],
                        "topic_name": t["topic_name"],
                        "priority": t["priority"],
                        "roadmap_topic_id": roadmap_topic_id
                    })

            revision = revision[:3]

        # ---------- RESPONSE ----------
        return Response({
            "status": "success",
            "data": data,
            "today_revision": revision
        })
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

        # If explanation already exists, return it directly
        if topic.ai_explanation:
            return Response({
                "topic": topic.topic.name,
                "explanation": topic.ai_explanation
            })

        hours = topic.estimated_hours
        topic_name = topic.topic.name

        prompt = f"""
You are an expert tutor helping students quickly understand concepts for exams.

Explain the topic in a short and clear way so that a student can grasp the core idea quickly.

Topic: {topic_name}

Provide the explanation in below format:
 1. Concept Overview Explain what the topic is and its main idea in clear, simple terms.  
2. Key Points and Subtopics Summarize the important ideas, principles, or subtopics related to the topic that students should understand.

Instructions:
- Write a concise explanation of the topic.
- Focus on the main concept and why it is important.
- Mention one or two key points students should remember for exams.
- Use simple, clear language suitable for quick revision.
- Do not include headings, bullet points, or markdown.

Output rules:
-Give 5-6 points on It's sub topics.
- Write overview in a paragraph.
-keypoints in bullet points without using markdown symbols like - or *.
- Keep the entire explanation within 120 words.
"""

        llm = LLMService()

        explanation = llm.generate_response(
            prompt,
            user=request.user,
            endpoint="topic-explanation"
        )

        # Fallback if AI fails
        if not explanation:
            explanation = "Explanation unavailable."
        if explanation:
            explanation = re.sub(r'(?<=:)\s+', '\n', explanation)
            explanation = explanation.replace("**", "").strip()
        # Save explanation for future requests
        topic.ai_explanation = explanation
        topic.save(update_fields=["ai_explanation"])

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

class ActivateRoadmapView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, roadmap_id):

        user = request.user

        roadmap = Roadmap.objects.filter(
            id=roadmap_id,
            user=user
        ).first()

        if not roadmap:
            return Response({"error": "Roadmap not found"}, status=404)

        with transaction.atomic():

            Roadmap.objects.filter(
                user=user,
                is_active=True
            ).update(is_active=False)

            roadmap.is_active = True
            roadmap.save()

        return Response({"message": "Roadmap activated"})