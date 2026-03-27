from django.urls import path

from apps.analytics.views_dashboard import DashboardView
from .views import  AdaptiveRoadmapView, AdaptiveStudyPlanView, StudyContentView, TopicAggregationView, TopicPerformanceView,UserAnalyticsView, PerformanceStatsView


app_name = 'analytics'

urlpatterns = [
    path('/', UserAnalyticsView.as_view(), name='user-analytics'),
    path('stats/', PerformanceStatsView.as_view(), name='performance-stats'),
    path("dashboard/",DashboardView.as_view(), name="dashboard"),
    path('aggregation/', TopicAggregationView.as_view(), name='topic-aggregation'),
    path('performance/', TopicPerformanceView.as_view(), name='topic-performance'),
    path('adaptive-roadmap/', AdaptiveRoadmapView.as_view(), name='adaptive-roadmap'),
    path('adaptive-study-plan/', AdaptiveStudyPlanView.as_view()),
    path("study-content/<int:topic_id>/", StudyContentView.as_view()),
]
