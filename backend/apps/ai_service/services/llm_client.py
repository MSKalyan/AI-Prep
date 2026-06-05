import os
import logging
from typing import Any
from django.conf import settings
from groq import Groq, AsyncGroq
import google as genai
from pydantic import ValidationError

from .llm_schema import LLMResponseSchema

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self):
        self.ai_mode = os.getenv("AI_MODE", "groq")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.groq = None
        self.groq_async = None
        self.gemini_model = None
        self._init_clients()

    def _init_clients(self):
        if self.ai_mode == "groq" and self.groq_api_key:
            self.groq = Groq(api_key=self.groq_api_key)
            self.groq_async = AsyncGroq(api_key=self.groq_api_key)
        elif self.ai_mode == "gemini" and self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")

    def call(self, messages):
        if self.ai_mode == "mock":
            return self._validate_response(self._mock_response())
        if self.ai_mode == "groq":
            return self._validate_response(self._call_groq(messages))
        if self.ai_mode == "gemini":
            return self._validate_response(self._call_gemini(messages))
        raise ValueError("Invalid AI_MODE")

    def _convert_groq_response(self, response):
        try:
            logger.info(f"Groq response type: {type(response)}")
            logger.info(f"Groq response: {response}")
            
            if not response.choices:
                logger.error("No choices in Groq response")
                return {"choices": [{"message": {"content": ""}}], "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}
            
            content = response.choices[0].message.content
            logger.info(f"Extracted content: {content}")
            
            usage = response.usage if hasattr(response, 'usage') and response.usage else None
            
            return {
                "choices": [
                    {
                        "message": {
                            "content": content
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": usage.prompt_tokens if usage else 0,
                    "completion_tokens": usage.completion_tokens if usage else 0,
                    "total_tokens": usage.total_tokens if usage else 0
                }
            }
        except (AttributeError, IndexError) as e:
            logger.error(f"Failed to convert Groq response: {e}", exc_info=True)
            return {"choices": [{"message": {"content": ""}}], "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}

    def _validate_response(self, response: Any):
        try:
            validated = LLMResponseSchema.model_validate(response)
            return validated.model_dump()
        except ValidationError:
            logger.error("Invalid LLM response schema", exc_info=True)
            raise ValueError("LLM returned invalid response schema")

    def _mock_response(self):
        return {"response": "This is a mock response for testing.", "reasoning": "Mock mode enabled"}

    def _call_groq(self, messages):
            try:
                response = self.groq.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                return self._convert_groq_response(response)
            except Exception as e:
                logger.error("Groq API call failed", exc_info=True)
                raise

    def _call_gemini(self, messages):
        try:
            formatted = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            response = self.gemini_model.generate_content(formatted)
            return self._convert_gemini_response(response)
        except Exception as e:
            logger.error("Gemini API call failed", exc_info=True)
            raise

    def _convert_gemini_response(self, response):
        try:
            content = response.text if hasattr(response, 'text') else str(response)
            return {
                "choices": [{"message": {"content": content}}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }
        except Exception as e:
            logger.error(f"Failed to convert Gemini response: {e}")
            return {"choices": [{"message": {"content": ""}}], "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}

    async def call_async(self, messages):
        if self.ai_mode == "mock":
            return self._validate_response(self._mock_response())
        if self.ai_mode == "groq":
            return self._validate_response(await self._call_groq_async(messages))
        if self.ai_mode == "gemini":
            return self._validate_response(self._call_gemini(messages))
        raise ValueError("Invalid AI_MODE")

    async def _call_groq_async(self, messages):
        try:
            response = await self.groq_async.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return self._convert_groq_response(response)
        except Exception as e:
            logger.error("Groq API call failed", exc_info=True)
            raise