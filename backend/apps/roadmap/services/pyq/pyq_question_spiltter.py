import re

def split_questions(text):

    pattern = r"Q\d+\."
    chunks = re.split(pattern, text)

    questions = []

    for chunk in chunks:
        cleaned = chunk.strip()
        if len(cleaned) > 40:
            questions.append(cleaned)

    return questions