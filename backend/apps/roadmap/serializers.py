from datetime import date

from rest_framework import serializers
from .models import Roadmap, RoadmapTopic, Exam



class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = (
            "id",
            "name",
            "category",
            "total_marks",
            "exam_date",
        )


class RoadmapTopicSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source="topic.name", read_only=True)
    subject_name = serializers.SerializerMethodField()

    def get_subject_name(self, obj):
        if obj.topic.parent:
            return obj.topic.parent.name
        return obj.topic.name

    class Meta:
        model = RoadmapTopic
        fields = (
            "id",
            "week_number",
            "topic_name",
            "estimated_hours",
            "resources",
            "priority",
            "is_completed",
            "completed_at",
            "created_at",
            "subject_name",
            "phase",
        )

        read_only_fields = (
            "id",
            "created_at",
        )


class RoadmapSerializer(serializers.ModelSerializer):
    topics = RoadmapTopicSerializer(many=True, read_only=True)

    exam = ExamSerializer(read_only=True)

    class Meta:
        model = Roadmap
        fields = (
            "id",
            "exam",
            "target_date",
            "total_weeks",
            "description",
            "topics",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )



class DeterministicRoadmapGenerateSerializer(serializers.Serializer):
    exam_id = serializers.IntegerField()
    target_date = serializers.DateField()
    study_hours_per_day = serializers.IntegerField(min_value=1, max_value=24)

    def validate_target_date(self, value):
        if value <= date.today():
            raise serializers.ValidationError("Target date must be a future date.")
        if value > date(2027, 3, 1):
            raise serializers.ValidationError("Target date must be on or before 01 March 2027.")
        return value

    def validate(self, data):
        exam_id = data.get("exam_id")
        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            raise serializers.ValidationError({"exam_id": "Invalid exam selected."})

        data["exam"] = exam
        return data

    class StudyTopicSerializer(serializers.Serializer):
        topic = serializers.CharField()
        subject = serializers.CharField()
        week = serializers.IntegerField()
        phase = serializers.CharField()
        estimated_hours = serializers.IntegerField()
        ai_explanation = serializers.CharField(allow_blank=True)

        pyqs = serializers.ListField(default=[])
        youtube_resources = serializers.ListField(default=[])
        mock_tests = serializers.ListField(default=[])
