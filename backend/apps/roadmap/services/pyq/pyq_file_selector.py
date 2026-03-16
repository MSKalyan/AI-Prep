# apps/roadmap/services/pyq/pyq_file_selector.py

import os
import re

BASE_DIR = "data/gate_pyq_pdf/CS"

TARGET_YEARS = {2020, 2021, 2022, 2023, 2024, 2025}


def get_target_pdfs():

    papers = []

    for root, _, files in os.walk(BASE_DIR):

        for f in files:

            if not f.lower().endswith(".pdf"):
                continue

            year_match = re.search(r"(20\d{2})", f)

            if not year_match:
                continue

            year = int(year_match.group(1))

            if year not in TARGET_YEARS:
                continue

            papers.append({
                "year": year,
                "path": os.path.join(root, f)
            })

    papers.sort(key=lambda x: x["year"])

    return papers