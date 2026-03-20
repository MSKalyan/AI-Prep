from rest_framework import serializers
from .models import Question, MockTest, TestAttempt, Answer


# -------------------- QUESTION --------------------

class QuestionSerializer(serializers.ModelSerializer):
    topic=serializers.CharField(source='topic.name', read_only=True)
    class Meta:
        model = Question
        fields = (
            'id',
            'topic',
            'question_text',
            'question_type',
            'options',
            'difficulty',
            'marks',
            'negative_marks',
            'tags'
        )
        # correct_answer & explanation intentionally excluded

class MockTestQuestionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    question_text = serializers.CharField()
    options = serializers.ListField()
    selected_option = serializers.CharField(allow_null=True)
    is_answered = serializers.BooleanField()
class QuestionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'


# -------------------- MOCK TEST --------------------

class MockTestSerializer(serializers.ModelSerializer):
    questions_count = serializers.SerializerMethodField()

    class Meta:
        model = MockTest
        fields = (
            'id',
            'title',
            'description',
            'total_marks',
            'duration_minutes',
            'status',
            'questions_count',
            'started_at',
            'completed_at',
            'created_at'
        )
        read_only_fields = ('id', 'created_at')

    def get_questions_count(self, obj):
        return obj.questions.count()


class MockTestDetailSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = MockTest
        fields = (
            'id',
            'title',
            'description',
            'total_marks',
            'duration_minutes',
            'status',
            'questions',
            'started_at',
            'completed_at',
            'created_at',
            'updated_at',
            'question_count'
        )


# -------------------- ANSWERS --------------------

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = (
            'question',
            'user_answer',
            'is_correct',
            'marks_obtained',
            'time_taken_seconds'
        )
        read_only_fields = ('is_correct', 'marks_obtained')


# -------------------- TEST ATTEMPT --------------------

class TestAttemptSerializer(serializers.ModelSerializer):
    mock_test_title = serializers.CharField(source='mock_test.title', read_only=True)
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = TestAttempt
        fields = (
            'id',
            'mock_test',
            'mock_test_title',
            'started_at',
            'submitted_at',
            'time_taken_minutes',
            'score',
            'total_marks',
            'percentage',
            'correct_answers',
            'incorrect_answers',
            'unanswered',
            'answers'
        )
        read_only_fields = ('id', 'started_at', 'score', 'percentage')


# -------------------- INPUT SERIALIZERS --------------------

class SubmitAnswerSerializer(serializers.Serializer):
    attempt_id = serializers.IntegerField()
    question_id = serializers.IntegerField()
    user_answer = serializers.CharField(max_length=500)
    time_taken_seconds = serializers.IntegerField(default=0)


class TestResultDetailSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    question_text = serializers.CharField()
    your_answer = serializers.CharField(allow_null=True)
    correct_answer = serializers.CharField()
    is_correct = serializers.BooleanField()
    explanation = serializers.CharField()

class GeneratePracticeSerializer(serializers.Serializer):
    # legacy (AI-based) — keep for now
    exam_type = serializers.CharField(max_length=100)
    subject = serializers.CharField(max_length=200)
    topic = serializers.CharField(max_length=200, required=False, allow_blank=True)
    difficulty = serializers.ChoiceField(
        choices=['easy', 'medium', 'hard'],
        default='medium'
    )
    num_questions = serializers.IntegerField(min_value=1, max_value=50, default=10)