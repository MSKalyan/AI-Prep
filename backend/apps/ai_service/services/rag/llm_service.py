import json
import time

from groq import Groq
from django.conf import settings
from django.db import transaction

from apps.ai_service.models import AIUsageLog


class LLMService:
    """
    Service responsible for communicating with the LLM provider
    and logging AI usage with structured error handling.
    """

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
        expect_json: bool = False
    ):
        start_time = time.time()
        if not self.client:
            return None
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an educational assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            content = ""
            if response and response.choices:
                message = response.choices[0].message
                if message and message.content:
                    content = message.content.strip()

            usage = getattr(response, "usage", None)

            prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
            completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
            total_tokens = getattr(usage, "total_tokens", 0) if usage else 0

            response_time = int((time.time() - start_time) * 1000)

            # Log successful usage
            self._log_usage(
                user=user,
                endpoint=endpoint,
                success=True,
                response_time=response_time,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )

            # Validate response
            if not content or len(content) < 10:
                return None

            if expect_json:
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return None

            return content

        except Exception as e:

            response_time = int((time.time() - start_time) * 1000)

            # Log failure
            self._log_usage(
                user=user,
                endpoint=endpoint,
                success=False,
                response_time=response_time,
                error_message=str(e)[:500],
            )

            print(f"LLM Error: {e}")

            return None

    def _log_usage(
        self,
        user,
        endpoint,
        success,
        response_time,
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
        error_message=None,
    ):
        """
        Internal helper for logging AI usage safely.
        Logging failure should never break the application.
        """

        try:
            AIUsageLog.objects.create(
                user=user,
                endpoint=endpoint,
                model_used=self.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                response_time_ms=response_time,
                success=success,
                error_message=error_message,
            )
        except Exception as log_error:
            print(f"AIUsageLog failed: {log_error}")