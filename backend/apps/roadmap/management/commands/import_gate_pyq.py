from django.core.management.base import BaseCommand
from pathlib import Path
from apps.roadmap.models import Exam

from apps.roadmap.services.pyq.drive_downloader import download_drive_folder
from apps.roadmap.services.pyq.zip_extractor_service import extract_all
from apps.roadmap.services.pyq.pyq_file_selector import get_target_pdfs
from apps.roadmap.services.pyq.pyq_text_extractor import extract_text
from apps.roadmap.services.pyq.question_parser_service import QuestionParserService
from apps.roadmap.services.pyq.pyq_import_service import PYQImportService
from apps.roadmap.services.pyq.topic_mapper_service import TopicMapperService

ZIP_DIR = Path("data/gate_pyq_zip")

def zip_files_exist():
    if not ZIP_DIR.exists():
        return False
    return any(ZIP_DIR.glob("*.zip"))
class Command(BaseCommand):

    help = "Import GATE PYQs from Google Drive dataset"

    def handle(self, *args, **kwargs):

        exam = Exam.objects.get(name="GATE CS")

        DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1sV6FgtOUDl_PGjc36Zdc0eJwK1zZ_2OF"

        if zip_files_exist():
            self.stdout.write("ZIP files already exist → skipping download")
        else:
            self.stdout.write("Step 1 → Downloading ZIP files")
            download_drive_folder(DRIVE_FOLDER_URL)
        self.stdout.write("Step 2 → Extracting ZIP files")
        extract_all()

        self.stdout.write("Step 3 → Selecting PDF papers")
        pdf_files = get_target_pdfs()

        self.stdout.write(f"Found {len(pdf_files)} papers")

        for pdf in pdf_files:

            year = pdf["year"]
            path = pdf["path"]

            self.stdout.write(f"Processing {year} → {path}")

            try:
                text = extract_text(path)
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"Skipping corrupted PDF → {path} ({str(e)})")
                )
                continue
            questions = QuestionParserService.split_questions(text)

            self.stdout.write(f"Extracted {len(questions)} questions")

            for q in questions:

                topic = TopicMapperService.map_topic(q, exam=exam)

                PYQImportService.save_question(
                    exam=exam,
                    topic=topic,
                    question_text=q,
                    year=year,
                    marks=1,
                    source_url=path
                )

        self.stdout.write(self.style.SUCCESS("PYQ ingestion completed"))