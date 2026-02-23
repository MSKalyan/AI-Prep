from django.contrib import admin
from .models import Exam, Roadmap, RoadmapTopic, RoadmapGenerationJob


class RoadmapTopicInline(admin.TabularInline):
    model = RoadmapTopic
    extra = 0
    fields = ('week_number', 'title', 'estimated_hours', 'priority', 'is_completed')


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'total_marks')
    search_fields = ('name', 'category')

@admin.register(RoadmapGenerationJob)
class RoadmapGenerationJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__email',)

@admin.register(Roadmap)
class RoadmapAdmin(admin.ModelAdmin):
    list_display = ('exam', 'user', 'target_date', 'difficulty_level', 'total_weeks', 'created_at')
    list_filter = ('difficulty_level', 'created_at')
    search_fields = ('exam__name', 'user__email')
    inlines = [RoadmapTopicInline]
    date_hierarchy = 'created_at'


@admin.register(RoadmapTopic)
class RoadmapTopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'roadmap', 'week_number', 'estimated_hours', 'is_completed')
    list_filter = ('is_completed', 'week_number')
    search_fields = ('title', 'description', 'roadmap__exam__name')
