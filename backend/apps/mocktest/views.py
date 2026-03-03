from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Question, MockTest, TestAttempt
from .serializers import (
    QuestionSerializer,
    MockTestSerializer,
    MockTestDetailSerializer,
    TestAttemptSerializer,
    SubmitAnswerSerializer,
    GeneratePracticeSerializer
)
from .services import MockTestService
from apps.analytics.services import AnalyticsService

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

            mock_test = MockTest.objects.get(
                pk=pk,
                user=request.user
            )

            # Find active attempt
            attempt = TestAttempt.objects.filter(
                mock_test=mock_test,
                user=request.user,
                submitted_at__isnull=True
            ).first()

            serializer = MockTestDetailSerializer(mock_test)

            answers = []

            if attempt:
                answers = attempt.answers.values(
                    "question",
                    "user_answer"
                )

            return Response({
                **serializer.data,
                "attempt_id": attempt.id if attempt else None,
                "answers": list(answers)
            })

        except MockTest.DoesNotExist:

            return Response(
                {"error": "Mock test not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class SubmitAnswerView(APIView):
    """Submit an answer for a question"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = SubmitAnswerSerializer(data=request.data)
        if serializer.is_valid():
            answer = MockTestService.submit_answer(
                attempt_id=serializer.validated_data['attempt_id'],
                question_id=serializer.validated_data['question_id'],
                user_answer=serializer.validated_data['user_answer'],
                time_taken_seconds=serializer.validated_data.get('time_taken_seconds', 0)
            )
            
            if answer:
                return Response({
                    'message': 'Answer submitted successfully',
                    'is_correct': answer.is_correct,
                    'marks_obtained': answer.marks_obtained
                })
            
            return Response(
                {'error': 'Failed to submit answer'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TestResultView(APIView):
    """Get test results and finalize test"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Finalize and get test results"""
        attempt_id = request.data.get('attempt_id')
        
        if not attempt_id:
            return Response(
                {'error': 'attempt_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        attempt = MockTestService.finalize_test(attempt_id)
        
        if attempt and attempt.user == request.user:

            # AUTOMATIC ANALYTICS PIPELINE
            AnalyticsService.create_performance_snapshot(attempt)

            serializer = TestAttemptSerializer(attempt)
            return Response(serializer.data)
        return Response(
            {'error': 'Test attempt not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    def get(self, request):
        """Get all test results for user"""
        attempts = TestAttempt.objects.filter(
            user=request.user,
            submitted_at__isnull=False
        ).order_by('-submitted_at')[:20]
        
        serializer = TestAttemptSerializer(attempts, many=True)
        return Response(serializer.data)


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
