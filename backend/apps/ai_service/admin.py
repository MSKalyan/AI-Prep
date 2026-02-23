from django.contrib import admin
from .models import Document, Conversation, Message, AIUsageLog


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'document_type', 'subject', 'exam_type', 'created_at')
    list_filter = ('document_type', 'exam_type', 'subject')
    search_fields = ('title', 'content', 'subject', 'topic')
    list_per_page = 50


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ('role', 'content', 'total_tokens', 'created_at')
    readonly_fields = ('created_at',)
    can_delete = False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'context', 'created_at', 'updated_at')
    list_filter = ('created_at', 'context')
    search_fields = ('user__email', 'title', 'context')
    inlines = [MessageInline]
    date_hierarchy = 'created_at'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'role', 'content_preview', 'total_tokens', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('content', 'conversation__user__email')
    readonly_fields = ('created_at',)
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'


@admin.register(AIUsageLog)
class AIUsageLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'endpoint', 'model_used', 'total_tokens', 
                   'success', 'response_time_ms', 'created_at')
    list_filter = ('success', 'endpoint', 'model_used', 'created_at')
    search_fields = ('user__email', 'endpoint')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
