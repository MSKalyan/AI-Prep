from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Question, MockTest, TestAttempt
from apps.roadmap.models import Roadmap, Topic
from .serializers import (
    QuestionSerializer,
    MockTestSerializer,
    MockTestDetailSerializer,
    TestAttemptSerializer,
    SubmitAnswerSerializer,
    GeneratePracticeSerializer
)
from .services import MockTestService
from apps.analytics.services.services import AnalyticsService
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from groq import Groq
from django.conf import settings
from .models import Question



class QuestionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        questions = Question.objects.all()

        exam_type = request.query_params.get('exam_type')
        subject = request.query_params.get('subject')
        difficulty = request.query_params.get('difficulty')
        topic = request.query_params.get('topic')

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

    def get(self, request, pk):
        try:
            mock_test = MockTest.objects.get(pk=pk, user=request.user)

            attempt = TestAttempt.objects.filter(
                mock_test=mock_test,
                user=request.user,
                submitted_at__isnull=True
            ).first()
            # 🔥 Ensure attempt ALWAYS exists
            if not attempt:
                attempt = TestAttempt.objects.create(
                    user=request.user,
                    mock_test=mock_test,
                    total_marks=mock_test.total_marks
                )

            # ✅ FIX 1: start timer once
            if not mock_test.started_at:
                mock_test.started_at = timezone.now()
                mock_test.save(update_fields=["started_at"])

            # ✅ FIX 2: timer calculation
            now = timezone.now()
            total_seconds = mock_test.duration_minutes * 60

            # ✅ FIX: handle not started case
            if not mock_test.started_at:
                remaining_seconds = total_seconds
            else:
                elapsed = (now - mock_test.started_at).total_seconds()
                remaining_seconds = max(0, int(total_seconds - elapsed))
            questions_data = []

            for idx, q in enumerate(mock_test.questions.all(), start=1):

                options_list = [
                    {"key": key, "text": value}
                    for key, value in q.options.items()
                ]

                selected_answer = None

                if attempt:
                    ans = attempt.answers.filter(question=q).first()
                    if ans:
                        selected_answer = ans.user_answer

                questions_data.append({
                    "id": q.id,
                    "question_text": q.question_text,
                    "options": options_list,
                    "selected_option": selected_answer,
                    "is_answered": selected_answer is not None,
                    "question_number": idx,
                    "topic": q.topic.name if q.topic else None
                })

            return Response({
                "id": mock_test.id,
                "topics": list(
    mock_test.questions.values_list("topic__name", flat=True).distinct()
),
                "title": mock_test.title,
                "description": mock_test.description,
                "duration_minutes": mock_test.duration_minutes,
                "remaining_seconds": remaining_seconds,
                "total_marks": mock_test.total_marks,
                "question_count": mock_test.questions.count(),
                "attempt_id": attempt.id if attempt else None,
                "questions": questions_data,
                "answers": [
                    {
                        "question": ans.question.id,
                        "user_answer": ans.user_answer
                    }
                    for ans in attempt.answers.all()
                ] if attempt else []
            })

        except MockTest.DoesNotExist:
            return Response(
                {"error": "Mock test not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class StartTestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            mock_test = MockTest.objects.get(pk=pk, user=request.user)

            # ✅ Start only once
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

        attempt_id = serializer.validated_data['attempt_id']
        question_id = serializer.validated_data['question_id']
        user_answer = serializer.validated_data['user_answer']
        time_taken = serializer.validated_data.get('time_taken_seconds', 0)

        # ✅ FIX 4: pass user (CRITICAL)
        answer, attempt = MockTestService.submit_answer(
            user=request.user,
            attempt_id=attempt_id,
            question_id=question_id,
            user_answer=user_answer,
            time_taken_seconds=time_taken
        )

        if not answer or not attempt:
            return Response(
                {"error": "Invalid attempt or question"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if attempt.user != request.user:
            return Response(
                {"error": "Unauthorized"},
                status=status.HTTP_403_FORBIDDEN
            )

        if attempt.submitted_at:
            return Response(
                {"error": "Test already submitted"},
                status=status.HTTP_400_BAD_REQUEST
            )

        total_questions = attempt.mock_test.questions.count()

        # ✅ FIX 5: correct progress query
        answered = attempt.answers.exclude(user_answer__isnull=True).count()

        return Response({
            "question_id": question_id,
            "selected_option": answer.user_answer,
            "is_correct": answer.is_correct,
            "marks_obtained": answer.marks_obtained,
            "progress": {
                "answered": answered,
                "total": total_questions
            }
        })


class TestResultView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            attempts = TestAttempt.objects.filter(
                user=request.user,
                submitted_at__isnull=False
            ).select_related(
                "mock_test",
              
            ).order_by('-submitted_at')[:20]

            result_list = []

            for attempt in attempts:
                answers = attempt.answers.select_related("question__topic").all()

                topic_name = None
                subject = None

                first_answer = answers.first()

                if first_answer and first_answer.question.topic:
                    topic = first_answer.question.topic
                    topic_name = topic.name
                    subject = topic.parent.name if topic.parent else None

                result_list.append({
                    "attempt_id": attempt.id,
                    "mock_test_id": attempt.mock_test.id,
                    "title": (
                        f"{subject} - {topic_name}"
                        if topic_name
                        else attempt.mock_test.title
                    ),
                    "topic": topic_name,
                    "subject": subject,
                    "score": attempt.score,
                    "percentage": attempt.percentage,
                    "correct": attempt.correct_answers,
                    "incorrect": attempt.incorrect_answers,
                    "date": attempt.submitted_at
                })
            return Response(result_list)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def post(self, request):
        attempt_id = request.data.get('attempt_id')

        if not attempt_id:
            return Response(
                {'error': 'attempt_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        attempt = MockTestService.finalize_test(attempt_id)

        if not attempt or attempt.user != request.user:
            return Response(
                {'error': 'Test attempt not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # ✅ Analytics (keep)
        AnalyticsService.create_performance_snapshot(attempt)

        questions_result = []

        answers = attempt.answers.select_related('question')

        for ans in answers:
            q = ans.question

            questions_result.append({
                "question_id": q.id,
                "question_text": q.question_text,
                "your_answer": ans.user_answer,
                "correct_answer": q.correct_answer,
                "is_correct": ans.is_correct,
                "marks_obtained": ans.marks_obtained,
                "explanation": q.explanation
            })

        return Response({
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
            "questions": questions_result
        })

class TestResultDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, attempt_id):
        try:
            attempt = TestAttempt.objects.get(
                id=attempt_id,
                user=request.user
            )

            answers = attempt.answers.select_related('question')
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
                    "explanation": q.explanation
                })

            return Response({
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
                "questions": questions
            })

        except TestAttempt.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

class GenerateMockTestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        topic_id = request.data.get("topic_id")  # optional now
        roadmap_id = request.data.get("roadmap_id")
        day = request.data.get("day")
        num_questions = request.data.get("num_questions", 10)

        if not roadmap_id or day is None:
            return Response(
                {"error": "roadmap_id and day are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            roadmap = Roadmap.objects.get(id=roadmap_id)

            day_topics_qs = Topic.objects.filter(
                roadmap_entries__roadmap=roadmap,
                roadmap_entries__day_number=day
            ).distinct()

            if not day_topics_qs.exists():
                return Response(
                    {"error": "No topics found for this day"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            data = MockTestService.create_mock_test(
                user=request.user,
                roadmap=roadmap,
                day=day,
                topics=list(day_topics_qs),
                num_questions=num_questions
            )

            return Response({
                "mock_test": MockTestDetailSerializer(data["mock_test"]).data,
                "attempt": TestAttemptSerializer(data["attempt"]).data
            })

        except Roadmap.DoesNotExist:
            return Response(
                {"error": "Invalid roadmap_id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            print("MOCK TEST ERROR:", str(e))
            return Response(
                {"error": f"Failed to generate test: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ExplainQuestionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        question_id = request.data.get("question_id")

        try:
            question = Question.objects.get(id=question_id)

            client = Groq(api_key=settings.GROQ_API_KEY)

            prompt = f"""

Explain this MCQ in a structured bullet format.

Question:
{question.question_text}

Options:
{question.options}

Correct Answer:
{question.correct_answer}

Rules:
- Use ONLY plain text (NO **, NO markdown, NO symbols)
- DO NOT write paragraphs
- Use bullet points with "-"
- Each line must be short (1 sentence)
- Keep explanation medium length (6–10 lines total)

Format EXACTLY like this:

Correct:
- <why correct in 1 line>
- <extra reasoning if needed>

Wrong Options:
- A: <why wrong>
- B: <why wrong>
- C: <why wrong>
- D: <why wrong>

Key Concept:
- <main idea>
- <important takeaway>


"""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )

            explanation = response.choices[0].message.content.strip()
            explanation = "\n".join([line for line in explanation.split("\n") if line.strip()])
            return Response({
                "explanation": explanation
            })

        except Question.DoesNotExist:
            return Response({"error": "Invalid question"}, status=400)

        except Exception as e:
            return Response({"error": str(e)}, status=500)