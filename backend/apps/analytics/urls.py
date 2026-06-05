from django.urls import path

from apps.analytics.views_dashboard import DashboardView
from .views import AdaptiveStudyPlanView, StudyContentView, TopicPerformanceView, UserAnalyticsView

app_name = 'analytics'

urlpatterns = [
    path('', UserAnalyticsView.as_view(), name='user-analytics'),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path('performance/', TopicPerformanceView.as_view(), name='topic-performance'),
    path('adaptive-study-plan/', AdaptiveStudyPlanView.as_view(), name='adaptive-study-plan'),
    path("study-content/", StudyContentView.as_view(), name="study-content"),
]