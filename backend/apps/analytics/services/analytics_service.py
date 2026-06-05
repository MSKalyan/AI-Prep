from .user_analytics_service import UserAnalyticsService
from .metrics_service import MetricsService

class AnalyticsService:
    get_user_analytics = UserAnalyticsService.get_user_analytics
    get_weak_subject = UserAnalyticsService.get_weak_subject
    update_performance_metrics = MetricsService.update_performance_metrics
    update_weak_areas = MetricsService.update_weak_areas
    update_daily_progress = MetricsService.update_daily_progress
    rebuild_performance_metrics = MetricsService.rebuild_performance_metrics
    create_performance_snapshot = MetricsService.create_performance_snapshot

__all__ = ["AnalyticsService", "UserAnalyticsService", "MetricsService"]