from django.urls import path
from .views import UserAnalyticsView, PerformanceStatsView

app_name = 'analytics'

urlpatterns = [
    path('analytics/', UserAnalyticsView.as_view(), name='user-analytics'),
    path('analytics/stats/', PerformanceStatsView.as_view(), name='performance-stats'),
]
