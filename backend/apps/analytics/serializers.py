from rest_framework import serializers
from .models import StudySession, PerformanceMetrics, WeakArea, DailyProgress


class StudySessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudySession
        fields = ('id', 'activity_type', 'subject', 'topic', 'duration_minutes',
                  'questions_attempted', 'questions_correct', 'started_at', 'ended_at')
        read_only_fields = ('id', 'started_at')


class PerformanceMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceMetrics
        fields = ('id', 'subject', 'total_attempts', 'total_questions',
                  'correct_answers', 'incorrect_answers', 'accuracy_percentage',
                  'average_score', 'total_time_minutes', 'average_time_per_question',
                  'easy_accuracy', 'medium_accuracy', 'hard_accuracy',
                  'improvement_rate', 'consistency_score', 'last_activity', 'updated_at')


class WeakAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeakArea
        fields = ('id', 'subject', 'topic', 'attempts', 'correct', 'accuracy',
                  'priority', 'is_improving', 'created_at', 'updated_at')


class DailyProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyProgress
        fields = ('id', 'date', 'study_time_minutes', 'questions_attempted',
                  'questions_correct', 'mock_tests_taken', 'ai_queries',
                  'topics_covered', 'streak_days', 'goals_met', 'created_at')


class AnalyticsSummarySerializer(serializers.Serializer):
    """Combined analytics data"""
    overall_stats = serializers.DictField()
    subject_performance = PerformanceMetricsSerializer(many=True)
    weak_areas = WeakAreaSerializer(many=True)
    recent_progress = DailyProgressSerializer(many=True)
    study_streak = serializers.IntegerField()
    total_study_time = serializers.IntegerField()
