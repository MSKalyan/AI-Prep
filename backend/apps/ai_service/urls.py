from django.urls import path
from .views import AskAIView, GenerateQuestionsView,HealthCheckView

app_name = 'ai_service'

urlpatterns = [
    path('ask-ai/', AskAIView.as_view(), name='ask-ai'),
    path('generate-questions/', GenerateQuestionsView.as_view(), name='generate-questions'),
    path("health/", HealthCheckView.as_view()),

]
