from ...models import Document
from .embedding_service import generate_embedding
from .faiss_store import FAISSVectorStore


def embed_document_chunks(document):

    chunks = Document.objects.filter(parent_document=document)

    new_chunks = []

    for chunk in chunks:

        if chunk.embedding:
            continue

        vector = generate_embedding(chunk.content)

        chunk.embedding = vector
        chunk.save()

        new_chunks.append(chunk)

    # ✅ Update FAISS
    if new_chunks:
        store = FAISSVectorStore()
        store.add_embeddings(new_chunks)

    return len(new_chunks)