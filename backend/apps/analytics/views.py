from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    AnalyticsSummarySerializer,
    PerformanceMetricsSerializer,
    WeakAreaSerializer,
    DailyProgressSerializer,
    StudySessionSerializer
)
from .services.services import AnalyticsService
from .models import PerformanceMetrics, WeakArea, DailyProgress


class UserAnalyticsView(APIView):
    """
    GET /api/analytics/
    Get comprehensive analytics for authenticated user
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            analytics_data = AnalyticsService.get_user_analytics(request.user)
            
            # Serialize the data
            response_data = {
                'overall_stats': analytics_data['overall_stats'],
                'subject_performance': PerformanceMetricsSerializer(
                    analytics_data['subject_performance'], 
                    many=True
                ).data,
                'weak_areas': WeakAreaSerializer(
                    analytics_data['weak_areas'], 
                    many=True
                ).data,
                'recent_progress': DailyProgressSerializer(
                    analytics_data['recent_progress'], 
                    many=True
                ).data,
                'study_streak': analytics_data['study_streak'],
                'total_study_time': analytics_data['total_study_time']
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': f'Failed to fetch analytics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PerformanceStatsView(APIView):
    """
    GET /api/analytics/stats/
    Get detailed performance statistics
    
    Query params:
    - subject: Filter by subject
    - days: Number of days to include (default: 30)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        subject = request.query_params.get('subject')
        days = int(request.query_params.get('days', 30))
        
        try:
            # Performance metrics
            metrics = PerformanceMetrics.objects.filter(user=request.user)
            if subject:
                metrics = metrics.filter(subject=subject)
            
            # Weak areas
            weak_areas = WeakArea.objects.filter(user=request.user)
            if subject:
                weak_areas = weak_areas.filter(subject=subject)
            
            # Daily progress for the period
            from datetime import timedelta
            from django.utils import timezone
            
            start_date = timezone.now().date() - timedelta(days=days)
            daily_progress = DailyProgress.objects.filter(
                user=request.user,
                date__gte=start_date
            ).order_by('date')
            
            return Response({
                'performance_metrics': PerformanceMetricsSerializer(
                    metrics, 
                    many=True
                ).data,
                'weak_areas': WeakAreaSerializer(
                    weak_areas, 
                    many=True
                ).data,
                'daily_progress': DailyProgressSerializer(
                    daily_progress, 
                    many=True
                ).data,
                'period_days': days
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': f'Failed to fetch performance stats: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
