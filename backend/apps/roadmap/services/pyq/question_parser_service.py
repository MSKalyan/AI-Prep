import re
import requests
from bs4 import BeautifulSoup
from apps.utils.retry_utils import safe_get


class QuestionParserService:
    HEADERS = {"User-Agent": "Mozilla/5.0"}

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

    MARK_TWO = "2 mark"
    MARK_TWO_ALT = "two mark"

    @staticmethod
    def _contains_number_dot(text: str) -> bool:
        i = 0
        n = len(text)
        while i < n:
            if not text[i].isdigit():
                i += 1
                continue

            j = i + 1
            while j < n and text[j].isdigit():
                j += 1

            if j < n and text[j] == ".":
                return True

            i = j

        return False

    @staticmethod
    def _parse_marks(page_text):
        if (
            QuestionParserService.MARK_TWO in page_text
            or QuestionParserService.MARK_TWO_ALT in page_text
        ):
            return 2
        return 1

    @staticmethod
    def parse_question(url):
        try:
            response = safe_get(url, timeout=10)
        except Exception:
            return "", [], None, None

        if response.status_code != 200:
            return "", [], None, None

        soup = BeautifulSoup(response.text, "html.parser")

        question_text = ""

        question_div = soup.select_one(".qa-q-view-content")

        if question_div:
            question_text = question_div.get_text(" ", strip=True)

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

        year = None

        match = re.search(r"gate-cse-(\d{4})", url)

        if match:
            year = int(match.group(1))

        marks = QuestionParserService._parse_marks(soup.get_text().lower())

        return question_text, list(topic_candidates), year, marks

    @staticmethod
    def clean_question(text):

        text = re.sub(r"Organising Institute:.*?Page \d+ of \d+", "", text)

        text = re.sub(r"Computer Science and Information Technology \(CS\d\)", "", text)

        text = re.sub(r"\s+", " ", text)

        return text.strip()

    @staticmethod
    def split_questions(text):

        text = text.replace("\n", " ")

        pattern = r"(?:Q\.?\s?\d+|\b\d+\.)"

        parts = re.split(pattern, text)

        questions = []

        for part in parts:
            cleaned = part.strip()

            if len(cleaned) > 120:
                questions.append(cleaned)

        return questions

    @staticmethod
    def parse_pdf_page_text(text):
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        questions = []
        current_q = None

        for line in lines:
            current_q = QuestionParserService._process_line(line, current_q, questions)

        if current_q and current_q.get("question_text"):
            questions.append(current_q)

        return questions

    @staticmethod
    def _process_line(line, current_q, questions):
        line = line.strip()
        if not line:
            return current_q

        q_match = re.match(r"Q\.?\s*(\d+)\.?\s*$", line, re.IGNORECASE)
        if q_match:
            return QuestionParserService._start_question(
                int(q_match.group(1)), current_q, questions
            )

        q_with_text_match = re.match(r"Q\.?\s*(\d+)\.?\s+(.+)", line, re.IGNORECASE)
        if q_with_text_match:
            return QuestionParserService._start_question_with_text(
                q_with_text_match, current_q, questions
            )

        if current_q is None:
            return None

        current_q = QuestionParserService._parse_options(line, current_q)
        if current_q and QuestionParserService.MARK_TWO in line.lower():
            current_q["marks"] = 2

        return QuestionParserService._append_question_text(line, current_q)

    @staticmethod
    def _start_question(q_num, current_q, questions):
        if current_q and current_q.get("question_text"):
            questions.append(current_q)
        return {
            "number": q_num,
            "question_text": "",
            "options": {},
            "correct_answer": None,
            "question_type": "mcq",
            "marks": 1,
        }

    @staticmethod
    def _start_question_with_text(match, current_q, questions):
        if current_q and current_q.get("question_text"):
            questions.append(current_q)
        return {
            "number": int(match.group(1)),
            "question_text": match.group(2).strip(),
            "options": {},
            "correct_answer": None,
            "question_type": "mcq",
            "marks": 1,
        }

    @staticmethod
    def _parse_options(line, current_q):
        for pattern in [r"\(([A-D])\)\s+(.+)", r"^([A-D])\.\s+(.+)"]:
            opt_match = re.match(pattern, line)
            if opt_match:
                current_q["options"][opt_match.group(1).upper()] = opt_match.group(
                    2
                ).strip()
                break
        return current_q

    @staticmethod
    def _append_question_text(line, current_q):
        if len(current_q["options"]) < 2:
            current_q["question_text"] = (
                (current_q["question_text"] + " " + line)
                if current_q["question_text"]
                else line
            )
        return current_q

    @staticmethod
    def extract_answer_key_from_text(text):
        """Extract answer key from GATE answer key page."""

        answers = {}

        lines = text.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            match = re.match(
                r"^\s*(\d+)\s+(MCQ|NAT|MSQ)\s+\w+\s+([A-Z0-9.\-]+)\s*$",
                line,
                re.IGNORECASE,
            )
            if match:
                q_num = int(match.group(1))
                answer = match.group(3).strip().upper()
                if answer in ["A", "B", "C", "D"]:
                    answers[q_num] = answer
                continue

            simple_match = re.match(r"^\s*(\d+)\s+([A-D])\s*$", line)
            if simple_match:
                q_num = int(simple_match.group(1))
                answer = simple_match.group(2).upper()
                answers[q_num] = answer

        return answers

    @staticmethod
    def parse_pdf_complete(text, expected_year=None):
        """Complete PDF parsing with answer key extraction."""

        pages = text.split("\n\n----\n\n")

        if len(pages) <= 1:
            pages = text.split("\n\n")

        answer_key_pages = []
        question_pages = []

        for i, page in enumerate(pages):
            page_upper = page.upper()
            if "ANSWER" in page_upper or "KEY" in page_upper or "Q.NO" in page_upper:
                answer_key_pages.append((i, page))
            elif "Q." in page or QuestionParserService._contains_number_dot(page):
                question_pages.append((i, page))

        all_answers = {}
        for _, answer_page in answer_key_pages:
            answers = QuestionParserService.extract_answer_key_from_text(answer_page)
            if answers:
                all_answers.update(answers)

        all_questions = []
        for _, q_page in question_pages:
            questions = QuestionParserService.parse_pdf_page_text(q_page)
            all_questions.extend(questions)

        for q in all_questions:
            q_num = q.get("number")
            if q_num and q_num in all_answers:
                q["correct_answer"] = all_answers[q_num]

        return all_questions

    @staticmethod
    def extract_questions_from_pdf_text(text):
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        structured_questions = []
        current_question = None

        for line in lines:
            current_question = QuestionParserService._parse_question_line(
                line, current_question, structured_questions
            )

        if current_question and current_question.get("question_text"):
            structured_questions.append(current_question)

        return structured_questions

    @staticmethod
    def _parse_question_line(line, current_question, structured_questions):
        line = line.strip()
        if not line:
            return current_question

        q_match = re.match(r"Q\.?\s*(\d+)\.?\s*(.*)", line, re.IGNORECASE)
        if q_match:
            return QuestionParserService._handle_question_start(
                q_match, current_question, structured_questions
            )

        if current_question is None:
            return None

        current_question = QuestionParserService._parse_question_options(
            line, current_question
        )
        return QuestionParserService._append_to_question_text(line, current_question)

    @staticmethod
    def _handle_question_start(q_match, current_question, structured_questions):
        if current_question and current_question.get("question_text"):
            structured_questions.append(current_question)
        return {
            "number": int(q_match.group(1)),
            "question_text": q_match.group(2).strip(),
            "options": {},
            "correct_answer": None,
            "question_type": "mcq",
            "marks": 1,
        }

    @staticmethod
    def _parse_question_options(line, current_question):
        for pattern in [r"\(([A-D])\)\s*(.+)", r"^([A-D])\.\s+(.+)"]:
            option_match = re.match(pattern, line)
            if option_match:
                current_question["options"][option_match.group(1).upper()] = (
                    option_match.group(2).strip()
                )
                break
        return current_question

    @staticmethod
    def _append_to_question_text(line, current_question):
        if current_question["question_text"]:
            current_question["question_text"] += " " + line
        else:
            current_question["question_text"] = line
        return current_question

    @staticmethod
    def extract_answer_key(text):
        """Extract answer key from GATE answer key section."""

        answers = {}

        lines = text.split("\n")

        in_answer_section = False

        for line in lines:
            line = line.upper().strip()

            if "ANSWER KEY" in line or "ANSWERS" in line or "Q.NO" in line:
                in_answer_section = True
                continue

            if not in_answer_section:
                continue

            match = re.match(r"^\s*(\d+)\s+([A-D])\s*$", line)
            if match:
                q_num = int(match.group(1))
                answer = match.group(2).strip()
                answers[q_num] = answer
                continue

            match = re.match(
                r"^\s*(\d+)\s+(MCQ|NAT|MSQ)\s+[A-Z]+\s+([A-Z0-9.\-]+)",
                line,
                re.IGNORECASE,
            )
            if match:
                q_num = int(match.group(1))
                answer = match.group(3).strip()
                if answer in ["A", "B", "C", "D"]:
                    answers[q_num] = answer

        return answers

    @staticmethod
    def parse_pdf_questions(text):
        """Complete PDF parsing: extract questions and match with answers."""

        last_pages = []
        pages = text.split("\n\n")

        if len(pages) > 3:
            last_pages = pages[-3:]
            main_text = "\n\n".join(pages[:-3])
        else:
            main_text = text

        answers = {}
        for page in last_pages:
            page_answers = QuestionParserService.extract_answer_key(page)
            if page_answers:
                answers.update(page_answers)
                break

        questions = QuestionParserService.extract_questions_from_pdf_text(main_text)

        for q in questions:
            q_num = q.get("number")
            if q_num and q_num in answers:
                q["correct_answer"] = answers[q_num]

        return questions
