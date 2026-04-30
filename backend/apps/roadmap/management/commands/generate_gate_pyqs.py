import secrets

from django.core.management.base import BaseCommand

from apps.roadmap.models import Exam, Topic, PYQ
from backend.apps.roadmap.services.pyq.weightage_service import WeightageService


class Command(BaseCommand):
    help = "Generate synthetic GATE CSE PYQs (2019â€“2023)"

    def handle(self, *args, **kwargs):
        exam = self._get_exam()
        parent_topics = self._get_parent_topics(exam)

        if not parent_topics.exists():
            self.stdout.write(self.style.ERROR("No syllabus found."))
            return

        self._clear_old_pyqs(exam)
        self._generate_for_years(
            exam,
            parent_topics,
            self._get_years(),
            self._get_weight_distribution(),
        )
        WeightageService.compute_weightage(exam)
        self.stdout.write(self.style.SUCCESS("Synthetic PYQs generated successfully."))

    @staticmethod
    def _get_exam():
        return Exam.objects.get(name="GATE CSE")

    @staticmethod
    def _get_parent_topics(exam):
        return Topic.objects.filter(exam=exam, parent__isnull=True)

    @staticmethod
    def _clear_old_pyqs(exam):
        PYQ.objects.filter(exam=exam).delete()

    @staticmethod
    def _get_years():
        return [2019, 2020, 2021, 2022, 2023]

    @staticmethod
    def _get_weight_distribution():
        return {
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

    def _generate_for_years(self, exam, parent_topics, years, weight_distribution):
        for year in years:
            self._generate_for_topics(exam, parent_topics, year, weight_distribution)

    def _generate_for_topics(self, exam, parent_topics, year, weight_distribution):
        total_marks_year = 100
        for topic in parent_topics:
            percentage = weight_distribution.get(topic.name, 5)
            topic_marks = int((percentage / 100) * total_marks_year)
            self._create_topic_pyqs(exam, topic, year, topic_marks)

    @staticmethod
    def _create_topic_pyqs(exam, topic, year, topic_marks):
        remaining = topic_marks
        while remaining > 0:
            mark = secrets.choice((1, 2))
            if mark > remaining:
                mark = remaining
            PYQ.objects.create(exam=exam, topic=topic, year=year, marks=mark)
            remaining -= mark
