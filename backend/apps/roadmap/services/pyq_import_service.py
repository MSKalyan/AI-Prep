from apps.roadmap.models import PYQ, Topic


class PYQImportService:

    @staticmethod
    def save_question(exam, topic_name, year, marks):

        topic = Topic.objects.filter(
            exam=exam,
            name__iexact=topic_name
        ).first()

        if not topic:
            print(f"Topic not found: {topic_name}")
            return

        # avoid duplicate entries
        obj, created = PYQ.objects.get_or_create(
            exam=exam,
            topic=topic,
            year=year,
            marks=marks
        )

        if created:
            print(f"Inserted PYQ → {topic_name} ({year}, {marks} marks)")