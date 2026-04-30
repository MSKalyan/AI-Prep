import gdown
import os
import logging

DOWNLOAD_DIR = "data/gate_pyq_zip"
logger = logging.getLogger(__name__)


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

        logger.info("Downloaded files: %s", files)

    except (OSError, ValueError, RuntimeError):
        logger.error("Drive folder download failed for url=%s", folder_url, exc_info=True)
        raise
