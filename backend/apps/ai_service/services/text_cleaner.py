import re


def clean_text(text: str) -> str:
    """
    Normalize extracted text for downstream processing.
    """

    if not text:
        return ""

    # Remove extra whitespace and newlines
    text = re.sub(r"\s+", " ", text)

    # Remove non-printable characters
    text = re.sub(r"[^\x20-\x7E]+", " ", text)

    # Trim leading/trailing spaces
    text = text.strip()

    return text