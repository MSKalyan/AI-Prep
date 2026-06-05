import os
import requests
from urllib.parse import urlparse

DOWNLOAD_DIR = "data/gate_syllabus"
REQUEST_TIMEOUT_SECONDS = 30
CHUNK_SIZE_BYTES = 1024 * 1024

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def download_pdf(url):
    filename = os.path.basename(urlparse(url).path) or "syllabus.pdf"
    path = os.path.join(DOWNLOAD_DIR, filename)

    if os.path.exists(path):
        return path

    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS, stream=True)
    response.raise_for_status()

    with open(path, "wb") as f:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE_BYTES):
            if chunk:
                f.write(chunk)

    return path