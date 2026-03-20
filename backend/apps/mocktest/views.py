from httpx import request
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Question, MockTest, TestAttempt
from apps.roadmap.models import Topic
from rest_framework.permissions import IsAuthenticated
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

class QuestionListView(APIView):
    """List and filter questions"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        questions = Question.objects.all()
        
        # Filters
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
            questions = questions.filter(topic__icontains=topic)
        
        serializer = QuestionSerializer(questions[:50], many=True)
        return Response(serializer.data)


class MockTestCreateView(APIView):
    """Create a new mock test"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        title = request.data.get('title', 'Mock Test')
        exam_type = request.data.get('exam_type')
        subject = request.data.get('subject')
        difficulty = request.data.get('difficulty', 'medium')
        num_questions = request.data.get('num_questions', 10)
        duration = request.data.get('duration_minutes', 60)
        
        if not exam_type or not subject:
            return Response(
                {'error': 'exam_type and subject are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            mock_test = MockTestService.create_mock_test(
                user=request.user,
                title=title,
                exam_type=exam_type,
                subject=subject,
                difficulty=difficulty,
                num_questions=num_questions,
                duration_minutes=duration
            )
            
            # Start attempt automatically
            attempt = MockTestService.start_test_attempt(
                user=request.user,
                mock_test_id=mock_test.id
            )
            
            return Response({
                'mock_test': MockTestDetailSerializer(mock_test).data,
                'attempt': TestAttemptSerializer(attempt).data
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': f'Failed to create mock test: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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

            questions_data = []

            for idx,q in enumerate(mock_test.questions.all(),start=1):

                # Convert options JSON → list
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
                "title": mock_test.title,
                "description": mock_test.description,
                "duration_minutes": mock_test.duration_minutes,
                "total_marks": mock_test.total_marks,
                "question_count": mock_test.questions.count(),
                "attempt_id": attempt.id if attempt else None,
                "questions": questions_data
            })

        except MockTest.DoesNotExist:
            return Response(
                {"error": "Mock test not found"},
                status=status.HTTP_404_NOT_FOUND
            )


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

        answer, attempt = MockTestService.submit_answer(
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

        # Ownership check
        if attempt.user != request.user:
            return Response(
                {"error": "Unauthorized"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Prevent answering after submission
        if attempt.submitted_at:
            return Response(
                {"error": "Test already submitted"},
                status=status.HTTP_400_BAD_REQUEST
            )

        total_questions = attempt.mock_test.questions.count()
        answered = attempt.answers.exclude(user_answer='').count()

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
    """Finalize test and return detailed results"""
    permission_classes = [IsAuthenticated]

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

        # ✅ Analytics pipeline (keep this)
        AnalyticsService.create_performance_snapshot(attempt)

        # ✅ Build detailed question-wise result
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

        # ✅ Final response
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

    def get(self, request):
        """Get all completed test results for user"""
        attempts = TestAttempt.objects.filter(
            user=request.user,
            submitted_at__isnull=False
        ).order_by('-submitted_at')[:20]

        result_list = []

        for attempt in attempts:
            result_list.append({
                "attempt_id": attempt.id,
                "mock_test_id": attempt.mock_test.id,
                "title": attempt.mock_test.title,
                "score": attempt.score,
                "percentage": attempt.percentage,
                "correct": attempt.correct_answers,
                "incorrect": attempt.incorrect_answers,
                "date": attempt.submitted_at
            })

        return Response(result_list)
class GeneratePracticeView(APIView):
    """Generate practice questions using AI"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = GeneratePracticeSerializer(data=request.data)
        if serializer.is_valid():
            try:
                questions = MockTestService.generate_ai_questions(
                    exam_type=serializer.validated_data['exam_type'],
                    subject=serializer.validated_data['subject'],
                    topic=serializer.validated_data.get('topic', ''),
                    difficulty=serializer.validated_data['difficulty'],
                    num_questions=serializer.validated_data['num_questions']
                )
                
                if questions:
                    return Response({
                        'message': f'Generated {len(questions)} questions',
                        'questions': QuestionSerializer(questions, many=True).data
                    }, status=status.HTTP_201_CREATED)
                
                return Response(
                    {'error': 'Failed to generate questions'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            except Exception as e:
                return Response(
                    {'error': f'Error generating questions: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GenerateMockTestView(APIView):
    """
    Generate mock test using PYQs (new system)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        topic_id = request.data.get("topic_id")
        num_questions = request.data.get("num_questions", 5)

        if not topic_id:
            return Response(
                {"error": "topic_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            topic = Topic.objects.get(id=topic_id)

            mock_test = MockTestService.create_mock_test(
                user=request.user,
                topic=topic,
                num_questions=num_questions
            )

            # auto start attempt (same pattern as old flow)
            attempt = MockTestService.start_test_attempt(
                user=request.user,
                mock_test_id=mock_test.id
            )

            return Response({
                "mock_test": MockTestDetailSerializer(mock_test).data,
                "attempt": TestAttemptSerializer(attempt).data
            }, status=status.HTTP_201_CREATED)

        except Topic.DoesNotExist:
            return Response(
                {"error": "Invalid topic_id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {"error": f"Failed to generate test: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )