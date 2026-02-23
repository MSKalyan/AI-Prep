from django.contrib import admin
from .models import StudySession, PerformanceMetrics, WeakArea, DailyProgress,PerformanceSnapshot   


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'subject', 'duration_minutes',
                   'questions_attempted', 'questions_correct', 'started_at')
    list_filter = ('activity_type', 'started_at')
    search_fields = ('user__email', 'subject', 'topic')
    date_hierarchy = 'started_at'


@admin.register(PerformanceMetrics)
class PerformanceMetricsAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'accuracy_percentage', 'total_attempts',
                   'average_score', 'improvement_rate', 'last_activity')
    list_filter = ('subject', 'last_activity')
    search_fields = ('user__email', 'subject')
    readonly_fields = ( 'average_score', 'updated_at')


@admin.register(WeakArea)
class WeakAreaAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'topic', 'accuracy', 'priority',
                   'is_improving', 'attempts')
    list_filter = ('priority', 'is_improving', 'subject')
    search_fields = ('user__email', 'subject', 'topic')
    ordering = ['priority', '-accuracy']


@admin.register(DailyProgress)
class DailyProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'study_time_minutes', 'questions_attempted',
                   'mock_tests_taken', 'streak_days', 'goals_met')
    list_filter = ('date', 'goals_met')
    search_fields = ('user__email',)
    date_hierarchy = 'date'
    readonly_fields = ('streak_days',)


admin.site.register(PerformanceSnapshot)


class StudySessionInline(admin.TabularInline):
    model = StudySession
    extra = 0


class PerformanceSnapshotInline(admin.TabularInline):
    model = PerformanceSnapshot
    extra = 0


class WeakAreaInline(admin.TabularInline):
    model = WeakArea
    extra = 0


class DailyProgressInline(admin.TabularInline):
    model = DailyProgress
    extra = 0

class PerformanceMetricsInline(admin.TabularInline):
    model = PerformanceMetrics
    extra = 0