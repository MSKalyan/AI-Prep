from django.db import models
from django.conf import settings


class StudySession(models.Model):
    """Track user study sessions"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='study_sessions'
    )
    
    activity_type = models.CharField(
        max_length=50,
        choices=[
            ('roadmap', 'Roadmap Study'),
            ('mock_test', 'Mock Test'),
            ('practice', 'Practice Questions'),
            ('ai_chat', 'AI Doubt Clearing'),
            ('revision', 'Revision'),
        ],
        db_index=True
    )
    
    subject = models.CharField(max_length=200, blank=True)
    topic = models.CharField(max_length=200, blank=True)
    
    duration_minutes = models.IntegerField(default=0)
    questions_attempted = models.IntegerField(default=0)
    questions_correct = models.IntegerField(default=0)
    
    started_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    @property
    def duration(self):
        if self.ended_at:
            delta = self.ended_at - self.started_at
            return delta.total_seconds() / 60
        return 0
    class Meta:
        db_table = 'study_sessions'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'started_at']),
            models.Index(fields=['activity_type']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.activity_type} - {self.duration_minutes}min"


class PerformanceMetrics(models.Model):
    """Aggregate performance metrics for users"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='performance_metrics'
    )
    
    subject = models.CharField(max_length=200,db_index=True)
    
    # Attempt statistics
    total_attempts = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    incorrect_answers = models.IntegerField(default=0)
    @property
    def calculated_accuracy(self):
        if self.total_questions == 0:
            return 0
        return (self.correct_answers / self.total_questions) * 100
    # Performance scores
    accuracy_percentage = models.FloatField(default=0.0)
    average_score = models.FloatField(default=0.0)
    
    # Time statistics
    total_time_minutes = models.IntegerField(default=0)
    average_time_per_question = models.FloatField(default=0.0)  # in seconds
    
    # Difficulty-wise breakdown
    easy_accuracy = models.FloatField(default=0.0)
    medium_accuracy = models.FloatField(default=0.0)
    hard_accuracy = models.FloatField(default=0.0)
    
    # Trends
    improvement_rate = models.FloatField(default=0.0)  # % change over last period
    consistency_score = models.FloatField(default=0.0)  # 0-100
    
    # Metadata
    last_activity = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'performance_metrics'
        unique_together = ['user', 'subject']
        ordering = ['-accuracy_percentage']
    
    def __str__(self):
        return f"{self.user.email} - {self.subject} - {self.accuracy_percentage:.1f}%"


class WeakArea(models.Model):
    """Identified weak areas for targeted improvement"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='weak_areas'
    )
    
    subject = models.CharField(max_length=200,db_index=True)
    topic = models.CharField(max_length=200,db_index=True)
    
    attempts = models.IntegerField(default=0)
    correct = models.IntegerField(default=0)
    accuracy = models.FloatField(default=0.0)
    
    priority = models.IntegerField(
        default=1,
        help_text="1=High, 2=Medium, 3=Low"
    )
    
    is_improving = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'weak_areas'
        ordering = ['priority', '-accuracy']
        unique_together = ['user', 'subject', 'topic']
    
    def __str__(self):
        return f"{self.user.email} - {self.topic} ({self.accuracy:.1f}%)"


class DailyProgress(models.Model):
    """Daily progress tracking"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='daily_progress'
    )
    
    date = models.DateField(db_index=True)
    
    study_time_minutes = models.IntegerField(default=0)
    questions_attempted = models.IntegerField(default=0)
    questions_correct = models.IntegerField(default=0)
    
    mock_tests_taken = models.IntegerField(default=0)
    ai_queries = models.IntegerField(default=0)
    
    topics_covered = models.JSONField(default=list, blank=True)
    
    streak_days = models.IntegerField(default=0)
    goals_met = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'daily_progress'
        unique_together = ['user', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', 'date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.date} - {self.study_time_minutes}min"


class PerformanceSnapshot(models.Model):
    """Snapshot of performance per test attempt"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="performance_snapshots",
        db_index=True
    )

    subject = models.CharField(max_length=200, db_index=True)

    test_attempt = models.ForeignKey(
        "mocktest.TestAttempt",
        on_delete=models.CASCADE,
        related_name="performance_snapshots"
    )

    score = models.FloatField()
    total_marks = models.FloatField()
    accuracy = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "performance_snapshots"   # ✅ IMPORTANT (explicit table)
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["subject"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.subject} - {self.accuracy:.2f}%"