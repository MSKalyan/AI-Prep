import re
import requests
from bs4 import BeautifulSoup


class QuestionParserService:

    HEADERS = {"User-Agent": "Mozilla/5.0"}

    IGNORE_TAGS = {
        "easy",
        "medium",
        "hard",
        "multiple selects",
        "numerical answers",
        "normal",
        "one-mark",
        "two-mark",
    }

    @staticmethod
    def parse_question(url):

        try:
            response = requests.get(
                url,
                headers=QuestionParserService.HEADERS,
                timeout=10
            )

            if response.status_code != 200:
                return [], None, None

        except requests.RequestException:
            return [], None, None

        soup = BeautifulSoup(response.text, "html.parser")

        year = None
        marks = 1
        topic_candidates = set()

        # -------- Extract category --------
        category = soup.select_one(".qa-category-link")

        if category:
            text = category.get_text(strip=True).lower()
            if text:
                topic_candidates.add(text)

        # -------- Extract tags --------
        tags = soup.select(".qa-tag-link")

        for tag in tags:

            text = tag.get_text(strip=True).lower()

            if not text:
                continue

            # detect marks
            if "two-mark" in text or "two marks" in text:
                marks = 2

            if "one-mark" in text or "one mark" in text:
                marks = 1

            # skip irrelevant tags
            if text in QuestionParserService.IGNORE_TAGS:
                continue

            topic_candidates.add(text)

        # -------- Extract year from URL --------
        match = re.search(r"gate-cse-(\d{4})", url)

        if match:
            year = int(match.group(1))

        return list(topic_candidates), year, marks