import re

from .embedding_service import generate_embedding
from .faiss_store import FAISSVectorStore
from ...models import Document

STOPWORDS = {"what", "is", "the", "in", "of", "a", "an", "and", "to"}


def clean_text(text):
    return re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())


def extract_keywords(query):
    query = clean_text(query)
    words = query.split()
    return [w for w in words if w not in STOPWORDS and len(w) > 2]


def semantic_search(query, top_k=20):

    # =========================
    # 🔍 STEP 1 — KEYWORDS
    # =========================
    keywords = extract_keywords(query)

    keyword_results = []

    if keywords:
        query_filter = None

        for word in keywords:
            condition = Document.objects.filter(
                parent_document__isnull=False,
                content__icontains=word
            )

            query_filter = condition if query_filter is None else query_filter | condition

        keyword_chunks = query_filter.distinct()[:20]

        for chunk in keyword_chunks:
            content = clean_text(chunk.content or "")
            score = 0.0

            match_count = sum(1 for word in keywords if word in content)

            if match_count > 0:
                score += match_count * 1.0

                # 🔥 definition boost
                if "is a" in content or "defined as" in content:
                    score += 0.5

                keyword_results.append((chunk, score))

    # =========================
    # 🧠 STEP 2 — VECTOR SEARCH
    # =========================
    query_embedding = generate_embedding(query,is_query=True)

    store = FAISSVectorStore()
    raw_results = store.search(query_embedding, top_k=top_k)

    vector_results = []

    if raw_results:
        first = raw_results[0]

        if hasattr(first[0], "id"):
            vector_results = raw_results
        else:
            chunk_ids = [cid for cid, _ in raw_results]
            chunks = Document.objects.filter(id__in=chunk_ids)
            chunk_map = {c.id: c for c in chunks}

            for cid, score in raw_results:
                chunk = chunk_map.get(cid)
                if chunk:
                    vector_results.append((chunk, score))

    # =========================
    # 🔀 STEP 3 — MERGE (SOFT LOGIC)
    # =========================
    combined = {}

    for chunk, score in keyword_results:
        combined[chunk.id] = (chunk, score + 2.0)

    for chunk, score in vector_results:

        if not hasattr(chunk, "content"):
            continue

        content = clean_text(chunk.content or "")

        # 🔥 SOFT keyword scoring
        match_count = sum(1 for word in keywords if word in content)

        if match_count == 0:
            score *= 0.3   # reduce but DO NOT drop
        else:
            score += match_count * 0.2

        if chunk.id in combined:
            existing_score = combined[chunk.id][1]
            combined[chunk.id] = (chunk, existing_score + score)
        else:
            combined[chunk.id] = (chunk, score)

    # =========================
    # 🔥 FINAL FILTER (RELAXED)
    # =========================
    filtered = []

    for chunk, score in combined.values():
        if score < 0.2:   # only remove extremely weak results
            continue
        filtered.append((chunk, score))

    # =========================
    # SORT
    # =========================
    filtered.sort(key=lambda x: x[1], reverse=True)

    return filtered[:top_k]