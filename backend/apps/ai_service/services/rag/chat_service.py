import os
import time
from django.http import JsonResponse
from config import settings
from groq import Groq
from .rag_service import RAGService
from ...models import Conversation, Message, AIUsageLog
import google as genai

class AIService:
    LOW_CONFIDENCE_THRESHOLD = 0.7

    def __init__(self):
        self.ai_mode = os.getenv("AI_MODE")
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
  
    def ask_ai(self, user, question: str, context: str = "",
               conversation_id: int = None, exam_type: str = ""):

        start_time = time.time()
        print("AI_MODE at runtime", self.ai_mode)
        try:
            question_clean = question.strip().lower()

            if question_clean in ["ok", "okay", "proceed", "continue", "yes"]:
                return {
                    "answer": "Please specify what you'd like to proceed with.",
                    "mode": "clarification",
                    "confidence": 0
                }

            relevant_docs = RAGService.retrieve_relevant_documents(
                query=question,
                exam_type=exam_type,
                top_k=settings.TOP_K_RESULTS
            )

            
            top_score = relevant_docs[0][1] if relevant_docs else 0
            if top_score < self.LOW_CONFIDENCE_THRESHOLD:
                mode = "llm"
            knowledge_context = RAGService.build_context(relevant_docs)

            if conversation_id:
                conversation = Conversation.objects.get(id=conversation_id, user=user)
            else:
                conversation = Conversation.objects.create(
                    user=user,
                    title=question[:100],
                    context=context
                )

            previous_messages = list(
                conversation.messages.all().order_by('-created_at')[:5]
            )[::-1]

           
            previous_messages = self._filter_relevant_history(question, previous_messages)

            system_prompt = self._build_system_prompt(context, exam_type)

            if not relevant_docs or top_score < self.LOW_CONFIDENCE_THRESHOLD:
                user_prompt = self._build_llm_prompt(question)
                mode = "llm"
                previous_messages = []
            else:
                user_prompt = self._build_rag_prompt(question, knowledge_context)
                mode = "rag"

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
            usage = response.get('usage', {})  # ✅ always dict now

           
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
                    {
                        "id": doc.id,
                        "title": doc.title,
                        "subject": doc.subject
                    }
                    for doc, score in relevant_docs
                    if score >= self.LOW_CONFIDENCE_THRESHOLD
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
                "mode": mode,
                "confidence": round(top_score, 3),
                "conversation_id": conversation.id,
                "retrieved_documents": [
                    {
                        "index": i + 1,
                        "title": doc.title,
                        "subject": doc.subject,
                        "content": doc.content[:200]
                    }
                    for i, (doc, score) in enumerate(relevant_docs)
                    if score >= self.LOW_CONFIDENCE_THRESHOLD
                ][:3],
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

    
    def _filter_relevant_history(self, question, previous_messages):
        if not previous_messages:
            return []

        question_words = set(question.lower().split())

        return [
            msg for msg in previous_messages
            if len(question_words & set(msg.content.lower().split())) > 0
        ]

  
    def _call_llm(self, messages):

        if self.ai_mode == "mock":
            return {
                "choices": [{"message": {"content": "Mock response"}}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }

        if self.ai_mode == "groq":
            response = self.groq.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            usage_obj = getattr(response, "usage", None)

            usage = {
                "prompt_tokens": getattr(usage_obj, "prompt_tokens", 0),
                "completion_tokens": getattr(usage_obj, "completion_tokens", 0),
                "total_tokens": getattr(usage_obj, "total_tokens", 0),
            }

            return {
                "choices": [
                    {"message": {"content": response.choices[0].message.content}}
                ],
                "usage": usage
            }
        if self.ai_mode == "gemini":

            prompt = ""
            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "")

                if role == "system":
                    prompt += f"System: {content}\n"
                elif role == "user":
                    prompt += f"User: {content}\n"
                elif role == "assistant":
                    prompt += f"Assistant: {content}\n"

            response = self.gemini_model.generate_content(prompt)

            return {
                "choices": [
                    {"message": {"content": response.text}}
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
        raise Exception("Invalid AI_MODE")

  

    def _build_system_prompt(self, context, exam_type):
        base = "You are an expert AI tutor helping students."

        if context:
            base += f"\nContext: {context}"

        if exam_type:
            base += f"\nExam: {exam_type}"

        return base

    def _build_rag_prompt(self, question, context):
        return f"""
Answer using the provided context.

IMPORTANT:
- Use the context ONLY if it is relevant
- Cite sources using [number] ONLY when clearly applicable
- If context is insufficient, answer normally without forcing citations

Context:
{context}

Question:
{question}
"""

    def _build_llm_prompt(self, question):
        return f"""
Answer independently.

Do NOT rely on previous conversation unless relevant.

Question:
{question}
"""


    def _log_usage(self, user, endpoint, usage, response_time, success, error_message=None):
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


    