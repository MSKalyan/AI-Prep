import re

from apps.roadmap.models import RoadmapTopic, PYQ
from apps.ai_service.services.rag.llm_service import LLMService
from apps.analytics.services.study_content_service import StudyContentService
class StudyService:
    @staticmethod
    def generate_explanation(topic_name):

        prompt = f"""
    Explain the topic "{topic_name}" for competitive exams.

    Format:
    - Definition (clear and simple)
    - Key Concepts (bullet points)
    - Important Points (exam-focused)
    - Formula or Rules (if applicable)
    - Quick Revision Summary (short)

    Keep it concise, structured, and easy to revise.
    """

        try:
            return LLMService().generate_response(prompt=prompt)

        except Exception as e:
            print("Groq failed:", e)

            # fallback
            return f"""
    Topic: {topic_name}

    • Definition:
    Understand the meaning of {topic_name}

    • Key Concepts:
    Focus on core principles

    • Important Points:
    Revise frequently asked areas

    • Tip:
    Practice PYQs
    """
    @staticmethod
    def get_topic_study_data(topic_id):

        topic = RoadmapTopic.objects.select_related(
            "topic",
            "topic__parent",
            "roadmap"
        ).get(id=topic_id)

        subject = (
            topic.topic.parent.name
            if topic.topic.parent
            else topic.topic.name
        )
        if not topic.ai_explanation:
                    topic.ai_explanation = StudyService.generate_explanation(
                        topic.topic.name
                    )
                    topic.save(update_fields=["ai_explanation"])
        pyqs = PYQ.objects.filter(
            topic=topic.topic
        ).values("year", "marks")
        youtube_data = StudyContentService.get_study_content(
            topic.topic.name
        )
        return {
            "roadmap_id": topic.roadmap.id,
            "topic_id":topic.id,
            "topic": topic.topic.name,
            "subject": subject,
            "week": topic.week_number,
            "phase": topic.phase,
            "estimated_hours": topic.estimated_hours,
            "ai_explanation": topic.ai_explanation,
            "pyqs": list(pyqs),
    "youtube_resources": youtube_data.get("youtube_links", []) if youtube_data else [],            "mock_tests": []
        }


    @staticmethod
    def get_roadmap_topics(roadmap_id):

        topics = (
            RoadmapTopic.objects
            .filter(roadmap_id=roadmap_id)
            .select_related("topic")
            .values(
                "id",
                "topic__name",
                "week_number",
                "is_completed"
            )
            .order_by("week_number")
        )

        return [
            {
                "id": t["id"],
                "topic": t["topic__name"],
                "week": t["week_number"],
                "completed": t["is_completed"]
            }
            for t in topics
        ]