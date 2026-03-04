from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import (
    AskAISerializer,
    GenerateQuestionsAISerializer,
    ConversationSerializer,
    MessageSerializer
)
from .services.services import AIService
from .models import Conversation


class AskAIView(APIView):
    """
    POST /api/ask-ai/
    Ask AI a question and get answer using RAG
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = AskAISerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                ai_service = AIService()
                
                result = ai_service.ask_ai(
                    user=request.user,
                    question=serializer.validated_data['question'],
                    context=serializer.validated_data.get('context', ''),
                    conversation_id=serializer.validated_data.get('conversation_id'),
                    exam_type=serializer.validated_data.get('exam_type', '')
                )
                
                return Response(result, status=status.HTTP_200_OK)
            
            except Conversation.DoesNotExist:
                return Response(
                    {'error': 'Conversation not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            except Exception as e:
                return Response(
                    {'error': f'AI service error: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        """Get user's conversations"""
        conversations = Conversation.objects.filter(user=request.user)[:20]
        serializer = ConversationSerializer(conversations, many=True)
        return Response(serializer.data)


class GenerateQuestionsView(APIView):
    """
    POST /api/generate-questions/
    Generate questions using AI
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = GenerateQuestionsAISerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                ai_service = AIService()
                
                questions = ai_service.generate_questions(
                    exam_type=serializer.validated_data['exam_type'],
                    subject=serializer.validated_data['subject'],
                    topic=serializer.validated_data.get('topic', ''),
                    difficulty=serializer.validated_data['difficulty'],
                    num_questions=serializer.validated_data['num_questions'],
                    question_type=serializer.validated_data['question_type']
                )
                
                if questions:
                    return Response({
                        'questions': questions,
                        'count': len(questions),
                        'message': 'Questions generated successfully'
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response(
                        {'error': 'Failed to generate questions'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            
            except Exception as e:
                return Response(
                    {'error': f'Question generation error: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response({"status": "ok"})
