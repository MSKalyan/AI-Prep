import requests
from bs4 import BeautifulSoup


class GateOverflowScraper:

    BASE_URL = "https://gateoverflow.in"

    HEADERS = {
        "User-Agent": "Mozilla/5.0"
    }

    @staticmethod
    def get_question_links(tag):

        links = set()
        start = 0

        while True:

            if start == 0:
                url = f"{GateOverflowScraper.BASE_URL}/tag/{tag}"
            else:
                url = f"{GateOverflowScraper.BASE_URL}/tag/{tag}?start={start}"

            response = requests.get(url, headers=GateOverflowScraper.HEADERS)

            soup = BeautifulSoup(response.text, "html.parser")

            page_links = []

            for a in soup.find_all("a", href=True):

                href = a["href"]

                if "gate-cse" in href:

                    # remove ../
                    href = href.replace("../", "/")

                    full_url = GateOverflowScraper.BASE_URL + href

                    page_links.append(full_url)

            page_links = list(set(page_links))

            if not page_links:
                break

            links.update(page_links)

            start += 20

        return list(links)