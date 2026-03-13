import os
from config import settings
from groq import Groq 
from datetime import datetime
import time
from .rag_service import RAGService
from ..models import Document, Conversation, Message, AIUsageLog

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
                    {"title": doc.title, "subject": doc.subject}
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
    def _call_llm(self, messages):

        # =============================
        # MOCK MODE
        # =============================
        if self.ai_mode == "mock":

            content = self._mock_response(messages)

            return {
                "choices": [
                    {
                        "message": {
                            "content": content
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }

        # =============================
        # GROQ MODE
        # =============================
        if self.ai_mode == "groq":

            try:

                response = self.groq.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )

                content = response.choices[0].message.content

                usage = getattr(response, "usage", None)

                return {
                    "choices": [
                        {
                            "message": {
                                "content": content
                            }
                        }
                    ],
                    "usage": {
                        "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                        "completion_tokens": getattr(usage, "completion_tokens", 0),
                        "total_tokens": getattr(usage, "total_tokens", 0),
                    }
                }

            except Exception as e:
                raise Exception(f"LLM request failed: {str(e)}")

        # =============================
        # INVALID MODE
        # =============================
        raise Exception("Invalid AI_MODE configuration")
    
    def _build_system_prompt(self, context, exam_type):

        base = """You are an expert AI tutor helping students prepare for competitive exams."""

        if context:
            base += f"\nContext: {context}"

        if exam_type:
            base += f"\nExam: {exam_type}"

        return base

    def _build_user_prompt(self, question, knowledge_context):
      return f"""
You must answer ONLY using the provided context.

If the answer is not found in the context, reply:
"I cannot find the answer in the provided study material."

Context:
{knowledge_context}

Question:
{question}
"""

    # =====================================================

    
    def _log_usage(
        self,
        user,
        endpoint,
        usage,
        response_time,
        success,
        error_message=None
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
                error_message=error_message
            )
        except Exception as e:
            print("AIUsageLog failed:", e)