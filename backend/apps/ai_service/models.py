from django.db import models
from django.conf import settings


class Document(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ("textbook", "Textbook"),
        ("notes", "Notes"),
        ("article", "Article"),
        ("syllabus", "Syllabus"),
        ("previous_paper", "Previous Year Paper"),
    ]

    SOURCE_TYPE_CHOICES = [
        ("upload", "Upload"),
        ("scraped", "Scraped"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
        db_index=True,
        null=True,
        blank=True,
    )

    title = models.CharField(max_length=500)

    file = models.FileField(upload_to="documents/", null=True, blank=True)

    content = models.TextField()

    document_type = models.CharField(
        max_length=20, choices=DOCUMENT_TYPE_CHOICES, default="notes", db_index=True
    )

    subject = models.CharField(max_length=200)

    topic = models.CharField(max_length=200, blank=True)

    exam_type = models.CharField(max_length=100, db_index=True)

    source_type = models.CharField(
        max_length=20, choices=SOURCE_TYPE_CHOICES, default="upload", db_index=True
    )

    source_url = models.URLField(blank=True)

    tags = models.JSONField(default=list, blank=True)

    processed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "documents"
        ordering = ["id"]
        indexes = [
            models.Index(fields=["subject", "exam_type"]),
            models.Index(fields=["document_type"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.subject}"


class Conversation(models.Model):
    """Chat conversations with AI"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations",
        db_index=True,
    )
    title = models.CharField(max_length=300, blank=True)
    context = models.CharField(max_length=200, blank=True)  # e.g., subject/topic

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "conversations"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user.email} - {self.title or 'Conversation'}"


class Message(models.Model):
    """Individual messages in a conversation"""

    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System"),
    ]

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, db_index=True)
    content = models.TextField()

    # RAG metadata
    retrieved_documents = models.JSONField(default=list, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)

    # Token usage tracking
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messages"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."

