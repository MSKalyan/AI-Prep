import uuid
from typing import Dict, List, Any

from ..db.chroma_client import get_collection
from .embedder import get_embeddings


def store_chunks(chunks: List[str], metadata: Dict[str, Any]) -> None:
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
            "text": chunk[:500]
        })

    embeddings = get_embeddings(chunks)

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas
    )