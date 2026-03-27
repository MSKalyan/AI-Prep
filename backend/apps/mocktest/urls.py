from django.urls import path
from .views import (
    ExplainQuestionView,
    QuestionListView, 
    # MockTestCreateView, 
    MockTestDetailView,
    StartTestView,
    SubmitAnswerView,
    TestResultDetailView,
    TestResultView,
    # GeneratePracticeView,
    GenerateMockTestView
)

app_name = 'mocktest'

urlpatterns = [
    path('questions/', QuestionListView.as_view(), name='questions'),
    # path('mocktest/', .as_view(), name='create-test'),
    
path('mocktest/start/<int:pk>/', StartTestView.as_view(), name='start-test'),
    path('mocktest/<int:pk>/', MockTestDetailView.as_view(), name='test-detail'),
    path('mocktest/submit-answer/', SubmitAnswerView.as_view(), name='submit-answer'),
    path('mocktest/results/', TestResultView.as_view(), name='results'),
    path("mocktest/results/<int:attempt_id>/", TestResultDetailView.as_view()),
    # path('generate-practice/', GeneratePracticeView.as_view(), name='generate-practice'),
    path('mocktest/generate/', GenerateMockTestView.as_view(), name='generate-mock-test'),
    path('mocktest/explain/',ExplainQuestionView.as_view()),
]
