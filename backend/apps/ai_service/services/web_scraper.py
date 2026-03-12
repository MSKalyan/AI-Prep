import requests
import re
from bs4 import BeautifulSoup


def scrape_webpage(url):

    try:
        headers = {"User-Agent": "Mozilla/5.0"}

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            raise Exception(f"Website returned status {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        paragraphs = soup.find_all("p")

        text = " ".join(p.get_text(" ", strip=True) for p in paragraphs)
        text = re.sub(r"\s+", " ", text)
        return text

    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch webpage: {str(e)}")