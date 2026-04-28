import os
from typing import Any, Literal, Optional

from django.conf import settings
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage,AIMessage, SystemMessage


ChatModel = Literal["groq", "gemini"]


class LLMBase:
    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        self.api_mode = os.getenv("AI_MODE", "groq")
        self.groq_api_key = os.getenv("GROQ_API_KEY") or settings.GROQ_API_KEY
        self.gemini_api_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY

        self.model = model or settings.LLM_MODEL
        self.temperature = (
            temperature if temperature is not None else settings.LLM_TEMPERATURE
        )
        self.max_tokens = max_tokens or settings.LLM_MAX_TOKENS

        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self):
        if self.api_mode == "groq" and self.groq_api_key:
            return self._create_chat_model("groq")
        if self.api_mode == "gemini" and self.gemini_api_key:
            return self._create_chat_model("gemini")
        if self.groq_api_key:
            return self._create_chat_model("groq")
        raise ValueError("No valid LLM provider configured")

    def _create_chat_model(self, provider: str) -> Any:
        return LLMFactory._create(provider, self.model, self.temperature, self.max_tokens)

    def invoke(self, messages,system_message:str=None):
        if isinstance(messages, str):
            messages=[{"role":"user","content":messages}]

        if system_message:
            messages=[{"role":"system","content":system_message}]+messages
        return self.client.invoke(messages)

    def generate(self, messages: list):
        return self.client.generate(messages)

    def get_model_name(self) -> str:
        return self.model


class LLMFactory:
    _instance: Optional[LLMBase] = None

    @classmethod
    def get_client(cls, **kwargs) -> LLMBase:
        if cls._instance is None:
            cls._instance = LLMBase(**kwargs)
        return cls._instance

    @classmethod
    def reset(cls):
        cls._instance = None

    @classmethod
    def create_chat_model(
        cls,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        provider: Optional[ChatModel] = None,
    ):
        provider = provider or os.getenv("AI_MODE", "groq")
        return cls._create(provider, model, temperature, max_tokens)

    @staticmethod
    def _create(provider: str, model: Optional[str], temperature: Optional[float], max_tokens: Optional[int]) -> Any:
        if provider == "groq":
            return ChatGroq(
                groq_api_key=os.getenv("GROQ_API_KEY") or settings.GROQ_API_KEY,
                model=model or settings.LLM_MODEL,
                temperature=temperature or settings.LLM_TEMPERATURE,
                max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
            )
        if provider == "gemini":
            return ChatGoogleGenerativeAI(
                model=model or "gemini-1.5-flash",
                temperature=temperature or settings.LLM_TEMPERATURE,
                max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
            )
        raise ValueError(f"Invalid provider: {provider}")
    
class MessageHelper:

    @staticmethod
    def to_langchain_messages(messages:list[dict]) -> list[BaseMessage]:
        result=[]
        for msg in messages:
            role=msg.get("role","user")
            content=msg.get("content","")
            if role=="system":
                result.append(SystemMessage(content=content))
            elif role=="assistant":
                result.append(AIMessage(content=content))
            else:
                result.append(HumanMessage(content=content))
            return result
        
    @staticmethod
    def from_langchain_messages(messages: list[BaseMessage]) -> list[dict]:
        result = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                result.append({"role": "system", "content": msg.content})
            elif isinstance(msg, AIMessage):
                result.append({"role": "assistant", "content": msg.content})
            else:
                result.append({"role": "user", "content": msg.content})
        return result
