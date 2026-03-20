from django.db import models
from django.conf import settings


class Question(models.Model):
    """Unified Question Bank (PYQ + LLM)"""

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

    SOURCE_CHOICES = [
        ('pyq', 'PYQ'),
        ('llm', 'LLM'),
    ]

    # Core relations
    topic = models.ForeignKey(
        "roadmap.Topic",
        on_delete=models.CASCADE,
        related_name="questions"
    )

    exam = models.ForeignKey(
        "roadmap.Exam",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # Question content
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default='mcq'
    )

    # Flexible options (for MCQ)
    options = models.JSONField(null=True, blank=True)

    correct_answer = models.CharField(max_length=255)
    explanation = models.TextField(blank=True)

    # Metadata
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default='medium',
        db_index=True
    )

    marks = models.PositiveIntegerField(default=1)
    negative_marks = models.FloatField(default=0.0)

    source = models.CharField(
        max_length=10,
        choices=SOURCE_CHOICES,
        db_index=True
    )

    year = models.IntegerField(null=True, blank=True)  # For PYQs
    tags = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'questions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['topic']),
            models.Index(fields=['source']),
            models.Index(fields=['difficulty']),
        ]

    def __str__(self):
        return f"{self.topic} ({self.source}) - {self.difficulty}"


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
        default="topic_practice"
    )

    generation_topics = models.JSONField(default=list, blank=True)

    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)

    exam = models.ForeignKey(
        "roadmap.Exam",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    questions = models.ManyToManyField(Question, related_name='mock_tests')

    total_marks = models.IntegerField(default=0)
    question_count = models.IntegerField(default=0)
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

    correct_answers = models.IntegerField(default=0)
    incorrect_answers = models.IntegerField(default=0)
    unanswered = models.IntegerField(default=0)

    class Meta:
        db_table = 'test_attempts'
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.mock_test.title} - {self.user} - {self.percentage}%"


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