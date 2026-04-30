from django.utils import timezone
import logging
from django.db import DatabaseError
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Question, MockTest, TestAttempt
from apps.roadmap.models import Roadmap, Topic, RoadmapTopic
from .serializers import (
    QuestionSerializer,
    MockTestSerializer,
    MockTestDetailSerializer,
    TestAttemptSerializer,
    SubmitAnswerSerializer,
    GeneratePracticeSerializer,
)
from .services import MockTestService
from apps.analytics.services.services import AnalyticsService
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from groq import Groq
from django.conf import settings
from .models import Question
import json
from common.utils.retry_utils import safe_llm_call

logger = logging.getLogger(__name__)


class QuestionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        questions = Question.objects.all()

        exam_type = request.query_params.get("exam_type")
        subject = request.query_params.get("subject")
        difficulty = request.query_params.get("difficulty")
        topic = request.query_params.get("topic")

        if exam_type:
            questions = questions.filter(exam_type=exam_type)
        if subject:
            questions = questions.filter(subject=subject)
        if difficulty:
            questions = questions.filter(difficulty=difficulty)
        if topic:
            questions = questions.filter(topic__name__icontains=topic)

        serializer = QuestionSerializer(questions[:50], many=True)
        return Response(serializer.data)


class MockTestDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _normalize_options(raw_options):
        if raw_options is None:
            return {}

        if isinstance(raw_options, dict):
            return raw_options

        if isinstance(raw_options, str):
            try:
                parsed = json.loads(raw_options)
                if isinstance(parsed, dict):
                    return parsed
                if isinstance(parsed, list):
                    raw_options = parsed
            except (json.JSONDecodeError, TypeError, ValueError):
                logger.warning("Failed to parse question options payload", exc_info=True)
                return {}

        if isinstance(raw_options, list):
            option_keys = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            normalized = {}
            for idx, value in enumerate(raw_options):
                if idx >= len(option_keys):
                    break
                normalized[option_keys[idx]] = str(value)
            return normalized

        return {}

    def get(self, request, pk):
        try:
            mock_test = self._get_mock_test(pk, request.user)
            attempt = self._get_or_create_attempt(mock_test, request.user)

            self._ensure_test_started(mock_test)
            remaining_seconds = self._calculate_remaining_time(mock_test)

            questions_data = self._build_questions(mock_test, attempt)

            return Response(
                self._build_response(mock_test, attempt, questions_data, remaining_seconds)
            )

        except MockTest.DoesNotExist:
            return Response({"error": "Mock test not found"}, status=404)
    def _get_mock_test(self, pk, user):
        return MockTest.objects.get(pk=pk, user=user)

    def _get_or_create_attempt(self, mock_test, user):
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

    def _ensure_test_started(self, mock_test):
        if not mock_test.started_at:
            mock_test.started_at = timezone.now()
            mock_test.save(update_fields=["started_at"])

    def _calculate_remaining_time(self, mock_test):
        now = timezone.now()
        total_seconds = mock_test.duration_minutes * 60

        if not mock_test.started_at:
            return total_seconds

        elapsed = (now - mock_test.started_at).total_seconds()
        return max(0, int(total_seconds - elapsed))
    def _build_questions(self, mock_test, attempt):
        data = []

        for idx, q in enumerate(mock_test.questions.all(), start=1):
            options = self._format_options(q)
            selected = self._get_selected_answer(attempt, q)

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
    def _format_options(self, q):
        options_dict = self._normalize_options(q.options)
        return [{"key": k, "text": v} for k, v in options_dict.items()]


    def _get_selected_answer(self, attempt, q):
        ans = attempt.answers.filter(question=q).first()
        return ans.user_answer if ans else None
    def _build_response(self, mock_test, attempt, questions_data, remaining):
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

class StartTestView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        try:
            mock_test = MockTest.objects.get(pk=pk, user=request.user)
            if not mock_test.started_at:
                mock_test.started_at = timezone.now()
                mock_test.save(update_fields=["started_at"])
            return Response({"message": "Test started"})
        except MockTest.DoesNotExist:
            return Response({"error": "Test not found"}, status=404)


class SubmitAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SubmitAnswerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        attempt_id = serializer.validated_data["attempt_id"]
        question_id = serializer.validated_data["question_id"]
        user_answer = serializer.validated_data["user_answer"]
        time_taken = serializer.validated_data.get("time_taken_seconds", 0)
        answer, attempt = MockTestService.submit_answer(
            user=request.user,
            attempt_id=attempt_id,
            question_id=question_id,
            user_answer=user_answer,
            time_taken_seconds=time_taken,
        )
        if not answer or not attempt:
            return Response(
                {"error": "Invalid attempt or question"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if attempt.user != request.user:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        if attempt.submitted_at:
            return Response(
                {"error": "Test already submitted"}, status=status.HTTP_400_BAD_REQUEST
            )
        total_questions = attempt.mock_test.questions.count()
        answered = attempt.answers.exclude(user_answer__isnull=True).count()
        return Response(
            {
                "question_id": question_id,
                "selected_option": answer.user_answer,
                "is_correct": answer.is_correct,
                "marks_obtained": answer.marks_obtained,
                "progress": {"answered": answered, "total": total_questions},
            }
        )

class TestResultView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            attempts = self._get_recent_attempts(request.user)
            results = [self._build_result(a) for a in attempts]
            return Response(results)

        except (DatabaseError, ValueError, TypeError, AttributeError):
            logger.error("Failed to fetch test results", exc_info=True)
            return Response({"error": "Internal error"}, status=500)
    def _get_recent_attempts(self, user):
        return (
            TestAttempt.objects.filter(user=user, submitted_at__isnull=False)
            .select_related("mock_test")
            .order_by("-submitted_at")[:20]
        )
    def _build_result(self, attempt):
        answers = attempt.answers.select_related("question__topic").all()
        first = answers.first()

        topic = first.question.topic if first and first.question.topic else None
        topic_name = topic.name if topic else None
        subject = topic.parent.name if topic and topic.parent else None

        return {
            "attempt_id": attempt.id,
            "mock_test_id": attempt.mock_test.id,
            "title": f"{subject} - {topic_name}" if topic_name else attempt.mock_test.title,
            "topic": topic_name,
            "subject": subject,
            "score": attempt.score,
            "percentage": attempt.percentage,
            "correct": attempt.correct_answers,
            "incorrect": attempt.incorrect_answers,
            "date": attempt.submitted_at,
        }
    def post(self, request):
        attempt_id = request.data.get("attempt_id")

        if not attempt_id:
            return Response(
                {"error": "attempt_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        attempt = MockTestService.finalize_test(attempt_id)

        if not attempt or attempt.user != request.user:
            return Response(
                {"error": "Test attempt not found"}, status=status.HTTP_404_NOT_FOUND
            )
        AnalyticsService.create_performance_snapshot(attempt)
        questions_result = []
        answers = attempt.answers.select_related("question")
        for ans in answers:
            q = ans.question
            questions_result.append(
                {
                    "question_id": q.id,
                    "question_text": q.question_text,
                    "your_answer": ans.user_answer,
                    "correct_answer": q.correct_answer,
                    "is_correct": ans.is_correct,
                    "marks_obtained": ans.marks_obtained,
                    "explanation": q.explanation,
                }
            )
        return Response(
            {
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
            }
        )

class TestResultDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, attempt_id):
        try:
            attempt = TestAttempt.objects.get(id=attempt_id, user=request.user)

            answers = attempt.answers.select_related("question")
            topic = getattr(attempt.mock_test, "topic", None)

            topic_name = topic.name if topic else None
            subject = topic.parent.name if topic and topic.parent else None
            questions = []

            for ans in answers:
                q = ans.question

                questions.append(
                    {
                        "question_id": q.id,
                        "question_text": q.question_text,
                        "options": q.options,
                        "your_answer": ans.user_answer,
                        "correct_answer": q.correct_answer,
                        "is_correct": ans.is_correct,
                        "marks_obtained": ans.marks_obtained,
                        "explanation": q.explanation,
                    }
                )
            return Response(
                {
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
                }
            )
        except TestAttempt.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

class GenerateMockTestView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        data = self._validate_request(request)
        if isinstance(data, Response):
            return data
        try:
            roadmap = self._get_roadmap(data["roadmap_id"])
            topics = self._get_day_topics(roadmap, data["day"], data.get("topic_id"))
            if not topics:
                return Response({"error": "No topics found"}, status=400)
            result = self._create_test(request.user, roadmap, data, topics)
            return Response(result)
        except Roadmap.DoesNotExist:
            return Response({"error": "Invalid roadmap_id"}, status=400)
        except (DatabaseError, ValueError, TypeError, AttributeError, TimeoutError) as e:
            logger.error("Mock test generation failed", exc_info=True)
            return Response({"error": str(e)}, status=500)
    def _validate_request(self, request):
        roadmap_id = request.data.get("roadmap_id")
        day = request.data.get("day")
        if not roadmap_id or day is None:
            return Response({"error": "roadmap_id and day required"}, status=400)
        return {
            "roadmap_id": roadmap_id,
            "day": day,
            "topic_id": request.data.get("topic_id"),
            "num_questions": request.data.get("num_questions", 10),
        }
    def _get_roadmap(self, roadmap_id):
        return Roadmap.objects.get(id=roadmap_id)
    def _get_day_topics(self, roadmap, day, topic_id=None):
        queryset = Topic.objects.filter(
            roadmap_entries__roadmap=roadmap,
            roadmap_entries__day_number=day
        )
        if topic_id:
            # Frontend currently passes roadmap_topic id (`RoadmapTopic.id`) as `topic_id`.
            # Accept both:
            # 1) direct Topic.id
            # 2) RoadmapTopic.id belonging to this roadmap/day
            topic_match = queryset.filter(id=topic_id).distinct()
            if topic_match.exists():
                return list(topic_match)

            roadmap_entry = (
                RoadmapTopic.objects.filter(
                    id=topic_id,
                    roadmap=roadmap,
                )
                .select_related("topic")
                .first()
            )
            if roadmap_entry and roadmap_entry.topic_id:
                return list(
                    Topic.objects.filter(
                        id=roadmap_entry.topic_id,
                        roadmap_entries__roadmap=roadmap,
                    ).distinct()
                )
            return []
        return list(queryset.distinct())
    def _create_test(self, user, roadmap, data, topics):
        result = MockTestService.create_mock_test(
            user=user,
            roadmap=roadmap,
            day=data["day"],
            topics=topics,
            num_questions=data["num_questions"],
        )
        return {
            "mock_test": MockTestDetailSerializer(result["mock_test"]).data,
            "attempt": TestAttemptSerializer(result["attempt"]).data,
        }
class ExplainQuestionView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        question_id = request.data.get("question_id")
        try:
            question = Question.objects.get(id=question_id)
            explanation = self._generate_explanation(question)
            return Response({"explanation": explanation})
        except Question.DoesNotExist:
            return Response({"error": "Invalid question"}, status=400)
        except (DatabaseError, ValueError, TypeError, AttributeError, TimeoutError) as e:
            logger.error("Explain failed", exc_info=True)
            return Response({"error": str(e)}, status=500)
    def _generate_explanation(self, question):
        client = Groq(api_key=settings.GROQ_API_KEY)

        prompt = self._build_prompt(question)

        response = safe_llm_call(
            client,
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200,
        )
        text = response.choices[0].message.content.strip()
        return "\n".join([line for line in text.split("\n") if line.strip()])
    def _build_prompt(self, question):
        return f"""
    Explain this MCQ...

    Question: {question.question_text}
    Options: {question.options}
    Correct Answer: {question.correct_answer}
    """

