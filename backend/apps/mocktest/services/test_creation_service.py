import logging
from django.db import transaction

from ..models import Question, MockTest, TestAttempt

logger = logging.getLogger(__name__)


class TestCreationService:
    @staticmethod
    def create_mock_test(user, roadmap, day, topics, num_questions=10, duration_minutes=30):
        from .pyq_service import PYQService
        from .llm_question_service import LLMQuestionService

        topic_ids = sorted([t.id for t in topics])

        logger.debug("=== MOCKTEST DEBUG ===")
        logger.debug("Day: %s", day)
        logger.debug("Topics: %s", [t.name for t in topics])
        logger.debug("Num questions requested: %s", num_questions)

        main_topic = topics[0] if topics else None
        pyq_questions = PYQService.get_pyq_questions(topics, num_questions) if topics else []

        logger.debug("PYQ questions found in %s day topics: %s", len(topics), len(pyq_questions))

        selected_questions = list(pyq_questions)
        remaining = num_questions - len(selected_questions)

        if remaining > 0 and topics:
            from .question_bank_service import QuestionBankService
            bank_questions = QuestionBankService.get_questions(
                topics=topics, count=remaining, exclude_ids=[q.id for q in selected_questions]
            )
            logger.debug("Question-bank fallback found: %s", len(bank_questions))
            selected_questions.extend(bank_questions)
            remaining = num_questions - len(selected_questions)

        llm_questions = []
        if remaining > 0:
            llm_topics = topics if len(topics) <= 3 else topics[:3]
            logger.info("Generating %s questions via LLM for day topics: %s", remaining, [t.name for t in llm_topics])
            llm_questions = LLMQuestionService.generate_with_retry(topics=llm_topics, count=remaining)
            logger.debug("LLM questions generated: %s", len(llm_questions))
            selected_questions.extend(llm_questions)

        if len(selected_questions) == 0 and topics:
            llm_topics = topics[:2]
            selected_questions = LLMQuestionService.generate_with_retry(topics=llm_topics, count=num_questions)

        logger.debug("Total questions: %s", len(selected_questions))
        logger.debug("====================")

        if not selected_questions:
            raise ValueError(f"No questions available. PYQs: {len(pyq_questions)}, LLM failed.")

        selected_questions = selected_questions[:num_questions]
        import secrets
        secrets.SystemRandom().shuffle(selected_questions)

        topic = topics[0] if topics else None
        subject = topic.parent.name if topic and topic.parent else ""

        title = TestCreationService._build_title(subject, topic)

        with transaction.atomic():
            topic_name = main_topic.name if main_topic else "Mixed topics"

            mock_test = MockTest.objects.create(
                user=user,
                roadmap=roadmap,
                title=title,
                description=f"Day {day}: {topic_name}",
                duration_minutes=duration_minutes,
                status="active",
                generation_reason="daily_practice",
                generation_topics=topic_ids[:3],
                started_at=None,
            )

            total_marks = 0
            for q in selected_questions:
                mock_test.questions.add(q)
                total_marks += q.marks

            mock_test.total_marks = total_marks
            mock_test.question_count = len(selected_questions)
            mock_test.save()

            attempt = TestAttempt.objects.create(
                user=user, mock_test=mock_test, total_marks=mock_test.total_marks
            )

            return {"mock_test": mock_test, "attempt": attempt}

    @staticmethod
    def _build_title(subject, topic):
        if subject and topic:
            return f"{subject} - {topic.name}"
        if topic:
            return topic.name
        return "Mock Test"