import zipfile
import os

ZIP_DIR = "data/gate_pyq_zip"
EXTRACT_DIR = "data/gate_pyq_pdf"


def extract_all():

    os.makedirs(EXTRACT_DIR, exist_ok=True)

    for file in os.listdir(ZIP_DIR):

        if file.endswith(".zip"):

            path = os.path.join(ZIP_DIR, file)

            with zipfile.ZipFile(path, "r") as zip_ref:

                zip_ref.extractall(EXTRACT_DIR)