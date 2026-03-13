from django.core.management.base import BaseCommand

from apps.roadmap.services.scrape_gate_syllabus import get_syllabus_links
from apps.roadmap.services.pdf_downloader_service import download_pdf
from apps.roadmap.services.pdf_text_extractor import extract_text
from apps.roadmap.services.syllabus_parser_service import parse_syllabus
from apps.roadmap.services.syllabus_import_service import save_syllabus


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        links = get_syllabus_links()

        for link in links:

            pdf_path = download_pdf(link)

            text = extract_text(pdf_path)

            syllabus = parse_syllabus(text)

            filename = link.split("/")[-1]

            branch = filename.split("_")[0]

            exam_name = f"GATE {branch}"
            save_syllabus(exam_name, syllabus)

        self.stdout.write(self.style.SUCCESS("All syllabus imported"))