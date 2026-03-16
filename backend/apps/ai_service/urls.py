from django.urls import path
from .views import AskAIView, ChunkDocumentAPIView, DocumentUploadAPIView, GenerateQuestionsView,HealthCheckView, ScrapeDocumentAPIView, CleanDocumentAPIView, EmbedDocumentAPIView, SemanticSearchAPIView

app_name = 'ai_service'

urlpatterns = [
    path('ask-ai/', AskAIView.as_view(), name='ask-ai'),
    path('generate-questions/', GenerateQuestionsView.as_view(), name='generate-questions'),
    path("health/", HealthCheckView.as_view()),
    path("documents/upload/", DocumentUploadAPIView.as_view(), name="document-upload"),
    path("documents/scrape/", ScrapeDocumentAPIView.as_view(), name="document-scrape"),
path("documents/clean/", CleanDocumentAPIView.as_view(), name="clean-document"),
path("documents/chunk/", ChunkDocumentAPIView.as_view(), name="chunk-document"),
path("documents/embed/", EmbedDocumentAPIView.as_view(), name="embed-document"),
path("documents/search/", SemanticSearchAPIView.as_view(), name="semantic-search"),

]
