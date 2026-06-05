import pytest
import requests

from apps.roadmap.services.pyq.question_parser_service import QuestionParserService


def _mock_response(status_code=200, text=""):
    class MockResponse:
        def __init__(self, status, text):
            self.status_code = status
            self.text = text
        def raise_for_status(self):
            pass
    return MockResponse(status_code, text)


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
    def _mock_safe_get(*args, **kwargs):
        return _mock_response(200, html)

    monkeypatch.setattr(
        "apps.roadmap.services.pyq.question_parser_service.safe_get",
        _mock_safe_get,
    )

    question, topics, year, marks = QuestionParserService.parse_question(
        "https://example.com/gate-cse-2024/question/1"
    )

    assert question == "What is complexity?"
    assert topics == ["trees"]
    assert year == 2024
    assert marks == 2


def test_parse_question_returns_empty_on_non_200(monkeypatch):
    def _mock_safe_get(*args, **kwargs):
        return _mock_response(404, "")

    monkeypatch.setattr(
        "apps.roadmap.services.pyq.question_parser_service.safe_get",
        _mock_safe_get,
    )
    assert QuestionParserService.parse_question("https://example.com/x") == ("", [], None, None)


def test_parse_question_returns_empty_on_request_exception(monkeypatch):
    def _raise(*args, **kwargs):
        raise requests.RequestException("network down")

    monkeypatch.setattr(
        "apps.roadmap.services.pyq.question_parser_service.safe_get",
        _raise,
    )
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