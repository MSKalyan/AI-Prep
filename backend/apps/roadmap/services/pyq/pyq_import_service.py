import logging

from apps.roadmap.models import PYQ
from apps.roadmap.services.pyq.topic_mapper_service import TopicMapperService

logger = logging.getLogger(__name__)


class PYQImportService:
    @staticmethod
    def save_question(exam, topic, question_text, year, marks, source_url):
        topic = PYQImportService._resolve_topic(exam, topic, question_text)
        if topic is None:
            logger.warning("Skipping PYQ because no topic mapping could be inferred")
            return

        obj, created = PYQ.objects.get_or_create(
            exam=exam,
            question_text=question_text,
            defaults={
                "topic": topic,
                "year": year,
                "marks": marks,
                "question_type": "mcq",
                "source_url": source_url,
            },
        )

        if created:
            logger.info("Inserted PYQ -> %s (%s, %s marks)", topic.name, year, marks)
            return obj

        if PYQImportService._update_existing_pyq(obj, topic, marks, year):
            obj.save()

        return obj

    @staticmethod
    def _resolve_topic(exam, topic, question_text):
        if topic is not None:
            return topic
        return TopicMapperService.map_topic(question_text, exam=exam)

    @staticmethod
    def _update_existing_pyq(obj, topic, marks, year):
        updated = False
        if obj.topic != topic:
            obj.topic = topic
            updated = True
        if obj.marks != marks:
            obj.marks = marks
            updated = True
        if obj.year != year:
            obj.year = year
            updated = True
        return updated

    @staticmethod
    def save_question_with_options(
        exam,
        topic,
        question_text,
        year,
        marks=1,
        question_type="mcq",
        options=None,
        correct_answer=None,
        source_url="",
    ):
        """Save PYQ with full options and answer data."""
        topic = PYQImportService._resolve_topic(exam, topic, question_text)
        if topic is None:
            logger.warning(
                "Skipping PYQ: no topic mapping for: %s...", question_text[:50]
            )
            return None

        options_data = options if options else {}
        correct_answer_data = PYQImportService._normalize_correct_answer(correct_answer)
        existing = PYQImportService._get_existing_question(exam, topic, question_text, year)
        if existing:
            return PYQImportService._update_existing_options(existing, options_data)
        return PYQImportService._create_question_with_options(
            exam=exam,
            topic=topic,
            year=year,
            marks=marks,
            question_type=question_type,
            question_text=question_text,
            options_data=options_data,
            correct_answer_data=correct_answer_data,
            source_url=source_url,
        )

    @staticmethod
    def _normalize_correct_answer(correct_answer):
        if not correct_answer:
            return None
        if isinstance(correct_answer, str) and correct_answer.upper() in ["A", "B", "C", "D"]:
            return [correct_answer.upper()]
        if isinstance(correct_answer, list):
            return correct_answer
        return None

    @staticmethod
    def _get_existing_question(exam, topic, question_text, year):
        return PYQ.objects.filter(
            exam=exam,
            topic=topic,
            question_text__icontains=question_text[:100],
            year=year,
        ).first()

    @staticmethod
    def _update_existing_options(existing, options_data):
        if options_data and not existing.options:
            existing.options = options_data
            existing.save()
        return existing

    @staticmethod
    def _create_question_with_options(
        *,
        exam,
        topic,
        year,
        marks,
        question_type,
        question_text,
        options_data,
        correct_answer_data,
        source_url,
    ):
        pyq = PYQ.objects.create(
            exam=exam,
            topic=topic,
            year=year,
            marks=marks,
            question_type=question_type,
            question_text=question_text,
            options=options_data,
            correct_answer=correct_answer_data,
            source_url=source_url,
        )
        logger.info("Inserted PYQ with options -> %s (%s, %s marks)", topic.name, year, marks)
        return pyq
