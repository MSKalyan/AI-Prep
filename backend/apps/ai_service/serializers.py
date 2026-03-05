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







class TopicExplanationSerializer(serializers.Serializer):
    name = serializers.CharField()
    hours = serializers.IntegerField()
    explanation = serializers.CharField()


class WeekExplanationSerializer(serializers.Serializer):
    week = serializers.IntegerField()
    phase = serializers.CharField()
    topics = TopicExplanationSerializer(many=True)


class RoadmapAIResponseSerializer(serializers.Serializer):
    weeks = WeekExplanationSerializer(many=True)

    def validate(self, data):

        original = self.context["original"]

        if len(data["weeks"]) != len(original["weeks"]):
            raise serializers.ValidationError("Week count mismatch.")

        for ai_week, orig_week in zip(data["weeks"], original["weeks"]):

            if ai_week["week"] != orig_week["week"]:
                raise serializers.ValidationError(
                    f"Week number changed: {ai_week['week']}"
                )

            if ai_week["phase"] != orig_week["phase"]:
                raise serializers.ValidationError(
                    f"Phase changed in week {ai_week['week']}"
                )

            if len(ai_week["topics"]) != len(orig_week["topics"]):
                raise serializers.ValidationError(
                    f"Topic count mismatch in week {ai_week['week']}"
                )

            for ai_topic, orig_topic in zip(
                ai_week["topics"], orig_week["topics"]
            ):

                if ai_topic["name"] != orig_topic["name"]:
                    raise serializers.ValidationError(
                        f"Topic name changed: {orig_topic['name']}"
                    )

                if ai_topic["hours"] != orig_topic["hours"]:
                    raise serializers.ValidationError(
                        f"Study hours changed for {orig_topic['name']}"
                    )

        return data