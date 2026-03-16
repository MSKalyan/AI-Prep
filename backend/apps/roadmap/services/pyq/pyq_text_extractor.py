# apps/roadmap/services/pyq/pyq_text_service.py

from apps.roadmap.services.syllabus.pdf_text_extractor import extract_text

def extract_pyq_text(pdf_path):
    return extract_text(pdf_path)