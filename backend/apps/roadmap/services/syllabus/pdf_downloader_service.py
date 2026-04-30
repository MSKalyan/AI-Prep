import os
from urllib.parse import urlparse
from asgiref.sync import async_to_sync
import httpx

DOWNLOAD_DIR = "data/gate_syllabus"
REQUEST_TIMEOUT_SECONDS = 30
CHUNK_SIZE_BYTES = 1024 * 1024

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_pdf(url):
    return async_to_sync(download_pdf_async)(url)


async def download_pdf_async(url):

    filename = os.path.basename(urlparse(url).path) or "syllabus.pdf"
    path = os.path.join(DOWNLOAD_DIR, filename)

    if os.path.exists(path):
        return path

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            with open(path, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=CHUNK_SIZE_BYTES):
                    if chunk:
                        f.write(chunk)

    return path
