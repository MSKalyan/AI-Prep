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

        response = requests.get(url, headers=QuestionParserService.HEADERS)

        soup = BeautifulSoup(response.text, "html.parser")

        tags = [t.text.strip() for t in soup.select(".qa-tag-link")]

        topic = None
        year = None
        marks = 1

        for tag in tags:

            tag_lower = tag.lower()

            # marks
            if "two-mark" in tag_lower:
                marks = 2

            if "one-mark" in tag_lower:
                marks = 1

            # year

            if "gatecse" in tag_lower:

                match = re.search(r"\d{4}", tag_lower)

                if match:
                    year = int(match.group())
            # topic
            if (
                tag_lower not in QuestionParserService.IGNORE_TAGS
                and "gate" not in tag_lower
            ):
                topic = tag_lower.replace("-", " ").title()

        return topic, year, marks