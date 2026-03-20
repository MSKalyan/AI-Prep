import json
from django.core.management.base import BaseCommand
from apps.mocktest.models import Question
from apps.roadmap.models import Topic, Exam


class Command(BaseCommand):
    help = "Load PYQs into database"

    def handle(self, *args, **kwargs):

        with open('pyqs.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        created = 0
        skipped = 0

        for item in data:
            try:
                topic, _ = Topic.objects.get_or_create(name=item['topic'])
                exam = Exam.objects.get(name=item['exam'])

                # Validation
                if item['type'] == 'mcq' and not item.get('options'):
                    skipped += 1
                    continue

                Question.objects.create(
                    topic=topic,
                    exam=exam,
                    question_text=item['question'],
                    question_type=item['type'],
                    options=item.get('options'),
                    correct_answer=item.get('answer'),
                    explanation=item.get('explanation', ''),
                    difficulty='medium',
                    source='pyq',
                    year=item.get('year'),
                )

                created += 1

            except Exception as e:
                skipped += 1
                print(f"Error: {e}")

        self.stdout.write(self.style.SUCCESS(
            f"Created: {created}, Skipped: {skipped}"
        ))