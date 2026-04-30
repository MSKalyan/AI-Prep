import re
import logging

from apps.roadmap.models import RoadmapTopic, PYQ
from apps.ai_service.services.llm_service import LLMService
from apps.analytics.services.study_content_service import StudyContentService

logger = logging.getLogger(__name__)


class StudyService:
    @staticmethod
    def _fallback_explanation(topic_name: str) -> str:
        return (
            f"Definition:\n"
            f"- {topic_name} is a core concept commonly tested in competitive exams.\n\n"
            f"Key Points:\n"
            f"- Understand the basic meaning and purpose of {topic_name}.\n"
            f"- Learn the most important properties, rules, or behavior patterns.\n"
            f"- Compare it with related concepts to avoid common confusion.\n\n"
            f"Subtopics to Revise:\n"
            f"- Fundamental ideas and terminology\n"
            f"- Standard problem types and patterns\n"
            f"- Typical exam-level applications\n\n"
            f"Quick Revision:\n"
            f"- Focus on concept clarity first, then solve PYQs and timed questions."
        )
    @staticmethod
    def clean_ai_output(text: str) -> str:
        # Remove markdown bullets (*, -, etc.)
        text = re.sub(r"^\s*[\*\-]\s+", "", text, flags=re.MULTILINE)

        # Remove bold/italic markers (*, **)
        text = re.sub(r"\*{1,2}", "", text)

        # Normalize spacing
        text = re.sub(r"\n{2,}", "\n\n", text)

        return text.strip()

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
            raw = LLMService().generate_response(prompt=prompt)
            return StudyService.clean_ai_output(raw)
        except (TimeoutError, ValueError, TypeError, AttributeError):
            logger.error("Failed to generate AI explanation for topic '%s'", topic_name, exc_info=True)

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
    """.strip()

    @staticmethod
    def get_topic_study_data(topic_id):
        if topic_id is None:
            raise ValueError("topic_id is required")
        if not isinstance(topic_id, int):
            raise TypeError("topic_id must be an integer")

        topic = RoadmapTopic.objects.select_related(
            "topic", "topic__parent", "roadmap"
        ).get(id=topic_id)

        subject = topic.topic.parent.name if topic.topic.parent else topic.topic.name
        if not topic.ai_explanation or len(topic.ai_explanation.strip()) < 80:
            # Keep study page responsive: avoid blocking first-load on external LLM latency.
            topic.ai_explanation = StudyService._fallback_explanation(topic.topic.name)
            topic.save(update_fields=["ai_explanation"])
        pyqs = PYQ.objects.filter(topic=topic.topic).values("year", "marks")
        youtube_data = StudyContentService.get_study_content(topic.topic.name)
        return {
            "roadmap_id": topic.roadmap.id,
            "topic_id": topic.id,
            "topic": topic.topic.name,
            "subject": subject,
            "week": topic.week_number,
            "phase": topic.phase,
            "estimated_hours": topic.estimated_hours,
            "ai_explanation": topic.ai_explanation,
            "pyqs": list(pyqs),
            "youtube_resources": youtube_data.get("youtube_links", [])
            if youtube_data
            else [],
            "mock_tests": [],
        }

    @staticmethod
    def get_roadmap_topics(roadmap_id):

        topics = (
            RoadmapTopic.objects.filter(roadmap_id=roadmap_id)
            .select_related("topic")
            .values("id", "topic__name", "week_number", "is_completed")
            .order_by("week_number")
        )

        return [
            {
                "id": t["id"],
                "topic": t["topic__name"],
                "week": t["week_number"],
                "completed": t["is_completed"],
            }
            for t in topics
        ]
