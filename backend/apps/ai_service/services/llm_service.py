import json

from groq import Groq
from django.conf import settings


class LLMService:
    """
    Service responsible for communicating with the LLM provider.
    """

    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS

    def generate_response(self, prompt: str, expect_json: bool = False) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an educational assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            content = response.choices[0].message.content.strip()

            if expect_json:
                return json.loads(content)

            return content

        except Exception as e:
            print(f"LLM Error: {e}")
            return None