import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import DocumentUploadSerializer

from apps.ai_service.rag.services.rag_service import RAGService
from .serializers import (
    AskAISerializer,
    GenerateQuestionsAISerializer,
    ConversationSerializer,
)
from .services.services import AIService
from .models import Conversation, Message, Document
from django.db import DatabaseError
from django.core.exceptions import ValidationError as DjangoValidationError

logger = logging.getLogger(__name__)

class AskAIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        serializer = AskAISerializer(data=request.data)

        if serializer.is_valid():
            try:
                ai_service = AIService()

                result = ai_service.ask_ai(
                    user=request.user,
                    question=serializer.validated_data["question"],
                    context=serializer.validated_data.get("context", ""),
                    conversation_id=serializer.validated_data.get("conversation_id"),
                    exam_type=serializer.validated_data.get("exam_type", ""),
                )

                return Response(result, status=status.HTTP_200_OK)

            except Conversation.DoesNotExist:
                return Response(
                    {"error": "Conversation not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            except (DatabaseError, ValueError, TypeError, KeyError, AttributeError, TimeoutError) as e:
                logger.error("Ask AI request failed", exc_info=True)
                return Response(
                    {"error": f"AI service error: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request) -> Response:
        conversations = Conversation.objects.filter(user=request.user)[:20]
        serializer = ConversationSerializer(conversations, many=True)
        return Response(serializer.data)


class ConversationMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id) -> Response:
        # Prevent IDOR by ensuring the conversation belongs to the user.
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            limit = int(request.query_params.get("limit", "10"))
        except (ValueError, TypeError):
            limit = 10

        limit = max(1, min(limit, 100))

        qs = (
            Message.objects.filter(conversation=conversation)
            .order_by("-created_at")
            .only("role", "content", "retrieved_documents", "created_at")
        )[:limit]

        messages = list(qs)[::-1]

        return Response(
            [
                {
                    "role": m.role,
                    "content": m.content,
                    "retrieved_documents": m.retrieved_documents,
                    "created_at": m.created_at,
                }
                for m in messages
            ]
        )


class GenerateQuestionsView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request) -> Response:
        serializer = GenerateQuestionsAISerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            questions = self._generate_questions(serializer.validated_data)
            return self._build_success_response(questions)

        except (DatabaseError, ValueError, TypeError, KeyError, AttributeError, TimeoutError) as e:
            return self._handle_error(e)
    def _generate_questions(self, data) -> list:
        ai_service = AIService()
        return ai_service.generate_questions(
            exam_type=data["exam_type"],
            subject=data["subject"],
            topic=data.get("topic", ""),
            difficulty=data["difficulty"],
            num_questions=data["num_questions"],
            question_type=data["question_type"],
        )
    def _build_success_response(self, questions) -> Response:
        if not questions:
            return Response(
                {"error": "Failed to generate questions"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "questions": questions,
                "count": len(questions),
                "message": "Questions generated successfully",
            },
            status=status.HTTP_201_CREATED,
        )
    def _handle_error(self, error) -> Response:
        logger.error("Question generation failed", exc_info=True)
        return Response(
            {"error": f"Question generation error: {str(error)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )



class DocumentUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request) -> Response:
        serializer = DocumentUploadSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            document = serializer.save()

            return Response(
                {
                    "id": document.id,
                    "title": document.title,
                    "processed": document.processed,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ProcessDocumentView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request) -> Response:
        document_id = request.data.get("document_id")
        if not document_id:
            return Response(
                {"error": "document_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            document = Document.objects.get(id=document_id, user=request.user)
            if document.processed:
                return Response(
                    {"message": "Document already processed"},
                    status=status.HTTP_200_OK,
                )
            rag = RAGService()
            rag.ingest_document(document)
            document.processed = True
            document.save()
            return Response(
                {"message": "Document processed successfully"},
                status=status.HTTP_200_OK,
            )
        except Document.DoesNotExist:
            return Response(
                {"error": "Document not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except (DatabaseError, DjangoValidationError, OSError, ValueError, TypeError) as e:
            logger.error("Document processing failed", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request) -> Response:
        return Response({"status": "ok"})
