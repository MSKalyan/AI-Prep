from ..models import Document
from .embedding_service import generate_embedding


def embed_document_chunks(document):

    chunks = Document.objects.filter(parent_document=document)

    for chunk in chunks:

        if chunk.embedding:
            continue

        vector = generate_embedding(chunk.content)

        chunk.embedding = vector

        chunk.save()

    return chunks.count()