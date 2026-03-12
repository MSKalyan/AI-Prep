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

        pages = GateOverflowScraper.get_year_pages()

        total_links = 0
        inserted = 0

        visited_links = set()
        unmapped_tags = defaultdict(int)

        for page in pages:

            self.stdout.write(f"Scraping: {page}")

            links = GateOverflowScraper.get_question_links(page)

            total_links += len(links)

            for link in links:

                # Avoid duplicate parsing
                if link in visited_links:
                    continue

                visited_links.add(link)

                try:
                    candidates, year, marks = (
                        QuestionParserService.parse_question(link)
                    )

                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Failed to parse {link} : {e}"
                        )
                    )
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
                        year=year,
                        marks=marks,
                        source_url=link
                    )

                    inserted += 1

                except Exception as e:

                    self.stdout.write(
                        self.style.WARNING(
                            f"Failed to insert {link} : {e}"
                        )
                    )

                # Prevent aggressive scraping
                time.sleep(0.3)

        self.stdout.write("\n==============================")
        self.stdout.write(f"Total question links found: {total_links}")
        self.stdout.write(f"Inserted PYQs: {inserted}")

        if unmapped_tags:

            self.stdout.write("\nUnmapped topic candidates:")

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