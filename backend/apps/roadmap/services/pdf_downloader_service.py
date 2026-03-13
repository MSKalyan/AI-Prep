import os
import requests

DOWNLOAD_DIR = "data/gate_syllabus"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_pdf(url):

    filename = url.split("/")[-1]
    path = f"{DOWNLOAD_DIR}/{filename}"

    if os.path.exists(path):
        return path

    r = requests.get(url)

    with open(path, "wb") as f:
        f.write(r.content)

    return path