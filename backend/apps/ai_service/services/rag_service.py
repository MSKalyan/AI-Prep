from .vector_search import semantic_search
from ..models import Document



class RAGService:

    @staticmethod
    def retrieve_relevant_documents(query, context="", exam_type="", top_k=3):

        # run semantic search
        results = semantic_search(query, top_k=10)  # retrieve more first

        filtered_docs = []

        for chunk, score in results:

            # skip weak similarity
            if score < 0.35:
                continue

            # ensure we only use chunk documents
            if not chunk.parent_document_id:
                continue

            # optional exam filtering
            if exam_type and chunk.exam_type != exam_type:
                continue

            # attach score for later use
            chunk.score = score

            filtered_docs.append(chunk)

        # return best k documents
        return filtered_docs[:top_k]
    # =====================================================
    # BUILD CONTEXT FOR LLM
    # =====================================================
    @staticmethod
    def build_context(documents):

        if not documents:
            return ""

        context_parts = []

        for doc in documents:
            context_parts.append(
                f"""
Title: {doc.title}
Subject: {doc.subject}

Content:
{doc.content}
"""
            )

        return "\n\n".join(context_parts)
    
  