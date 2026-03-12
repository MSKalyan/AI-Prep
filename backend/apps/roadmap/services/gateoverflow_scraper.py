import time
import requests
from bs4 import BeautifulSoup


class GateOverflowScraper:

    BASE_URL = "https://gateoverflow.in"
    HEADERS = {"User-Agent": "Mozilla/5.0"}

    @staticmethod
    def get_year_pages(start_year=2020, end_year=2026):

        pages = []

        for year in range(start_year, end_year + 1):
            for set_no in range(1, 4):

                pages.append(
                    f"{GateOverflowScraper.BASE_URL}/tag/gatecse-{year}-set{set_no}"
                )

        return pages

    @staticmethod
    def get_question_links():

        links = set()
        start = 0

        while True:

            url = f"{GateOverflowScraper.TAG_URL}?start={start}"

            try:
                response = requests.get(
                    url,
                    headers=GateOverflowScraper.HEADERS,
                    timeout=15
                )

                if response.status_code != 200:
                    break

            except requests.RequestException:
                break

            soup = BeautifulSoup(response.text, "html.parser")

            page_links = []

            for a in soup.select(".qa-q-item-title a"):

                href = a.get("href")

                if not href:
                    continue

                if href.startswith("../"):
                    href = href.replace("../", "/")

                full_url = GateOverflowScraper.BASE_URL + href

                page_links.append(full_url)

            if not page_links:
                break

            links.update(page_links)

            print(f"Collected {len(links)} links so far...")

            start += 20

            time.sleep(0.3)

        return list(links)