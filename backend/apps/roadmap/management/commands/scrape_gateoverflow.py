from django.core.management.base import BaseCommand
from apps.roadmap.models import Exam
from apps.roadmap.services.gateoverflow_scraper import GateOverflowScraper
from apps.roadmap.services.question_parser_service import QuestionParserService
from apps.roadmap.services.pyq_import_service import PYQImportService
from apps.roadmap.services.topic_mapper_service import TopicMapperService


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        exam = Exam.objects.get(name="GATE CSE")

        links = GateOverflowScraper.get_question_links("gatecse-2026-set1")

        print("Total question links:", len(links))

        inserted = 0

        for link in links:

            topic, year, marks = QuestionParserService.parse_question(link)
            mapped_topic = TopicMapperService.map_topic(topic)

            if not topic or not year:
                continue

            success = PYQImportService.save_question(
                exam=exam,
                topic_name=topic,
                year=year,
                marks=marks
            )
            if success:
                inserted += 1

        print("Inserted:", inserted)

        self.stdout.write(self.style.SUCCESS("Scraping completed"))