import json
from pathlib import Path
from django.core.management.base import BaseCommand
from apps.roadmap.models import Exam, Subject, Topic


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="Path to syllabus json file"
        )

    def handle(self, *args, **options):

        file_path = options["file"]

        if not file_path:
            self.stdout.write(self.style.ERROR("Provide --file"))
            return

        with open(file_path) as f:
            data = json.load(f)

        exam, _ = Exam.objects.get_or_create(name=data["exam"])

        for subject_index, subject_data in enumerate(data["subjects"]):

            subject, _ = Subject.objects.get_or_create(
                exam=exam,
                name=subject_data["name"],
                order=subject_index
            )

            for topic_index, topic_name in enumerate(subject_data["topics"]):

                Topic.objects.get_or_create(
                    subject=subject,
                    name=topic_name,
                    order=topic_index
                )

        self.stdout.write(
            self.style.SUCCESS(f"{data['exam']} syllabus seeded successfully")
        )