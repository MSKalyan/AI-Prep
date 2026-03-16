import re
import requests
from bs4 import BeautifulSoup


class QuestionParserService:

    HEADERS = {
        "User-Agent": "Mozilla/5.0"
    }

    IGNORE_TAGS = {
        "easy",
        "medium",
        "hard",
        "multiple-selects",
        "numerical-answers",
        "normal",
        "one-mark",
        "two-mark",
    }

    # ---------------------------------------------------
    # Parse question from web page (GATEOverflow style)
    # ---------------------------------------------------

    @staticmethod
    def parse_question(url):

        try:
            response = requests.get(
                url,
                headers=QuestionParserService.HEADERS,
                timeout=10
            )

            if response.status_code != 200:
                return "", [], None, None

        except requests.RequestException:
            return "", [], None, None

        soup = BeautifulSoup(response.text, "html.parser")

        # -------------------------
        # Question text
        # -------------------------

        question_text = ""

        question_div = soup.select_one(".qa-q-view-content")

        if question_div:
            question_text = question_div.get_text(" ", strip=True)

        # -------------------------
        # Extract topic tags
        # -------------------------

        topic_candidates = set()

        for tag in soup.select(".qa-tag-link"):

            text = tag.get_text(strip=True).lower()

            if not text:
                continue

            if text in QuestionParserService.IGNORE_TAGS:
                continue

            if re.match(r"gatecse-\d{4}", text):
                continue

            topic_candidates.add(text)

        # -------------------------
        # Extract year
        # -------------------------

        year = None

        match = re.search(r"gate-cse-(\d{4})", url)

        if match:
            year = int(match.group(1))

        # -------------------------
        # Extract marks
        # -------------------------

        marks = 1

        page_text = soup.get_text().lower()

        if "2 mark" in page_text or "two mark" in page_text:
            marks = 2

        if "1 mark" in page_text or "one mark" in page_text:
            marks = 1

        return question_text, list(topic_candidates), year, marks

    # ---------------------------------------------------
    # Clean PDF question artifacts
    # ---------------------------------------------------

    @staticmethod
    def clean_question(text):

        text = re.sub(
            r"Organising Institute:.*?Page \d+ of \d+",
            "",
            text
        )

        text = re.sub(
            r"Computer Science and Information Technology \(CS\d\)",
            "",
            text
        )

        text = re.sub(r"\s+", " ", text)

        return text.strip()

    # ---------------------------------------------------
    # Split PDF text into questions
    # ---------------------------------------------------



    @staticmethod
    def split_questions(text):

        # normalize newlines
        text = text.replace("\n", " ")

        # detect multiple question formats
        pattern = r"(?:Q\.?\s?\d+|\b\d+\.)"

        parts = re.split(pattern, text)

        questions = []

        for part in parts:

            cleaned = part.strip()

            if len(cleaned) > 120:  # avoid small fragments
                questions.append(cleaned)

        return questions