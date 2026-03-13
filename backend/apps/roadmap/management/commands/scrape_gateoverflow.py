from collections import defaultdict
import time

from django.core.management.base import BaseCommand

from apps.roadmap.models import Exam
from apps.roadmap.services.gateoverflow_scraper import GateOverflowScraper
from apps.roadmap.services.question_parser_service import QuestionParserService
from apps.roadmap.services.topic_mapper_service import TopicMapperService
from apps.roadmap.services.pyq_import_service import PYQImportService


class Command(BaseCommand):

    help = "Scrape GATEOverflow PYQs"

    def handle(self, *args, **kwargs):

        exam = Exam.objects.get(name="GATE CSE")

        # Scrape all question links from tag pages
        self.stdout.write("Collecting question links...")

        links = GateOverflowScraper.get_question_links()

        self.stdout.write(f"Total links collected: {len(links)}")

        inserted = 0
        visited_links = set()
        unmapped_tags = defaultdict(int)

        for link in links:

            if link in visited_links:
                continue

            visited_links.add(link)

            try:

                question_text, candidates, year, marks = (
                    QuestionParserService.parse_question(link)
                )

            except Exception as e:

                self.stdout.write(
                    self.style.WARNING(
                        f"Failed to parse {link} : {e}"
                    )
                )
                continue

            # Validation
            if not question_text or not year:
                continue

            mapped_topic = TopicMapperService.map_topic(candidates)

            if not mapped_topic:

                for tag in candidates:
                    unmapped_tags[tag] += 1

                continue

            try:

                PYQImportService.save_question(
                    exam=exam,
                    topic_name=mapped_topic,
                    question_text=question_text,
                    year=year,
                    marks=marks,
                    source_url=link
                )

                inserted += 1

                if inserted % 50 == 0:
                    self.stdout.write(f"Inserted {inserted} PYQs")

            except Exception as e:

                self.stdout.write(
                    self.style.WARNING(
                        f"Failed to insert {link} : {e}"
                    )
                )

            time.sleep(0.4)

        self.stdout.write("\n==============================")
        self.stdout.write(f"Total question links found: {len(links)}")
        self.stdout.write(f"Inserted PYQs: {inserted}")

        if unmapped_tags:

            self.stdout.write("\nTop Unmapped Topic Candidates:")

            sorted_tags = sorted(
                unmapped_tags.items(),
                key=lambda x: x[1],
                reverse=True
            )

            for tag, count in sorted_tags[:20]:
                self.stdout.write(f"{tag} -> {count}")

        self.stdout.write(
            self.style.SUCCESS("\nScraping completed")
        )