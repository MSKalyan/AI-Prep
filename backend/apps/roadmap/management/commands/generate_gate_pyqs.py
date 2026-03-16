from django.core.management.base import BaseCommand
from apps.roadmap.models import Exam, Topic, PYQ
import random
from backend.apps.roadmap.services.pyq.weightage_service import WeightageService


class Command(BaseCommand):
    help = "Generate synthetic GATE CSE PYQs (2019–2023)"

    def handle(self, *args, **kwargs):

        exam = Exam.objects.get(name="GATE CSE")

        parent_topics = Topic.objects.filter(
            exam=exam,
            parent__isnull=True
        )

        if not parent_topics.exists():
            self.stdout.write(self.style.ERROR("No syllabus found."))
            return

        # Approx realistic distribution %
        weight_distribution = {
            "Engineering Mathematics": 5,
            "Programming & Data Structures": 10,
            "Algorithms": 10,
            "Operating Systems": 10,
            "Databases": 8,
            "Computer Networks": 8,
            "Computer Organization & Architecture": 8,
            "Theory of Computation": 7,
            "Compiler Design": 7,
            "Digital Logic": 7,
        }

        years = [2019, 2020, 2021, 2022, 2023]

        # Clear old synthetic PYQs
        PYQ.objects.filter(exam=exam).delete()

        for year in years:

            total_marks_year = 100

            for topic in parent_topics:

                percentage = weight_distribution.get(topic.name, 5)

                topic_marks = int((percentage / 100) * total_marks_year)

                # Split into random 1 or 2 mark questions
                remaining = topic_marks

                while remaining > 0:

                    mark = random.choice([1, 2])
                    if mark > remaining:
                        mark = remaining

                    PYQ.objects.create(
                        exam=exam,
                        topic=topic,
                        year=year,
                        marks=mark
                    )

                    remaining -= mark

        # After generating PYQs
        WeightageService.compute_weightage(exam)

        self.stdout.write(
            self.style.SUCCESS("Synthetic PYQs generated successfully.")
        )

