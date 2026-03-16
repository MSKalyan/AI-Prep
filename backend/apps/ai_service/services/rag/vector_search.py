import numpy as np
from ...models import Document
from .embedding_service import generate_embedding


def cosine_similarity(vec1, vec2):

    vec1 = np.array(vec1)
    vec2 = np.array(vec2)

    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def semantic_search(query, top_k=5):

    query_embedding = generate_embedding(query)

    chunks = Document.objects.filter(
        embedding__isnull=False,
        parent_document__isnull=False
    )
    results = []

    for chunk in chunks:

        score = cosine_similarity(query_embedding, chunk.embedding)

        results.append((chunk, score))

    results.sort(key=lambda x: x[1], reverse=True)

    return results[:top_k]