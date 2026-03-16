import re

from apps.roadmap.models import RoadmapTopic, PYQ
from apps.ai_service.services.rag.llm_service import LLMService


class StudyService:

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

#         # -----------------------------
#         # Generate AI explanation once
#         # -----------------------------
#         if not topic.ai_explanation:

#             llm = LLMService()

#             prompt = f"""
# You are an expert tutor helping a student prepare for competitive exams.

# Topic: {topic.topic.name}
# Subject: {subject}

# Explain the topic as concise study notes.

# Instructions:
# - Use simple language.
# - Limit the entire explanation to about 120 words.
# - Focus only on key exam concepts.
# - Do not use markdown symbols like ** or ##.
# - Keep formatting exactly as shown below.

# Output format:

# Concept Overview:
# A short explanation (2–3 sentences).

# Key Points:
# - Important idea
# - Important idea
# - Important idea

# Exam Focus:
# - What exam questions usually test
# - Important formula, rule, or comparison
# """

#             explanation = llm.generate_response(prompt, user=topic.roadmap.user, endpoint="topic-explanation") or "Explanation unavailable."
#             print("Generated AI Explanation:", explanation)
#             if explanation:
#                 explanation = re.sub(r'(?<=:)\s+', '\n', explanation)
#                 explanation = explanation.replace("**", "").strip()
#             topic.ai_explanation = explanation
#             topic.save(update_fields=["ai_explanation"])

        # -----------------------------
        # Fetch PYQs
        # -----------------------------
        pyqs = PYQ.objects.filter(
            topic=topic.topic
        ).values("year", "marks")

        return {
            "roadmap_id": topic.roadmap.id,
            "topic": topic.topic.name,
            "subject": subject,
            "week": topic.week_number,
            "phase": topic.phase,
            "estimated_hours": topic.estimated_hours,
            "ai_explanation": topic.ai_explanation,
            "pyqs": list(pyqs),
            "youtube_resources": [],
            "mock_tests": []
        }

    # --------------------------------
    # Sidebar Topics
    # --------------------------------

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