# apps/roadmap/services/pyq/pyq_file_selector.py

import os

BASE_DIR = "data/gate_pyq_pdf/CS"
YEARS = ["2020", "2021", "2022", "2023", "2024","2025"]

def get_target_pdfs():
    files = []
    for f in os.listdir(BASE_DIR):
        for y in YEARS:
            if y in f and f.endswith(".pdf"):
                files.append(os.path.join(BASE_DIR, f))
    return files