from ...models import Document
from .text_cleaner import clean_text


def clean_document(document: Document):

    cleaned = clean_text(document.content)

    document.content = cleaned
    document.save()

    return document