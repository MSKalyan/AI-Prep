import pdfplumber


def extract_text(file_path):

    if file_path.endswith(".pdf"):

        text = ""

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        return text

    elif file_path.endswith(".txt") or file_path.endswith(".md"):

        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    return ""