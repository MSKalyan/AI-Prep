from apps.roadmap.models import PYQ
from apps.roadmap.services.pyq.topic_mapper_service import TopicMapperService


class PYQImportService:
    @staticmethod
    def save_question(exam, topic, question_text, year, marks, source_url):

        if topic is None:
            topic = TopicMapperService.map_topic(question_text, exam=exam)

        if topic is None:
            print("Skipping PYQ because no topic mapping could be inferred")
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
            print(f"Inserted PYQ → {topic.name} ({year}, {marks} marks)")
            return obj

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

        if updated:
            obj.save()

        return obj

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

        if topic is None:
            topic = TopicMapperService.map_topic(question_text, exam=exam)

        if topic is None:
            print(f"Skipping PYQ: no topic mapping for: {question_text[:50]}...")
            return None

        options_data = options if options else {}

        correct_answer_data = None
        if correct_answer:
            if isinstance(correct_answer, str) and correct_answer.upper() in [
                "A",
                "B",
                "C",
                "D",
            ]:
                correct_answer_data = [correct_answer.upper()]
            elif isinstance(correct_answer, list):
                correct_answer_data = correct_answer

        existing = PYQ.objects.filter(
            exam=exam,
            topic=topic,
            question_text__icontains=question_text[:100],
            year=year,
        ).first()

        if existing:
            if options_data and not existing.options:
                existing.options = options_data
                existing.save()
            return existing

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

        print(f"Inserted PYQ with options → {topic.name} ({year}, {marks} marks)")
        return pyq
