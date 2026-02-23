from django.contrib import admin
from .models import Question, MockTest, TestAttempt, Answer


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('subject', 'topic', 'question_type', 'difficulty', 'exam_type', 'marks')
    list_filter = ('question_type', 'difficulty', 'exam_type', 'subject')
    search_fields = ('question_text', 'subject', 'topic')
    list_per_page = 50


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    fields = ('question', 'user_answer', 'is_correct', 'marks_obtained')
    readonly_fields = ('is_correct', 'marks_obtained')


@admin.register(MockTest)
class MockTestAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'exam_type', 'total_marks', 'status', 'created_at')
    list_filter = ('status', 'exam_type', 'created_at')
    search_fields = ('title', 'user__email')
    filter_horizontal = ('questions',)


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ('mock_test', 'user', 'score', 'percentage', 'started_at', 'submitted_at')
    list_filter = ('submitted_at', 'started_at')
    search_fields = ('user__email', 'mock_test__title')
    inlines = [AnswerInline]
    readonly_fields = ( 'correct_answers', 'incorrect_answers')


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'is_correct', 'marks_obtained')
    list_filter = ('is_correct',)
    search_fields = ('attempt__user__email', 'question__question_text')
