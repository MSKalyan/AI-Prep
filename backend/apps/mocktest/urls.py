from django.urls import path
from .views import (
    ExplainQuestionView,
    MockTestDetailView,
    StartTestView,
    SubmitAnswerView,
    TestResultDetailView,
    TestResultView,
    GenerateMockTestView
)

app_name = 'mocktest'

urlpatterns = [
    path('generate/', GenerateMockTestView.as_view(), name='generate-mock-test'),
    path('start/<int:pk>/', StartTestView.as_view(), name='start-test'),
    path('submit-answer/', SubmitAnswerView.as_view(), name='submit-answer'),
    path("results/<int:attempt_id>/", TestResultDetailView.as_view()),
    path('results/', TestResultView.as_view(), name='results'),
    path('<int:pk>/', MockTestDetailView.as_view(), name='test-detail'),
    path('explain/',ExplainQuestionView.as_view()),
]
