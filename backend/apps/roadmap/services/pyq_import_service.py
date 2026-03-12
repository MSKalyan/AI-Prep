from apps.roadmap.models import PYQ, Topic


class PYQImportService:

    @staticmethod
    def save_question(exam, topic_name, year, marks, source_url):

        topic = Topic.objects.filter(
            exam=exam,
            name=topic_name
        ).first()

        if not topic:
            print(f"Topic not found: {topic_name}")
            return

        # Prevent duplicate insertion using source URL
        obj, created = PYQ.objects.get_or_create(
            source_url=source_url,
            defaults={
                "exam": exam,
                "topic": topic,
                "year": year,
                "marks": marks
            }
        )

        if created:
            print(f"Inserted PYQ → {topic_name} ({year}, {marks} marks)")
            