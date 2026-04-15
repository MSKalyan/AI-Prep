from ..retrieval.hybrid_retriever import hybrid_retrieve
from ..llm.generator import generate_answer, generate_summary


class RAGService:
    def ingest_document(self, document):
        from ..ingestion.loader import load_pdf
        from ..ingestion.chunker import chunk_text
        from ..ingestion.store import store_chunks

        if document.file:
            text = load_pdf(document.file.path)
        else:
            text = document.content

        if not text or len(text.strip()) < 50:
            raise ValueError("Document content is empty")

        chunks = chunk_text(text)

        store_chunks(
            chunks,
            metadata={
                "document_id": document.id,
                "title": document.title,
                "subject": document.subject,
                "exam_type": document.exam_type,
                "topic": document.topic,
            },
        )

        return True

    # ✅ ADD THIS METHOD
    def query(self, query, exam_type=None, subject=None, top_k=5):
        query_text = query.strip().lower()
        candidate_k = top_k
        if query_text.startswith(("what is", "define", "explain", "describe", "state")):
            candidate_k = max(top_k, 12)

        entries = hybrid_retrieve(
            query=query,
            top_k=candidate_k,
            exam_type=exam_type,
            subject=subject,
        )

        if not entries:
            return {
                "answer": "No relevant information found in documents.",
                "documents": [],
            }

        filtered_entries = [entry for entry in entries if entry["text"].strip()]

        if not filtered_entries:
            return {
                "answer": "No relevant information found in documents.",
                "documents": [],
            }

        hierarchical_context = self._build_hierarchical_context(query, filtered_entries)
        context = "\n\n".join(hierarchical_context[:5])

        if not context.strip():
            context = "\n\n".join([entry["text"] for entry in filtered_entries[:5]])

        answer = generate_answer(query, context)

        return {
            "answer": answer,
            "documents": [entry["text"] for entry in filtered_entries[:5]],
        }

    def _group_entries_by_document(self, chunk_entries, window_size):
        grouped_batches = []
        current_doc = None
        current_group = []

        sorted_entries = sorted(
            chunk_entries,
            key=lambda item: (
                item["metadata"].get("document_id"),
                item["metadata"].get("chunk_index", 0),
            ),
        )

        for entry in sorted_entries:
            document_id = entry["metadata"].get("document_id")
            if current_doc is None:
                current_doc = document_id
            if document_id != current_doc or len(current_group) >= window_size:
                if current_group:
                    grouped_batches.append(current_group)
                current_group = []
                current_doc = document_id
            current_group.append(entry)

        if current_group:
            grouped_batches.append(current_group)

        return grouped_batches

    def _summarize_group(self, group, query):
        group_text = "\n\n".join(entry["text"] for entry in group)
        if len(group_text.split()) <= 120:
            return group_text
        summary = generate_summary(group_text, query).strip()
        if not summary or len(summary) < 40:
            return group_text[:800]
        return summary

    def _build_hierarchical_context(
        self, query, chunk_entries, window_size=3, max_groups=3
    ):
        grouped_batches = self._group_entries_by_document(chunk_entries, window_size)
        summaries = []
        for group in grouped_batches[:max_groups]:
            if group:
                summaries.append(self._summarize_group(group, query))
        return summaries
