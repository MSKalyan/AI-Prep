from ..models import Document
from .chunk_service import chunk_text


def create_chunks(document):

    chunks = chunk_text(document.content)

    created_chunks = []

    for index, chunk in enumerate(chunks):

        chunk_doc = Document.objects.create(
            title=document.title,
            content=chunk,
            subject=document.subject,
            topic=document.topic,
            exam_type=document.exam_type,
            document_type=document.document_type,
            source_type=document.source_type,
            parent_document=document,
            chunk_index=index
        )

        created_chunks.append(chunk_doc)

    document.processed = True
    document.save()

    return created_chunks