import gdown
import os


DOWNLOAD_DIR = "data/gate_pyq_zip"


def download_drive_folder(folder_url):

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    gdown.download_folder(
        url=folder_url,
        output=DOWNLOAD_DIR,
        quiet=False,
        use_cookies=False
    )