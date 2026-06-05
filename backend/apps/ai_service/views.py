import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from .utils.ai_utils import (
    ask_ai,
    get_conversations,
    get_conversation_messages,
    upload_document,
    process_document,
)

logger = logging.getLogger(__name__)


class AskAIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        result, error, status_code = ask_ai(request)
        if error:
            return Response(error, status=status_code)
        return Response(result, status=status.HTTP_200_OK)

    def get(self, request) -> Response:
        data, _, _ = get_conversations(request.user)
        return Response(data)


class ConversationMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id) -> Response:
        result, error, status_code = get_conversation_messages(request, conversation_id)
        if error:
            return Response(error, status=status_code)
        return Response(result)


class DocumentUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request) -> Response:
        result, error, status_code = upload_document(request)
        if error:
            return Response(error, status=status_code)
        return Response(result, status=status.HTTP_201_CREATED)


class ProcessDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        result, error, status_code = process_document(request)
        if error:
            return Response(error, status=status_code)
        return Response(result, status=status.HTTP_200_OK)
