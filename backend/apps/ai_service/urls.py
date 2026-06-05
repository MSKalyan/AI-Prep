from django.urls import path
from .views import (
    AskAIView,
    ConversationMessagesView,
    DocumentUploadView,
    ProcessDocumentView,
)

app_name = "ai_service"

urlpatterns = [
    path("ask-ai/", AskAIView.as_view(), name="ask-ai"),
    path("conversations/<int:conversation_id>/messages/",ConversationMessagesView.as_view(),name="get-messages"),
    path("documents/", DocumentUploadView.as_view()),
    path("documents/process/", ProcessDocumentView.as_view(), name="process-document"),
]
