from rest_framework import serializers
from .models import Conversation, Message, Document


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('id', 'role', 'content', 'confidence_score', 
                  'retrieved_documents', 'created_at')
        read_only_fields = ('id', 'created_at', 'confidence_score', 'retrieved_documents')


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ('id', 'title', 'context', 'message_count', 
                  'messages', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_message_count(self, obj):
        return obj.messages.count()


class AskAISerializer(serializers.Serializer):
    question = serializers.CharField(max_length=2000)
    context = serializers.CharField(
        max_length=200, 
        required=False, 
        allow_blank=True,
        help_text="Subject or topic context"
    )
    conversation_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Continue existing conversation"
    )
    exam_type = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True
    )


class GenerateQuestionsAISerializer(serializers.Serializer):
    exam_type = serializers.CharField(max_length=100)
    subject = serializers.CharField(max_length=200)
    topic = serializers.CharField(max_length=200, required=False, allow_blank=True)
    difficulty = serializers.ChoiceField(
        choices=['easy', 'medium', 'hard'],
        default='medium'
    )
    num_questions = serializers.IntegerField(min_value=1, max_value=20, default=5)
    question_type = serializers.ChoiceField(
        choices=['mcq', 'true_false', 'short_answer'],
        default='mcq'
    )


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ('id', 'title', 'content', 'document_type', 'subject',
                  'topic', 'exam_type', 'source_url', 'author', 'tags',
                  'created_at')
        read_only_fields = ('id', 'created_at', 'embedding')
