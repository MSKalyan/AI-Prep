from asgiref.sync import async_to_sync
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from common.utils.retry_utils import safe_get_async

BASE_URL = "https://gate2026.iitg.ac.in"
REQUEST_TIMEOUT_SECONDS = 10


def get_syllabus_links():
    return async_to_sync(get_syllabus_links_async)()


async def get_syllabus_links_async():

    url = f"{BASE_URL}/exam-papers-and-syllabus.html"

    res = await safe_get_async(url, timeout=REQUEST_TIMEOUT_SECONDS)
    html = res.text

    soup = BeautifulSoup(html, "html.parser")

    links = set()

    for a in soup.find_all("a"):

        href = a.get("href")

        if href and "Syllabus" in href and href.endswith(".pdf"):

            full_url = urljoin(BASE_URL, href)

            links.add(full_url)

    return sorted(links)
