import os
import json
import time
import openai
from typing import List, Dict, Any
from django.conf import settings
from django.core.cache import cache
from groq import Groq

from .models import Document, Conversation, Message, AIUsageLog


# =====================================================
# RAG SERVICE
# =====================================================

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


# =====================================================
# AI SERVICE
# =====================================================

class AIService:

    def __init__(self):

        self.ai_mode = os.getenv("AI_MODE", "mock")
        self.groq_api_key = os.getenv("GROQ_API_KEY")

        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS

        if self.ai_mode == "groq" and self.groq_api_key:
            self.groq = Groq(api_key=self.groq_api_key)

    # =====================================================
    # ASK AI
    # =====================================================

    def ask_ai(self, user, question: str, context: str = "",
               conversation_id: int = None, exam_type: str = ""):

        start_time = time.time()

        try:

            relevant_docs = RAGService.retrieve_relevant_documents(
                query=question,
                context=context,
                exam_type=exam_type,
                top_k=settings.TOP_K_RESULTS
            )

            knowledge_context = RAGService.build_context(relevant_docs)

            if conversation_id:
                conversation = Conversation.objects.get(
                    id=conversation_id,
                    user=user
                )
            else:
                conversation = Conversation.objects.create(
                    user=user,
                    title=question[:100],
                    context=context
                )

            previous_messages = list(
                conversation.messages.all().order_by('-created_at')[:5]
            )[::-1]

            system_prompt = self._build_system_prompt(context, exam_type)
            user_prompt = self._build_user_prompt(question, knowledge_context)

            messages = [{"role": "system", "content": system_prompt}]

            for msg in previous_messages:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

            messages.append({
                "role": "user",
                "content": user_prompt
            })

            response = self._call_llm(messages)

            answer = response['choices'][0]['message']['content']
            usage = response.get('usage', {})

            Message.objects.create(
                conversation=conversation,
                role='user',
                content=question
            )

            Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=answer,
                retrieved_documents=[
                    {"id": doc.id, "title": doc.title, "subject": doc.subject}
                    for doc in relevant_docs
                ]
            )

            response_time = int((time.time() - start_time) * 1000)

            self._log_usage(
                user=user,
                endpoint='ask-ai',
                usage=usage,
                response_time=response_time,
                success=True
            )

            return {
                "answer": answer,
                "conversation_id": conversation.id,
                "retrieved_documents": [
                    {"title": doc.title, "subject": doc.subject, "relevance": "high"}
                    for doc in relevant_docs[:3]
                ],
                "tokens_used": usage.get('total_tokens', 0)
            }

        except Exception as e:

            self._log_usage(
                user=user,
                endpoint='ask-ai',
                usage={},
                response_time=0,
                success=False,
                error_message=str(e)
            )

            raise e

    # =====================================================
    # LLM CALL
    # =====================================================

    def _call_llm(self, messages):

        # ---------- MOCK ----------
        if self.ai_mode == "mock":
            return {
                "choices": [{
                    "message": {
                        "content": self._mock_response(messages)
                    }
                }],
                "usage": {}
            }

        # ---------- GROQ ----------
        if self.ai_mode == "groq":

            response = self.groq.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            return {
                "choices": [{
                    "message": {
                        "content": response.choices[0].message.content
                    }
                }],
                "usage": {}
            }

        raise Exception("Invalid AI_MODE")

    # =====================================================

    def _mock_response(self, messages):

        user_message = messages[-1]["content"]

        return f"""
[LOCAL MOCK AI RESPONSE]

You asked:

{user_message}

This is simulated AI output.
"""

    # =====================================================

    def _build_system_prompt(self, context, exam_type):

        base = """You are an expert AI tutor helping students prepare for competitive exams."""

        if context:
            base += f"\nContext: {context}"

        if exam_type:
            base += f"\nExam: {exam_type}"

        return base

    def _build_user_prompt(self, question, knowledge_context):

        return f"""
Knowledge Base Context:
{knowledge_context}

Question: {question}
"""

    # =====================================================

    def _log_usage(self, user, endpoint, usage, response_time,
                   success=True, error_message=""):

        AIUsageLog.objects.create(
            user=user,
            endpoint=endpoint,
            model_used=self.model,
            response_time_ms=response_time,
            success=success,
            error_message=error_message
        )
