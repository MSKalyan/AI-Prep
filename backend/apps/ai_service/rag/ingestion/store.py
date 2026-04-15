import uuid
from ..db.chroma_client import get_collection
from .embedder import get_embeddings

def store_chunks(chunks, metadata):
    collection = get_collection()

    ids = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        ids.append(f"{metadata['document_id']}_{i}")

        metadatas.append({
            "document_id": metadata["document_id"],
            "title": metadata.get("title", ""),
            "subject": metadata.get("subject", ""),
            "exam_type": metadata.get("exam_type", ""),
            "topic": metadata.get("topic", ""),
            "chunk_index": i,
            "text": chunk[:500]  # IMPORTANT for keyword search
        })

    embeddings = get_embeddings(chunks)

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas
    )