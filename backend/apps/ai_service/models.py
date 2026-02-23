from django.db import models
from django.conf import settings


class Document(models.Model):
    """Knowledge base documents for RAG"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('textbook', 'Textbook'),
        ('notes', 'Notes'),
        ('article', 'Article'),
        ('syllabus', 'Syllabus'),
        ('previous_paper', 'Previous Year Paper'),
    ]
    
    title = models.CharField(max_length=500)
    content = models.TextField()
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPE_CHOICES,
        default='notes',
        db_index=True
    )
    
    subject = models.CharField(max_length=200)
    topic = models.CharField(max_length=200, blank=True)
    exam_type = models.CharField(max_length=100,db_index=True)  # e.g., UPSC, NEET, JEE

    
    # Vector embeddings stored as JSON for simplicity
    # In production, use a proper vector database like Pinecone, Weaviate, or pgvector
    embedding = models.JSONField(null=True, blank=True)
    
    # Metadata
    source_url = models.URLField(blank=True)
    author = models.CharField(max_length=200, blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    # Chunking info
    chunk_index = models.IntegerField(default=0)
    parent_document = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="chunks"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'documents'
        ordering = ['id']
        indexes = [
            models.Index(fields=['subject', 'exam_type']),
            models.Index(fields=['document_type']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.subject}"


class Conversation(models.Model):
    """Chat conversations with AI"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations',
        db_index=True
    )
    title = models.CharField(max_length=300, blank=True)
    context = models.CharField(max_length=200, blank=True)  # e.g., subject/topic
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'conversations'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.title or 'Conversation'}"


class Message(models.Model):
    """Individual messages in a conversation"""
    
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES,db_index=True)
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
        db_table = 'messages'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class AIUsageLog(models.Model):
    """Track AI API usage for billing and monitoring"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_usage_logs'
    )
    
    endpoint = models.CharField(max_length=100)  # ask-ai, generate-questions, etc.
    model_used = models.CharField(max_length=100)
    
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    
    cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    response_time_ms = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True,db_index=True)
    
    class Meta:
        db_table = 'ai_usage_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['endpoint']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.endpoint} - {self.total_tokens} tokens"
