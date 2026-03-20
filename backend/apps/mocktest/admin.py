from django.contrib import admin
from .models import Question, MockTest, TestAttempt, Answer


# -----------------------------
# Question Admin
# -----------------------------
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'topic',
        'source',
        'question_type',
        'difficulty',
        'year',
        'marks',
        'created_at'
    )

    list_filter = (
        'source',
        'question_type',
        'difficulty',
        'exam',
        'year'
    )

    search_fields = (
        'question_text',
        'topic__name'
    )

    list_per_page = 50


# -----------------------------
# Answer Inline (inside attempts)
# -----------------------------
class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0

    fields = (
        'question',
        'user_answer',
        'is_correct',
        'marks_obtained'
    )

    readonly_fields = (
        'is_correct',
        'marks_obtained'
    )


# -----------------------------
# Mock Test Admin
# -----------------------------
@admin.register(MockTest)
class MockTestAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'user',
        'exam',
        'question_count',
        'total_marks',
        'status',
        'created_at'
    )

    list_filter = (
        'status',
        'exam',
        'created_at'
    )

    search_fields = (
        'title',
        'user__email'
    )

    filter_horizontal = ('questions',)


# -----------------------------
# Test Attempt Admin
# -----------------------------
@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = (
        'mock_test',
        'user',
        'score',
        'percentage',
        'started_at',
        'submitted_at'
    )

    list_filter = (
        'submitted_at',
        'started_at'
    )

    search_fields = (
        'user__email',
        'mock_test__title'
    )

    inlines = [AnswerInline]

    readonly_fields = (
        'correct_answers',
        'incorrect_answers',
        'unanswered',
        'score',
        'percentage'
    )


# -----------------------------
# Answer Admin
# -----------------------------
@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = (
        'attempt',
        'question',
        'is_correct',
        'marks_obtained'
    )

    list_filter = (
        'is_correct',
    )

    search_fields = (
        'attempt__user__email',
        'question__question_text'
    )