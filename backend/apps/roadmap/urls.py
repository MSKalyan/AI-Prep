from django.urls import path
from .views import (
    ExamListView,
    RoadmapJobStatusView,
    RoadmapListView,
    RoadmapDetailView,
    DeterministicRoadmapGenerateView,
    RoadmapTopicsView,
    TopicExplanationView,
    TopicStudyView,
    WeekPlanView,
    TopicCompleteView,
    WeekProgressView,
    RoadmapProgressView,
    ActivateRoadmapView
)

app_name = "roadmap"

urlpatterns = [

    # exam list
    path("exams/", ExamListView.as_view(), name="exam_list"),

    # generate roadmap
    path(
        "roadmap/generate/",
        DeterministicRoadmapGenerateView.as_view(),
        name="generate"
    ),

    # async job status
    path(
        "roadmap/job/<int:job_id>/",
        RoadmapJobStatusView.as_view(),
        name="job_status"
    ),

    # roadmap list
    path(
        "roadmaps/",
        RoadmapListView.as_view(),
        name="list"
    ),

    # roadmap detail
    path(
        "roadmap/<int:pk>/",
        RoadmapDetailView.as_view(),
        name="detail"
    ),

    # -------- NEW ENDPOINTS --------

    # week → day topics
    path(
        "roadmap/<int:roadmap_id>/week/<int:week_number>/",
        WeekPlanView.as_view(),
        name="week_plan"
    ),

    # mark topic completed
    path(
        "roadmap/topic/<int:topic_id>/complete/",
        TopicCompleteView.as_view(),
        name="topic_complete"
    ),

    # weekly progress
    path(
        "roadmap/<int:roadmap_id>/week/<int:week_number>/progress/",
        WeekProgressView.as_view(),
        name="week_progress"
    ),

    # overall roadmap progress
    path(
        "roadmap/<int:roadmap_id>/progress/",
        RoadmapProgressView.as_view(),
        name="roadmap_progress"
    ),
    path(
    "roadmap/topics/<int:topic_id>/explanation/",
    TopicExplanationView.as_view(),
),

  path("roadmap/topics/<int:topic_id>/study/", TopicStudyView.as_view(), name="topic_study"),
  
  path(
    "roadmap/<int:roadmap_id>/topics/",
    RoadmapTopicsView.as_view(),
    name="roadmap_topics"
),
    path(
        "roadmap/activate/<int:roadmap_id>/",
        ActivateRoadmapView.as_view(),
        name="activate-roadmap",
    ),
]