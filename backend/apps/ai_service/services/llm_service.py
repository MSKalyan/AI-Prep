import json
import time

from django.conf import settings

from apps.ai_service.models import AIUsageLog
from apps.ai_service.llm.base import LLMBase


class LLMService:
    def __init__(self):
        self.llm = LLMBase()
        self.model = self.llm.get_model_name()

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
            # LangChain handles message internally (string is fine)
            response = self.llm.invoke(prompt)

            content = ""
            if response and hasattr(response, "content"):
                content = response.content.strip()

            # LangChain usage metadata (if available)
            usage = getattr(response, "usage_metadata", {}) or {}

            prompt_tokens = usage.get("prompt_token_count", 0)
            completion_tokens = usage.get("completion_token_count", 0)
            total_tokens = usage.get("total_token_count", 0)

            response_time = int((time.time() - start_time) * 1000)

            self._log_usage(
                user=user,
                endpoint=endpoint,
                success=True,
                response_time=response_time,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )

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