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

    def _mock_response(self, messages):

        user_message = messages[-1]["content"]

        return f"""
[LOCAL MOCK AI RESPONSE]

You asked:

{user_message}

This is simulated AI output.
"""

    # =====================================================

    