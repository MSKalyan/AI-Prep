import os
import json
import time
import openai
from typing import List, Dict, Any
from django.conf import settings
from django.core.cache import cache
from groq import Groq

from ..models import Document, Conversation, Message, AIUsageLog


# =====================================================
# RAG SERVICE
# =====================================================


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

    