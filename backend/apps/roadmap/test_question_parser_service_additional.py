from types import SimpleNamespace

import pytest
import requests

from apps.roadmap.services.pyq.question_parser_service import QuestionParserService


def _mock_response(status_code=200, text=""):
    response = SimpleNamespace(status_code=status_code, text=text)
    response.raise_for_status = lambda: None
    return response


@pytest.mark.parametrize(
    "text,expected",
    [
        ("abc 12. something", True),
        ("abc 12 something", False),
        ("1. start", True),
        ("no digits here", False),
    ],
)
def test_contains_number_dot(text, expected):
    assert QuestionParserService._contains_number_dot(text) is expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("this is a two mark question", 2),
        ("this is a 2 mark question", 2),
        ("regular one mark", 1),
    ],
)
def test_parse_marks_variants(text, expected):
    assert QuestionParserService._parse_marks(text) == expected


def test_parse_question_success_with_filters_and_year(monkeypatch):
    html = """
    <html><body>
      <div class="qa-q-view-content">What is complexity?</div>
      <a class="qa-tag-link">easy</a>
      <a class="qa-tag-link">Trees</a>
      <a class="qa-tag-link">gatecse-2024</a>
      <div>this is a two mark problem</div>
    </body></html>
    """
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: _mock_response(200, html))

    question, topics, year, marks = QuestionParserService.parse_question(
        "https://example.com/gate-cse-2024/question/1"
    )

    assert question == "What is complexity?"
    assert topics == ["trees"]
    assert year == 2024
    assert marks == 2


def test_parse_question_returns_empty_on_non_200(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: _mock_response(404, ""))
    assert QuestionParserService.parse_question("https://example.com/x") == ("", [], None, None)


def test_parse_question_returns_empty_on_request_exception(monkeypatch):
    def _raise(*args, **kwargs):
        raise requests.RequestException("network down")

    monkeypatch.setattr(requests, "get", _raise)
    assert QuestionParserService.parse_question("https://example.com/x") == ("", [], None, None)


def test_clean_question_removes_boilerplate_and_normalizes_spaces():
    raw = (
        "Organising Institute: XYZ something Page 3 of 20\n"
        "Computer Science and Information Technology (CS1)\n"
        "Q. What is DBMS?"
    )
    cleaned = QuestionParserService.clean_question(raw)
    assert "Organising Institute" not in cleaned
    assert "Computer Science and Information Technology" not in cleaned
    assert cleaned == "Q. What is DBMS?"


def test_split_questions_keeps_only_meaningful_question_length():
    long_part = "A" * 130
    short_part = "B" * 30
    text = f"Q1 {short_part} 2. {long_part} Q3 {long_part}"
    result = QuestionParserService.split_questions(text)
    assert all(len(x) > 120 for x in result)
    assert len(result) >= 2


def test_parse_pdf_page_text_parses_questions_options_and_marks():
    text = "\n".join(
        [
            "Q. 1",
            "What is OS?",
            "(A) Option A",
            "(B) Option B",
            "2 mark",
            "Q. 2. What is DBMS?",
            "A. Data",
            "B. Control",
        ]
    )
    questions = QuestionParserService.parse_pdf_page_text(text)
    assert len(questions) == 2
    assert questions[0]["number"] == 1
    assert questions[0]["marks"] == 2
    assert questions[0]["options"]["A"] == "Option A"
    assert questions[1]["number"] == 2
    assert questions[1]["options"]["B"] == "Control"


def test_extract_answer_key_from_text_supports_multiple_formats():
    text = "\n".join(
        [
            "1 MCQ X A",
            "2 NAT X 12.5",
            "3 C",
            "4 MSQ Y D",
        ]
    )
    answers = QuestionParserService.extract_answer_key_from_text(text)
    assert answers == {1: "A", 3: "C", 4: "D"}


def test_parse_pdf_complete_matches_answers_to_questions():
    q_page = "\n".join(["Q. 1. First question", "(A) A1", "(B) B1", "Q. 2. Second question"])
    answer_page = "\n".join(["Q.NO ANSWER KEY", "1 A", "2 B"])
    blob = f"{q_page}\n\n----\n\n{answer_page}"
    questions = QuestionParserService.parse_pdf_complete(blob)
    assert len(questions) == 2
    assert questions[0]["correct_answer"] == "A"
    assert questions[1]["correct_answer"] == "B"


def test_parse_pdf_questions_uses_last_pages_as_answer_key():
    text = "\n\n".join(
        [
            "Q. 1. First\n(A) A\n(B) B",
            "Q. 2. Second\n(A) A2\n(B) B2",
            "Random footer",
            "ANSWER KEY\n1 A\n2 B",
        ]
    )
    questions = QuestionParserService.parse_pdf_questions(text)
    assert len(questions) == 1
    assert questions[0]["number"] == 1
    assert questions[0]["correct_answer"] == "A"
