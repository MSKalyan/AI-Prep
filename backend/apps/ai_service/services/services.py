import logging
from ..models import Conversation, Message
from ..rag.services.rag_service import RAGService
from .llm_client import LLMClient
from .prompt_builder import build_system_prompt, build_user_prompt, should_fallback

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.llm = LLMClient()
        self.rag = RAGService()

    def ask_ai(self, user, question: str, context: str = "", conversation_id: int = None, exam_type: str = ""):
        try:
            self._validate_inputs(user=user, question=question)

            question_clean = question.strip().lower()
            if question_clean in ["ok", "okay", "proceed", "continue", "yes"]:
                return {
                    "answer": "Please specify what you'd like to proceed with.",
                    "mode": "clarification",
                    "confidence": 0,
                }

            conversation = self._get_or_create_conversation(user, conversation_id, question, context)

            previous_messages = list(
                conversation.messages.all().order_by("-created_at")[:5]
            )[::-1]

            rag_result = self.rag.query(query=question, exam_type=exam_type, subject=context)
            retrieved_docs = rag_result.get("documents", [])
            answer = rag_result.get("answer", "").strip()
            usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

            answer, usage = self._resolve_answer(
                retrieved_docs, answer, question, previous_messages, context, exam_type
            )

            self._save_messages(conversation, question, answer, retrieved_docs)

            return {
                "answer": answer,
                "mode": "rag",
                "confidence": 1.0 if retrieved_docs else 0.5,
                "conversation_id": conversation.id,
                "tokens_used": usage.get("total_tokens", 0),
                "sources": retrieved_docs[:3],
            }

        except (ValueError, TypeError, KeyError, AttributeError, TimeoutError):
            logger.error("AIService.ask_ai failed", exc_info=True)
            raise

    @staticmethod
    def _validate_inputs(user, question: str) -> None:
        if user is None:
            raise ValueError("user is required")
        if not isinstance(question, str):
            raise TypeError("question must be a string")
        if not question.strip():
            raise ValueError("question must not be empty")

    def _get_or_create_conversation(self, user, conversation_id, question, context):
        if conversation_id:
            try:
                return Conversation.objects.get(id=conversation_id, user=user)
            except Conversation.DoesNotExist:
                pass
        return Conversation.objects.create(user=user, title=question[:100], context=context)

    def _resolve_answer(self, retrieved_docs, answer, question, previous_messages, context, exam_type):
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        if not retrieved_docs:
            return self._call_fallback(question, previous_messages, context, exam_type, strict=False)
        if should_fallback(answer):
            return self._call_with_context(question, retrieved_docs, previous_messages, context, exam_type)
        return answer, usage

    def _call_fallback(self, question, previous_messages, context, exam_type, strict=True):
        system_prompt = build_system_prompt(context, exam_type, strict)
        user_prompt = build_user_prompt(question, strict=strict)
        messages = self._build_messages(system_prompt, user_prompt, previous_messages)
        response = self.llm.call(messages)
        answer = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = response.get("usage", {})
        return answer, usage

    def _call_with_context(self, question, retrieved_docs, previous_messages, context, exam_type):
        context_text = "\n\n".join(retrieved_docs[:3])
        system_prompt = build_system_prompt(context, exam_type)
        user_prompt = build_user_prompt(question, context_text)
        messages = self._build_messages(system_prompt, user_prompt, previous_messages)
        response = self.llm.call(messages)
        answer = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = response.get("usage", {})

        if should_fallback(answer):
            answer, usage = self._call_fallback(question, previous_messages, context, exam_type, strict=False)
        return answer, usage

    def _build_messages(self, system_prompt, user_prompt, previous_messages):
        messages = [{"role": "system", "content": system_prompt}]
        for msg in previous_messages:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": user_prompt})
        return messages

    def _save_messages(self, conversation, question, answer, retrieved_docs):
        Message.objects.create(conversation=conversation, role="user", content=question)
        Message.objects.create(
            conversation=conversation,
            role="assistant",
            content=answer,
            retrieved_documents=retrieved_docs,
        )

    def generate_questions(self, exam_type, subject, topic="", difficulty="medium", num_questions=10, question_type="mcq"):
        return self.llm.generate_questions(
            exam_type=exam_type,
            subject=subject,
            topic=topic,
            difficulty=difficulty,
            num_questions=num_questions,
            question_type=question_type,
        )