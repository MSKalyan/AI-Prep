from ..db.chroma_client import get_collection
from ..ingestion.embedder import get_embeddings


def keyword_score(query, text):
    query_words = set(query.lower().split())
    text_words = set(text.lower().split())

    # weighted match
    score = 0
    for word in query_words:
        if word in text_words:
            score += 2 if word in ["statistical", "mathematical", "empirical"] else 1

    return score


def hybrid_retrieve(query, top_k=5, exam_type=None, subject=None):
    collection = get_collection()

    query_embedding = get_embeddings([query])[0]

    where = {}
    if exam_type:
        where["exam_type"] = exam_type
    if subject:
        where["subject"] = subject

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k * 3,  # fetch more for reranking
        where=where if where else None,
        include=["documents", "metadatas", "distances"]
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    scored = []

    for doc, meta, dist in zip(docs, metas, distances):
        kw_score = keyword_score(query, meta.get("text", ""))

        # Combine scores
        final_score = (1 - dist) + (0.3 * kw_score)

        scored.append((final_score, doc, meta))

    # Sort by hybrid score
    scored.sort(key=lambda x: x[0], reverse=True)

    return [
        {"text": doc, "metadata": meta, "score": score}
        for score, doc, meta in scored[:top_k]
    ]