import gdown
import os

DOWNLOAD_DIR = "data/gate_pyq_zip"


def download_drive_folder(folder_url):

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    try:
        files = gdown.download_folder(
            url=folder_url,
            output=DOWNLOAD_DIR,
            quiet=False,
            use_cookies=False,
            remaining_ok=True   # important
        )

        print("Downloaded files:", files)

    except Exception as e:
        print("Drive download error:", e)