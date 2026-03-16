from backend.apps.ai_service.services.rag.llm_service import LLMService


class ExplanationService:

    def generate_topic_explanation(self, topic, subject, week):

        prompt = f"""
        Topic: {topic}
        Subject: {subject}
        Week: {week}

        Explain this topic briefly for a student preparing for exams.
        Limit explanation to 3-4 sentences.
        """

        llm = LLMService()

        explanation = llm.generate_response(prompt)

        return explanation