from django.db import models
from django.conf import settings


class Question(models.Model):
    """Question bank for mock tests"""
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    QUESTION_TYPE_CHOICES = [
        ('mcq', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
    ]
    
    subject = models.CharField(max_length=200)
    topic = models.CharField(max_length=200)
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default='mcq'
    )
    exam = models.ForeignKey(
    "roadmap.Exam",
    on_delete=models.CASCADE,
    null=True,
    blank=True
    )
    topic_fk = models.ForeignKey(
        "roadmap.RoadmapTopic",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="questions"
    )
    topic_obj = models.ForeignKey(
        "roadmap.Topic",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="questions"
    )
    
    # For MCQ
    option_a = models.CharField(max_length=500, blank=True)
    option_b = models.CharField(max_length=500, blank=True)
    option_c = models.CharField(max_length=500, blank=True)
    option_d = models.CharField(max_length=500, blank=True)
    
    correct_answer = models.CharField(max_length=500)
    explanation = models.TextField()
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default='medium',
        db_index=True
    )
    
    marks = models.PositiveIntegerField(default=1)
    negative_marks = models.FloatField(default=0.0)
    
    # Metadata
    exam_type = models.CharField(max_length=100,db_index=True)  # e.g., UPSC, NEET, JEE
    tags = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'questions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subject', 'topic']),
            models.Index(fields=['exam_type', 'difficulty']),
        ]
    
    def __str__(self):
        return f"{self.subject} - {self.topic} ({self.difficulty})"


class MockTest(models.Model):
    """Mock test instance"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mock_tests'
    )
    roadmap = models.ForeignKey(
        "roadmap.Roadmap",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="mock_tests"
    )   
    generation_reason = models.CharField(
        max_length=50,
        default="adaptive"
    )
    generation_topics = models.JSONField(default=list, blank=True)

    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    exam_type = models.CharField(max_length=100,db_index=True)  # e.g., UPSC, NEET, JEE
    
    questions = models.ManyToManyField(Question, related_name='mock_tests')
    total_marks = models.IntegerField(default=0)
    duration_minutes = models.IntegerField(default=60)
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True
    )
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'mock_tests'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user}"


class TestAttempt(models.Model):
    """User's attempt at a mock test"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='test_attempts',
        db_index=True
    )
    mock_test = models.ForeignKey(
        MockTest,
        on_delete=models.CASCADE,
        related_name='attempts',
        db_index=True
    )
    
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    time_taken_minutes = models.IntegerField(default=0)
    
    score = models.FloatField(default=0.0)
    total_marks = models.IntegerField(default=0)
    percentage = models.FloatField(default=0.0)
    
    # Analytics
    correct_answers = models.IntegerField(default=0)
    incorrect_answers = models.IntegerField(default=0)
    unanswered = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'test_attempts'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.mock_test.title} - {self.user.email} - {self.percentage}%"


class Answer(models.Model):
    """Individual answers in a test attempt"""
    
    attempt = models.ForeignKey(
        TestAttempt,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )
    
    
    user_answer = models.CharField(max_length=500, blank=True)
    is_correct = models.BooleanField(default=False)
    marks_obtained = models.FloatField(default=0.0)
    time_taken_seconds = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'answers'
        indexes = [
          models.Index(fields=['attempt']),
        ]

        unique_together = ['attempt', 'question']
    
    def __str__(self):
        return f"Q{self.question.id} - {'Correct' if self.is_correct else 'Incorrect'}"
