from bs4 import BeautifulSoup
from urllib.parse import urljoin
from common.utils.retry_utils import safe_get

BASE_URL = "https://gate2026.iitg.ac.in"
REQUEST_TIMEOUT_SECONDS = 10


def get_syllabus_links():

    url = f"{BASE_URL}/exam-papers-and-syllabus.html"

    res = safe_get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    html = res.text

    soup = BeautifulSoup(html, "html.parser")

    links = set()

    for a in soup.find_all("a"):

        href = a.get("href")

        if href and "Syllabus" in href and href.endswith(".pdf"):

            full_url = urljoin(BASE_URL, href)

            links.add(full_url)

    return sorted(links)
