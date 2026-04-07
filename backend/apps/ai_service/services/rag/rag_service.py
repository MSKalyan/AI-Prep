import re
from .vector_search import semantic_search


class RAGService:

    @staticmethod
    def retrieve_relevant_documents(query, user=None, exam_type="", top_k=5):

        # =========================
        # 🔥 DYNAMIC TOP-K
        # =========================
        query_len = len(query.split())

        if query_len <= 2:
            top_k = 3
        elif query_len <= 6:
            top_k = 5
        else:
            top_k = 8

        # =========================
        # 🔥 QUERY EXPANSION
        # =========================
        original_query = query

        if query_len <= 2:
            query = f"Define {query} in operating system"

        # =========================
        # 🔍 SEMANTIC SEARCH
        # =========================
        results = semantic_search(query, user=user, top_k=20)

        reranked = []
        seen_ids = set()

        query_words = set(original_query.lower().split())

        for chunk, score in results:

            # =========================
            # ❌ REMOVE DUPLICATES
            # =========================
            if chunk.id in seen_ids:
                continue
            seen_ids.add(chunk.id)

            content = chunk.content.lower()
            new_score = float(score)

            # =========================
            # 🔥 KEYWORD OVERLAP BOOST
            # =========================
            content_words = set(content.split())
            overlap = len(query_words & content_words)
            new_score += overlap * 0.1

            # =========================
            # 🔥 DEFINITION BOOST
            # =========================
            if "is a" in content or "defined as" in content:
                new_score += 0.4

            if query.lower() in content:
                new_score += 0.5

            # =========================
            # ❌ PENALIZE IRRELEVANT
            # =========================
            if "example" in content:
                new_score -= 0.3

            if "algorithm" in content:
                new_score -= 0.2

            if "implementation" in content:
                new_score -= 0.2

            # =========================
            # ❗ FILTER WEAK RESULTS
            # =========================
            if new_score < 0.25:
                continue

            reranked.append((chunk, new_score))

        # =========================
        # 🔥 NORMALIZATION
        # =========================
        if reranked:
            max_score = max(score for _, score in reranked)
            reranked = [(chunk, score / max_score) for chunk, score in reranked]

        # =========================
        # 🔥 FINAL SORT
        # =========================
        reranked.sort(key=lambda x: x[1], reverse=True)

        print(f"[RAG] Query: {query}")
        print(f"[RAG] Retrieved: {len(reranked)} chunks")

        return reranked[:top_k]

    # =====================================================
    # 🧠 BUILD CONTEXT FOR LLM (OPTIMIZED)
    # =====================================================

    @staticmethod
    def build_context(results, max_chars=1500):

        if not results:
            return ""

        context_parts = []
        seen_contents = set()
        total_chars = 0

        for i, (doc, score) in enumerate(results):

            content = doc.content.strip()

            # =========================
            # ❌ REMOVE NEAR DUPLICATES
            # =========================
            content_key = content[:100]

            if content_key in seen_contents:
                continue

            seen_contents.add(content_key)

            # =========================
            # 🔥 LIMIT CHUNK SIZE
            # =========================
            chunk_text = content[:300]

            chunk_block = f"""
[Source {i+1}]
Title: {doc.title}
Subject: {doc.subject}
Score: {round(score, 2)}

{chunk_text}
"""

            # =========================
            # 🔥 CHAR BUDGET CONTROL
            # =========================
            if total_chars + len(chunk_block) > max_chars:
                break

            context_parts.append(chunk_block)
            total_chars += len(chunk_block)

        return "\n\n".join(context_parts)