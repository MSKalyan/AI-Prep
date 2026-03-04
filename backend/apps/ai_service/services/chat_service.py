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
 