from pathlib import Path

from django.core.management.base import BaseCommand

from apps.roadmap.models import Exam
from apps.roadmap.services.pyq.drive_downloader import download_drive_folder
from apps.roadmap.services.pyq.pyq_file_selector import get_target_pdfs
from apps.roadmap.services.pyq.pyq_import_service import PYQImportService
from apps.roadmap.services.pyq.pyq_text_extractor import extract_text
from apps.roadmap.services.pyq.question_parser_service import QuestionParserService
from apps.roadmap.services.pyq.topic_mapper_service import TopicMapperService
from apps.roadmap.services.pyq.zip_extractor_service import extract_all

ZIP_DIR = Path("data/gate_pyq_zip")
DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1sV6FgtOUDl_PGjc36Zdc0eJwK1zZ_2OF"


def zip_files_exist() -> bool:
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

    def _get_exam(self, exam_name: str):
        try:
            return Exam.objects.get(name=exam_name)
        except Exam.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Exam {exam_name} not found"))
            return None

    def _ensure_zips_downloaded(self) -> None:
        if zip_files_exist():
            self.stdout.write("ZIP files already exist -> skipping download")
            return
        self.stdout.write("Step 1 -> Downloading ZIP files")
        download_drive_folder(DRIVE_FOLDER_URL)

    def _extract_zips(self) -> None:
        self.stdout.write("Step 2 -> Extracting ZIP files")
        extract_all()

    def _get_pdf_files(self):
        self.stdout.write("Step 3 -> Selecting PDF papers")
        pdf_files = get_target_pdfs()
        self.stdout.write(f"Found {len(pdf_files)} papers")
        return pdf_files

    @staticmethod
    def _is_valid_question(question_text, options, correct_answer, topic) -> bool:
        if not question_text or len(question_text) < 30:
            return False
        if not options or len(options) < 2:
            return False
        if not correct_answer:
            return False
        if not topic:
            return False
        return True

    def _process_questions(self, *, exam, year, path, questions, dry_run: bool):
        created = 0
        skipped = 0

        for sq in questions:
            is_created = self._process_single_question(
                exam=exam, year=year, path=path, sq=sq, dry_run=dry_run
            )
            if is_created is True:
                created += 1
            elif is_created is False:
                skipped += 1

        return created, skipped

    def _process_single_question(self, *, exam, year, path, sq, dry_run: bool):
        question_payload = self._extract_question_payload(sq, exam)
        if not question_payload:
            return False

        if dry_run:
            self._print_dry_run(question_payload["question_text"], question_payload["topic"])
            return None

        pyq_obj = PYQImportService.save_question_with_options(
            exam=exam,
            topic=question_payload["topic"],
            question_text=question_payload["question_text"],
            year=year,
            marks=question_payload["marks"],
            question_type=question_payload["question_type"],
            options=question_payload["options"],
            correct_answer=question_payload["correct_answer"],
            source_url=path,
        )
        return bool(pyq_obj)

    def _extract_question_payload(self, sq, exam):
        question_text = sq.get("question_text", "")
        options = sq.get("options", {})
        correct_answer = sq.get("correct_answer")
        marks = sq.get("marks", 1)
        question_type = sq.get("question_type", "mcq")
        topic = TopicMapperService.map_topic(question_text, exam=exam)

        if not self._is_valid_question(question_text, options, correct_answer, topic):
            return None

        return {
            "question_text": question_text,
            "options": options,
            "correct_answer": correct_answer,
            "marks": marks,
            "question_type": question_type,
            "topic": topic,
        }

    def _print_dry_run(self, question_text, topic):
        self.stdout.write(f"[DRY] Would create: {question_text[:50]}... -> {topic.name}")

    def _process_pdf(self, *, exam, pdf, dry_run: bool):
        year = pdf["year"]
        path = pdf["path"]

        self.stdout.write(f"Processing {year} -> {path}")

        try:
            text = extract_text(path)
        except (OSError, ValueError) as e:
            self.stdout.write(
                self.style.WARNING(f"Skipping corrupted PDF -> {path} ({str(e)})")
            )
            return 0, 0

        questions = QuestionParserService.parse_pdf_complete(text, year)
        self.stdout.write(f"Extracted {len(questions)} questions")

        return self._process_questions(
            exam=exam, year=year, path=path, questions=questions, dry_run=dry_run
        )

    def handle(self, *args, **kwargs):
        exam_name = kwargs.get("exam", "GATE CS")
        dry_run = kwargs.get("dry_run", False)

        exam = self._get_exam(exam_name)
        if exam is None:
            return

        self._ensure_zips_downloaded()
        self._extract_zips()
        pdf_files = self._get_pdf_files()

        created_count = 0
        skipped_count = 0

        for pdf in pdf_files:
            created, skipped = self._process_pdf(exam=exam, pdf=pdf, dry_run=dry_run)
            created_count += created
            skipped_count += skipped

        self.stdout.write(
            self.style.SUCCESS(
                f"PYQ ingestion completed: Created {created_count}, Skipped {skipped_count}"
            )
        )
