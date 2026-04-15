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

    def add_arguments(self, parser):
        parser.add_argument("--exam", type=str, default="GATE CS", help="Exam name")
        parser.add_argument(
            "--dry-run", action="store_true", help="Preview without saving"
        )

    def handle(self, *args, **kwargs):

        exam_name = kwargs.get("exam", "GATE CS")
        dry_run = kwargs.get("dry_run", False)

        try:
            exam = Exam.objects.get(name=exam_name)
        except Exam.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Exam {exam_name} not found"))
            return

        DRIVE_FOLDER_URL = (
            "https://drive.google.com/drive/folders/1sV6FgtOUDl_PGjc36Zdc0eJwK1zZ_2OF"
        )

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

        created_count = 0
        skipped_count = 0

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

            questions = QuestionParserService.parse_pdf_complete(text, year)

            self.stdout.write(f"Extracted {len(questions)} questions")

            for sq in questions:
                question_text = sq.get("question_text", "")
                options = sq.get("options", {})
                correct_answer = sq.get("correct_answer")
                marks = sq.get("marks", 1)
                question_type = sq.get("question_type", "mcq")

                if not question_text or len(question_text) < 30:
                    skipped_count += 1
                    continue

                if not options or len(options) < 2:
                    skipped_count += 1
                    continue

                if not correct_answer:
                    skipped_count += 1
                    continue

                topic = TopicMapperService.map_topic(question_text, exam=exam)

                if not topic:
                    skipped_count += 1
                    continue

                if dry_run:
                    self.stdout.write(
                        f"[DRY] Would create: {question_text[:50]}... -> {topic.name}"
                    )
                    continue

                pyq_obj = PYQImportService.save_question_with_options(
                    exam=exam,
                    topic=topic,
                    question_text=question_text,
                    year=year,
                    marks=marks,
                    question_type=question_type,
                    options=options,
                    correct_answer=correct_answer,
                    source_url=path,
                )

                if pyq_obj:
                    created_count += 1
                else:
                    skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"PYQ ingestion completed: Created {created_count}, Skipped {skipped_count}"
            )
        )
