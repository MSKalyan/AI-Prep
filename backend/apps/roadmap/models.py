from django.db import models
from django.conf import settings
from django.db.models import Q

# =====================================================
# EXAM MODEL (Dropdown source)
# =====================================================

class Exam(models.Model):

    name = models.CharField(max_length=200,unique=True)
    category = models.CharField(max_length=100, blank=True)
    total_marks = models.IntegerField(default=100)
    exam_date = models.DateField()  # NEW FIELD

    class Meta:
        db_table = "exams"
        ordering = ["name"]

    def __str__(self):
        return self.name

class Subject(models.Model):

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="subjects"
    )

    name = models.CharField(max_length=200)

    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "subjects"
        ordering = ["order", "name"]
        unique_together = ("exam", "name")

    def __str__(self):
        return f"{self.exam.name} - {self.name}"
class Topic(models.Model):

    name = models.CharField(max_length=200)

    subject = models.ForeignKey(
    Subject,
    on_delete=models.CASCADE,
    related_name="topics",
    null=True,
    blank=True
)

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="child_topics"
    )

    order = models.PositiveIntegerField(default=0)

      # NEW FIELDS
    weightage = models.FloatField(default=0.0)  # percentage
    pyq_total_marks = models.FloatField(default=0.0)  # sum of PYQ marks
    pyq_count = models.PositiveIntegerField(default=0)
    is_core = models.BooleanField(default=True)
    class Meta:
        db_table = "topics"
        ordering = ["order", "name"]
        unique_together = ("subject","parent","name")

    def __str__(self):
        if self.subject:
            return f"{self.subject.exam.name} - {self.name}"
        return self.name

class Subtopic(models.Model):

    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="subtopics"
    )

    name = models.CharField(max_length=300)

    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "subtopics"
        ordering = ["order"]
        unique_together = ("topic", "name")

    def __str__(self):
        return f"{self.topic.name} - {self.name}"

# =====================================================
# ROADMAP MODEL (Main learning plan)
# =====================================================

class Roadmap(models.Model):
    """
    Study roadmap generated for user's exam preparation
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="roadmaps",
    )

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="roadmaps",
        null=True,     # TEMP FIX
        blank=True
        
    )

    target_date = models.DateField(db_index=True)

   

    total_weeks = models.PositiveIntegerField(default=1)

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=False,db_index=True)

    class Meta:
        db_table = "roadmaps"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(is_active=True),
                name="unique_active_roadmap_per_user"
            )
        ]

    def __str__(self):
        exam_name = self.exam.name if self.exam else "No Exam"
        return f"{exam_name} - {self.user}"

# =====================================================
# ROADMAP TOPIC MODEL
# =====================================================

class RoadmapTopic(models.Model):
    """
    Individual topics in a roadmap
    """

    roadmap = models.ForeignKey(
        Roadmap,
        on_delete=models.CASCADE,
        related_name="topics",
    )

    topic = models.ForeignKey(
            Topic,
            on_delete=models.CASCADE,
            related_name="roadmap_entries"
        )

    week_number = models.IntegerField()

    day_number = models.IntegerField(default=1) #1-7
  
    estimated_hours = models.PositiveIntegerField(default=10)

    resources = models.JSONField(default=list, blank=True)

    priority = models.IntegerField(default=1)

    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    ai_explanation = models.TextField(null=True,blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    phase = models.CharField(
    max_length=20,
    choices=[
        ("coverage", "Coverage"),
        ("practice", "Practice"),
        ("revision", "Revision"),
    ],
)
    class Meta:
        db_table = "roadmap_topics"
        ordering = ["week_number", "priority"]
        unique_together = ("roadmap", "week_number","day_number", "topic")


    def __str__(self):
        return f"Week {self.week_number}: {self.topic.name}"


# =====================================================
# ASYNC GENERATION JOB MODEL (VERY IMPORTANT)
# =====================================================

class RoadmapGenerationJob(models.Model):
    """
    Tracks async roadmap generation status
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="roadmap_jobs",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
    )

    roadmap = models.ForeignKey(
        Roadmap,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="generation_jobs",
    )

    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    input_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "roadmap_generation_jobs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Job {self.id} - {self.status}"

class PYQ(models.Model):

    QUESTION_TYPES = [
        ("mcq", "Single Correct MCQ"),
        ("msq", "Multiple Select"),
        ("nat", "Numerical Answer"),
        ("int", "Integer Answer"),
        ("desc", "Descriptive"),
    ]

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE,related_name="pyqs")

    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="pyqs"
    )

    year = models.IntegerField()

    marks = models.FloatField()

    question_type = models.CharField(
        max_length=10,
        choices=QUESTION_TYPES
    )

    question_text = models.TextField()

    options = models.JSONField(
        null=True,
        blank=True
    )

    correct_answer = models.JSONField(
        null=True,
        blank=True
    )

    explanation = models.TextField(null=True, blank=True)

    source_url = models.URLField()

    class Meta:
        db_table = "pyqs"

        indexes = [
                models.Index(fields=["exam", "year"]),
                models.Index(fields=["topic"]),
            ]    
        
        
class UserPYQAttempt(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pyq_attempts"
    )

    pyq = models.ForeignKey(
        PYQ,
        on_delete=models.CASCADE,
        related_name="attempts"
    )

    answer = models.JSONField()

    is_correct = models.BooleanField()

    time_taken = models.IntegerField(null=True, blank=True)

    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_pyq_attempts"
        indexes = [
            models.Index(fields=["user", "pyq"]),
        ]