from django.urls import path
from .views import (
    ExamListView,
    RoadmapListView,
    RoadmapDetailView,
    DeterministicRoadmapGenerateView,
    RoadmapTopicsView,
    TopicStudyView,
    WeekPlanView,
    TopicCompleteView,
    WeekProgressView,
    RoadmapProgressView,
    ActivateRoadmapView
)

app_name = "roadmap"

urlpatterns = [
    path("exams/", ExamListView.as_view(), name="exam_list"),
    path("generate/",DeterministicRoadmapGenerateView.as_view(),name="generate"),
    path("roadmaps/",RoadmapListView.as_view(),name="list"),
    path("<int:pk>/",RoadmapDetailView.as_view(),name="detail"),
    path("<int:roadmap_id>/week/<int:week_number>/",WeekPlanView.as_view(),name="week_plan"),
    path("topic/<int:topic_id>/complete/",TopicCompleteView.as_view(),name="topic_complete"),
    path("<int:roadmap_id>/week/<int:week_number>/progress/",WeekProgressView.as_view(),name="week_progress"),
    path("<int:roadmap_id>/progress/",RoadmapProgressView.as_view(),name="roadmap_progress"),
    path("topics/<int:topic_id>/study/", TopicStudyView.as_view(), name="topic_study"),
    path("<int:roadmap_id>/topics/",RoadmapTopicsView.as_view(),name="roadmap_topics"),
    path("activate/<int:roadmap_id>/",ActivateRoadmapView.as_view(),name="activate-roadmap"),
]