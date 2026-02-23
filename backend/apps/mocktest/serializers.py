from rest_framework import serializers
from .models import Question, MockTest, TestAttempt, Answer


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ('id', 'subject', 'topic', 'question_text', 'question_type',
                  'option_a', 'option_b', 'option_c', 'option_d',
                  'difficulty', 'marks', 'negative_marks', 'exam_type', 'tags')
        # Don't expose correct_answer and explanation in list view


class QuestionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'


class MockTestSerializer(serializers.ModelSerializer):
    questions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MockTest
        fields = ('id', 'title', 'description', 'exam_type', 'total_marks',
                  'duration_minutes', 'status', 'questions_count',
                  'started_at', 'completed_at', 'created_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_questions_count(self, obj):
        return obj.questions.count()


class MockTestDetailSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = MockTest
        fields = ('id', 'title', 'description', 'exam_type', 'total_marks',
                  'duration_minutes', 'status', 'questions',
                  'started_at', 'completed_at', 'created_at', 'updated_at')


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ('question', 'user_answer', 'is_correct', 'marks_obtained',
                  'time_taken_seconds')
        read_only_fields = ('is_correct', 'marks_obtained')


class TestAttemptSerializer(serializers.ModelSerializer):
    mock_test_title = serializers.CharField(source='mock_test.title', read_only=True)
    answers = AnswerSerializer(many=True, read_only=True)
    
    class Meta:
        model = TestAttempt
        fields = ('id', 'mock_test', 'mock_test_title', 'started_at', 
                  'submitted_at', 'time_taken_minutes', 'score', 'total_marks',
                  'percentage', 'correct_answers', 'incorrect_answers',
                  'unanswered', 'answers')
        read_only_fields = ('id', 'started_at', 'score', 'percentage')


class SubmitAnswerSerializer(serializers.Serializer):
    attempt_id = serializers.IntegerField()
    question_id = serializers.IntegerField()
    user_answer = serializers.CharField(max_length=500)
    time_taken_seconds = serializers.IntegerField(default=0)


class GeneratePracticeSerializer(serializers.Serializer):
    exam_type = serializers.CharField(max_length=100)
    subject = serializers.CharField(max_length=200)
    topic = serializers.CharField(max_length=200, required=False, allow_blank=True)
    difficulty = serializers.ChoiceField(
        choices=['easy', 'medium', 'hard'],
        default='medium'
    )
    num_questions = serializers.IntegerField(min_value=1, max_value=50, default=10)
