import requests
from bs4 import BeautifulSoup


class GateOverflowScraper:

    BASE_URL = "https://gateoverflow.in"
    HEADERS = {"User-Agent": "Mozilla/5.0"}

    @staticmethod
    def get_year_pages(start=2020, end=2024):

        pages = []

        for year in range(start, end + 1):
            pages.append(f"{GateOverflowScraper.BASE_URL}/tag/gate-cse-{year}")

        return pages

    @staticmethod
    def get_question_links(page):

        links = set()

        try:
            response = requests.get(
                page,
                headers=GateOverflowScraper.HEADERS,
                timeout=15
            )

            if response.status_code != 200:
                return []

        except requests.RequestException:
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        # FIXED SELECTOR
        for a in soup.select("a.qa-q-item-title-link"):

            href = a.get("href")

            if not href:
                continue

            full_url = GateOverflowScraper.BASE_URL + href

            links.add(full_url)

        return list(links)