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
    def _generate_ai_explanation(topic_name: str, subject: str) -> str:
        from django.conf import settings
        try:
            api_key = settings.GROQ_API_KEY
            if not api_key:
                logger.warning("GROQ_API_KEY not configured, using fallback")
                return StudyService._fallback_explanation(topic_name)

            prompt = f"""You are an expert tutor helping students prepare for competitive exams like GATE.

Topic: {topic_name}
Subject: {subject}

Provide a concise explanation in this exact format:
1. Overview: A brief 2-3 sentence introduction to {topic_name}
2. Key Concepts: 4-5 important points students must know
3. Common Pitfalls: 2-3 mistakes students make
4. Quick Tips: 2-3 memory aids or shortcuts

Keep total under 150 words. Use simple language."""

            llm = LLMService()
            explanation = llm.generate_response(prompt, endpoint="topic-explanation")

            if explanation:
                explanation = StudyService.clean_ai_output(explanation)
                logger.info(f"Generated AI explanation for topic: {topic_name}")
                return explanation

            logger.warning(f"LLM returned empty explanation for {topic_name}, using fallback")
            return StudyService._fallback_explanation(topic_name)

        except Exception as e:
            logger.error(f"Failed to generate AI explanation for {topic_name}: {e}")
            return StudyService._fallback_explanation(topic_name)

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
        needs_regeneration = (
            not topic.ai_explanation or
            len(topic.ai_explanation.strip()) < 80 or
            "Definition:" in topic.ai_explanation
        )
        if needs_regeneration:
            explanation = StudyService._generate_ai_explanation(topic.topic.name, subject)
            topic.ai_explanation = explanation
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
            "youtube_resources": youtube_data.get("youtube_videos", [])
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
