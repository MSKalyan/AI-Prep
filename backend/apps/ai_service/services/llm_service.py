import json
import time
import logging
from groq import Groq
from django.conf import settings
from apps.utils.retry_utils import safe_llm_call

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        api_key = settings.GROQ_API_KEY
        self.client = None
        if api_key:
            self.client = Groq(api_key=api_key)
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS

    def generate_response(
        self,
        prompt: str,
        user=None,
        endpoint: str = "topic-explanation",
        expect_json: bool = False,
    ):
        start_time = time.time()
        if not self.client:
            return None
        try:
            response = self._call_llm(prompt)
            return response if not expect_json else json.loads(response)
        except Exception:
            self._handle_failure(start_time, user, endpoint)
            raise

    def _call_llm(self, prompt: str):
        response = safe_llm_call(
            self.client,
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an educational assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content if response else None

    def _handle_failure(self, start_time: float, user, endpoint: str):
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "LLM call failed for endpoint=%s user=%s elapsed_ms=%d",
            endpoint,
            user,
            elapsed_ms,
        )