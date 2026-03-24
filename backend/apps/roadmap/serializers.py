from datetime import date

from rest_framework import serializers
from .models import Roadmap, RoadmapTopic, Exam


# =====================================================
# EXAM SERIALIZER (Dropdown API)
# =====================================================

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


# =====================================================
# ROADMAP TOPIC SERIALIZER
# =====================================================

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


# =====================================================
# ROADMAP SERIALIZER (MAIN RESPONSE)
# =====================================================

class RoadmapSerializer(serializers.ModelSerializer):

    topics = RoadmapTopicSerializer(many=True, read_only=True) 

    # Show exam details instead of raw FK
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


# # =====================================================
# # ROADMAP GENERATE SERIALIZER (INPUT ONLY)
# # =====================================================

# class RoadmapGenerateSerializer(serializers.Serializer):

#     exam_id = serializers.IntegerField()

#     target_date = serializers.DateField()

#     target_marks = serializers.IntegerField(min_value=1)



#     study_hours_per_day = serializers.IntegerField(
#         min_value=1,
#         max_value=24
#     )

#     current_knowledge = serializers.CharField(
#         required=False,
#         allow_blank=True
#     )

# =====================================================
# DETERMINISTIC ROADMAP GENERATE SERIALIZER (SPRINT 3)
# =====================================================
 
class DeterministicRoadmapGenerateSerializer(serializers.Serializer):

    exam_id = serializers.IntegerField()
    target_date = serializers.DateField()
    study_hours_per_day = serializers.IntegerField(
        min_value=1,
        max_value=24
    )

    # Field-level validation
    def validate_target_date(self, value):
        if value <= date.today():
            raise serializers.ValidationError(
                "Target date must be a future date."
            )
        return value

    # Object-level validation
    def validate(self, data):
        exam_id = data.get("exam_id")
        target_date = data.get("target_date")

        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            raise serializers.ValidationError(
                {"exam_id": "Invalid exam selected."}
            )

        if exam.exam_date and target_date > exam.exam_date:
            raise serializers.ValidationError(
                {
                    "target_date":
                        "Target date cannot exceed the official exam date."
                }
            )

        # Store exam instance for later use
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