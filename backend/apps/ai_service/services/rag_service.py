


from linecache import cache

from polars import List

from backend.apps.ai_service.models import Document


class RAGService:

    @staticmethod
    def retrieve_relevant_documents(query: str, context: str = "",
                                    exam_type: str = "", top_k: int = 5) -> List[Document]:

        safe_query = query.replace("?", "").replace(":", "")
        safe_context = context.replace(":", "")
        safe_exam = exam_type.replace(":", "")

        cache_key = f"rag_docs:{safe_query}:{safe_context}:{safe_exam}"

        cached_docs = cache.get(cache_key)

        if cached_docs:
            return cached_docs

        documents = Document.objects.all()

        if exam_type:
            documents = documents.filter(exam_type=exam_type)

        if context:
            documents = documents.filter(subject__icontains=context) | \
                        documents.filter(topic__icontains=context)

        query_terms = query.lower().split()
        scored_docs = []

        for doc in documents[:100]:
            content_lower = doc.content.lower()
            title_lower = doc.title.lower()

            score = sum(
                content_lower.count(term) + title_lower.count(term) * 2
                for term in query_terms
            )

            if score > 0:
                scored_docs.append((score, doc))

        scored_docs.sort(reverse=True, key=lambda x: x[0])
        relevant_docs = [doc for score, doc in scored_docs[:top_k]]

        cache.set(cache_key, relevant_docs, 3600)
        return relevant_docs

    @staticmethod
    def build_context(documents: List[Document]) -> str:

        if not documents:
            return "No relevant context found in knowledge base."

        context_parts = []

        for i, doc in enumerate(documents, 1):
            context_parts.append(
                f"[Document {i}]\n"
                f"Title: {doc.title}\n"
                f"Subject: {doc.subject}\n"
                f"Content: {doc.content[:500]}...\n"
            )

        return "\n".join(context_parts)

