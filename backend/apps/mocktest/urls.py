from django.urls import path
from .views import (
    QuestionListView, 
    MockTestCreateView, 
    MockTestDetailView,
    SubmitAnswerView,
    TestResultView,
    GeneratePracticeView
)

app_name = 'mocktest'

urlpatterns = [
    path('questions/', QuestionListView.as_view(), name='questions'),
    path('mocktest/', MockTestCreateView.as_view(), name='create-test'),
    path('mocktest/<int:pk>/', MockTestDetailView.as_view(), name='test-detail'),
    path('submit-answer/', SubmitAnswerView.as_view(), name='submit-answer'),
    path('results/', TestResultView.as_view(), name='results'),
    path('generate-practice/', GeneratePracticeView.as_view(), name='generate-practice'),
]
