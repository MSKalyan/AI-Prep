from apps.roadmap.models import PYQ
from apps.roadmap.services.pyq.topic_mapper_service import TopicMapperService


class PYQImportService:

    @staticmethod
    def save_question(exam, topic, question_text, year, marks, source_url):

        # if topic not provided, infer using mapper
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
                "source_url": source_url
            }
        )

        if created:
            print(f"Inserted PYQ → {topic.name} ({year}, {marks} marks)")
            return obj

        # update existing record if metadata changed
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