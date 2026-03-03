from django.urls import path
from .views import  ExamListView, RoadmapGenerateView, RoadmapJobStatusView, RoadmapListView, RoadmapDetailView, DeterministicRoadmapGenerateView

app_name = 'roadmap'

urlpatterns = [
    path("exams/", ExamListView.as_view(), name="exam_list"),
    path("roadmap/generate/", DeterministicRoadmapGenerateView.as_view()),
    path('roadmap/generate/', RoadmapGenerateView.as_view(), name='generate'),
    path('roadmap/job/<int:job_id>/', RoadmapJobStatusView.as_view(), name='job_status'),
    path('roadmaps/', RoadmapListView.as_view(), name='list'),
    path('roadmap/<int:pk>/', RoadmapDetailView.as_view(), name='detail'),
]
