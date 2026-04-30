import os
import json
import time
import logging
from typing import Any
from django.conf import settings
from django.db import DatabaseError
from groq import Groq
import google as genai
from pydantic import BaseModel, ValidationError

from ..models import Conversation, Message, AIUsageLog
from ..rag.services.rag_service import RAGService

logger = logging.getLogger(__name__)


class LLMMessageSchema(BaseModel):
    content: str


class LLMChoiceSchema(BaseModel):
    message: LLMMessageSchema


class LLMUsageSchema(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMResponseSchema(BaseModel):
    choices: list[LLMChoiceSchema]
    usage: LLMUsageSchema = LLMUsageSchema()


class AIService:
    def __init__(self):
        self.ai_mode = os.getenv("AI_MODE", "groq")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS

        if self.ai_mode == "groq" and self.groq_api_key:
            self.groq = Groq(api_key=self.groq_api_key)
        elif self.ai_mode == "gemini" and self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")

        self.rag = RAGService()

    def ask_ai(
        self,
        user,
        question: str,
        context: str = "",
        conversation_id: int = None,
        exam_type: str = "",
    ):
        start_time = time.time()

        try:
            self._validate_ask_ai_inputs(user=user, question=question)
            question_clean = question.strip().lower()

            if question_clean in ["ok", "okay", "proceed", "continue", "yes"]:
                return {
                    "answer": "Please specify what you'd like to proceed with.",
                    "mode": "clarification",
                    "confidence": 0,
                }

            conversation = None

            if conversation_id:
                try:
                    conversation = Conversation.objects.get(
                        id=conversation_id, user=user
                    )
                except Conversation.DoesNotExist:
                    conversation = None

            if not conversation:
                conversation = Conversation.objects.create(
                    user=user, title=question[:100], context=context
                )

            previous_messages = list(
                conversation.messages.all().order_by("-created_at")[:5]
            )[::-1]

            rag_result = self.rag.query(
                query=question, exam_type=exam_type, subject=context
            )

            retrieved_docs = rag_result.get("documents", [])
            answer = rag_result.get("answer", "").strip()
            usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

            answer, usage = self._resolve_answer_with_fallback(
                retrieved_docs=retrieved_docs,
                answer=answer,
                question=question,
                previous_messages=previous_messages,
                context=context,
                exam_type=exam_type,
            )

            Message.objects.create(
                conversation=conversation,
                role="user",
                content=question,
            )

            Message.objects.create(
                conversation=conversation,
                role="assistant",
                content=answer,
                retrieved_documents=retrieved_docs,  # IMPORTANT
            )

            response_time = int((time.time() - start_time) * 1000)

            self._log_usage(
                user=user,
                endpoint="ask-ai",
                usage=usage,
                response_time=response_time,
                success=True,
            )

            return {
                "answer": answer,
                "mode": "rag",
                "confidence": 1.0 if retrieved_docs else 0.5,
                "conversation_id": conversation.id,
                "tokens_used": usage.get("total_tokens", 0),
                "sources": retrieved_docs[:3],
            }

        except (DatabaseError, ValueError, TypeError, KeyError, AttributeError, TimeoutError):
            self._log_usage(
                user=user,
                endpoint="ask-ai",
                usage={},
                response_time=0,
                success=False,
                error_message="ask_ai failed",
            )
            logger.error("AIService.ask_ai failed", exc_info=True)
            raise
    @staticmethod
    def _validate_ask_ai_inputs(user, question: str) -> None:
        if user is None:
            raise ValueError("user is required")
        if not isinstance(question, str):
            raise TypeError("question must be a string")
        if not question.strip():
            raise ValueError("question must not be empty")

    def _resolve_answer_with_fallback(
        self,
        *,
        retrieved_docs,
        answer,
        question,
        previous_messages,
        context,
        exam_type,
    ):
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        if not retrieved_docs:
            return self._call_with_fallback(
                question, previous_messages, context, exam_type, strict=False
            )
        if self._should_fallback(answer):
            return self._call_with_context_and_fallback(
                retrieved_docs, question, previous_messages, context, exam_type
            )
        return answer, usage

    def _should_fallback(self, text):
        normalized = text.strip().lower()
        triggers = [
            "not found",
            "no relevant information found",
            "can't find",
            "cannot find",
            "don't know",
            "unable to",
            "no answer",
        ]
        return (
            not normalized
            or any(trigger in normalized for trigger in triggers)
            or len(normalized) < 50
        )

    def _build_system_prompt(self, context, exam_type, strict=True):
        if strict:
            base = "You are a strict exam assistant. Answer ONLY from provided context."
        else:
            base = (
                "You are a helpful exam assistant. Use the provided context if it contains the answer, "
                "otherwise answer from general knowledge. Do not invent facts."
            )
        if context:
            base += f"\nContext hint: {context}"
        if exam_type:
            base += f"\nExam: {exam_type}"
        return base

    def _build_prompt(self, question, context_text="", strict=True):
        if strict:
            return f"""
You are a strict exam assistant.

Rules:
- Answer ONLY from the context
- Do NOT assume anything
- If answer is not present, say "Not found".

Context:
{context_text}

Question:
{question}

Answer:
"""
        else:
            if context_text:
                return f"""
You are a helpful exam assistant.

Rules:
- Use the provided context if it contains the answer.
- If the answer is not in the context, answer from general knowledge.
- Do NOT invent facts.

Context:
{context_text}

Question:
{question}

Answer:
"""
            return f"""
You are a helpful exam assistant.

Rules:
- Answer the question from general knowledge.
- Do NOT invent facts.

Question:
{question}

Answer:
"""
    def _call_with_fallback(
        self, question, previous_messages, context, exam_type, strict=True
    ):
        system_prompt = self._build_system_prompt(context, exam_type, strict=strict)
        user_prompt = self._build_prompt(question, strict=strict)
        messages = self._build_messages(system_prompt, user_prompt, previous_messages)
        response = self._call_llm(messages)
        return response["choices"][0]["message"]["content"], response.get("usage", {})

    def _call_with_context_and_fallback(
        self, retrieved_docs, question, previous_messages, context, exam_type
    ):
        context_text = "\n\n".join(retrieved_docs[:3])
        answer, usage = self._call_with_prompt(
            question, context_text, previous_messages, context, exam_type
        )
        if self._should_fallback(answer):
            answer, usage = self._call_with_fallback(
                question, previous_messages, context, exam_type, strict=False
            )
        return answer, usage

    def _call_with_prompt(
        self, question, context_text, previous_messages, context, exam_type
    ):
        system_prompt = self._build_system_prompt(context, exam_type)
        user_prompt = self._build_prompt(question, context_text)
        messages = self._build_messages(system_prompt, user_prompt, previous_messages)
        response = self._call_llm(messages)
        return response["choices"][0]["message"]["content"], response.get("usage", {})

    def _build_messages(self, system_prompt, user_prompt, previous_messages):
        messages = [{"role": "system", "content": system_prompt}]
        for msg in previous_messages:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": user_prompt})
        return messages

    def _call_llm(self, messages):
        if self.ai_mode == "mock":
            return self._validate_llm_response(self._mock_response())

        if self.ai_mode == "groq":
            return self._validate_llm_response(self._call_groq(messages))

        if self.ai_mode == "gemini":
            return self._validate_llm_response(self._call_gemini(messages))

        raise ValueError("Invalid AI_MODE")
    @staticmethod
    def _validate_llm_response(response: Any):
        try:
            validated = LLMResponseSchema.model_validate(response)
            return validated.model_dump()
        except ValidationError:
            logger.error("Invalid LLM response schema", exc_info=True)
            raise ValueError("LLM returned invalid response schema")
    def _mock_response(self):
        return {
            "choices": [{"message": {"content": "Mock response"}}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }
    def _call_groq(self, messages):
        response = self.groq.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        return self._format_groq_response(response)
    def _call_gemini(self, messages):
        prompt = self._build_gemini_prompt(messages)
        response = self.gemini_model.generate_content(prompt)

        return {
            "choices": [{"message": {"content": response.text}}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }
    def _build_gemini_prompt(self, messages):
        return "\n".join(
            f"{msg.get('role', '').upper()}: {msg.get('content', '')}"
            for msg in messages
        )
    def _format_groq_response(self, response):
        usage = getattr(response, "usage", None)

        return {
            "choices": [
                {"message": {"content": response.choices[0].message.content}}
            ],
            "usage": {
                "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                "completion_tokens": getattr(usage, "completion_tokens", 0),
                "total_tokens": getattr(usage, "total_tokens", 0),
            },
        }
    def _log_usage(
        self, user, endpoint, usage, response_time, success, error_message=None
    ):
        try:
            AIUsageLog.objects.create(
                user=user,
                endpoint=endpoint,
                model_used=self.model,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                response_time_ms=response_time,
                success=success,
                error_message=error_message,
            )
        except DatabaseError:
            logger.error("Failed to persist AI usage log", exc_info=True)
            raise
