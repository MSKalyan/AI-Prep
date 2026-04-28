import os
import pytest
from unittest.mock import patch, MagicMock

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.test_settings")

import django
django.setup()


class TestLLMBase:
    """Test LLMBase wrapper class."""
    
    @patch('apps.ai_service.llm.base.settings')
    @patch('apps.ai_service.llm.base.ChatGroq')
    def test_llm_base_initialization(self, mock_chatgroq, mock_settings):
        """Test LLMBase initializes correctly."""
        mock_settings.GROQ_API_KEY = "test-key"
        mock_settings.LLM_MODEL = "llama-3.1-8b-instant"
        mock_settings.LLM_TEMPERATURE = 0.3
        mock_settings.LLM_MAX_TOKENS = 2000
        mock_settings.GEMINI_API_KEY = None
        
        os.environ["GROQ_API_KEY"] = "test-key"
        os.environ["AI_MODE"] = "groq"
        
        from apps.ai_service.llm.base import LLMBase
        
        llm = LLMBase()
        
        assert llm.model == "llama-3.1-8b-instant"
        assert llm.temperature == 0.3
        assert llm.max_tokens == 2000
    
    @patch('apps.ai_service.llm.base.settings')
    @patch('apps.ai_service.llm.base.ChatGroq')
    def test_invoke_with_string(self, mock_chatgroq, mock_settings):
        """Test invoke accepts string input."""
        mock_settings.GROQ_API_KEY = "test-key"
        mock_settings.LLM_MODEL = "llama-8b"
        mock_settings.LLM_TEMPERATURE = 0.3
        mock_settings.LLM_MAX_TOKENS = 1000
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_client.invoke.return_value = mock_response
        mock_chatgroq.return_value = mock_client
        
        os.environ["GROQ_API_KEY"] = "test-key"
        
        from apps.ai_service.llm.base import LLMBase
        
        llm = LLMBase()
        response = llm.invoke("Hello")
        
        assert response.content == "Test response"
    
    @patch('apps.ai_service.llm.base.settings')
    @patch('apps.ai_service.llm.base.ChatGroq')
    def test_invoke_with_messages(self, mock_chatgroq, mock_settings):
        """Test invoke accepts messages list."""
        mock_settings.GROQ_API_KEY = "test-key"
        mock_settings.LLM_MODEL = "llama-8b"
        mock_settings.LLM_TEMPERATURE = 0.3
        mock_settings.LLM_MAX_TOKENS = 1000
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Response"
        mock_client.invoke.return_value = mock_response
        mock_chatgroq.return_value = mock_client
        
        os.environ["GROQ_API_KEY"] = "test-key"
        
        from apps.ai_service.llm.base import LLMBase
        
        llm = LLMBase()
        messages = [{"role": "user", "content": "Hi"}]
        response = llm.invoke(messages)
        
        mock_client.invoke.assert_called_once()
    
    @patch('apps.ai_service.llm.base.settings')
    @patch('apps.ai_service.llm.base.ChatGroq')
    def test_invoke_with_system_message(self, mock_chatgroq, mock_settings):
        """Test invoke adds system message."""
        mock_settings.GROQ_API_KEY = "test-key"
        mock_settings.LLM_MODEL = "llama-8b"
        mock_settings.LLM_TEMPERATURE = 0.3
        mock_settings.LLM_MAX_TOKENS = 1000
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Response"
        mock_client.invoke.return_value = mock_response
        mock_chatgroq.return_value = mock_client
        
        os.environ["GROQ_API_KEY"] = "test-key"
        
        from apps.ai_service.llm.base import LLMBase
        
        llm = LLMBase()
        response = llm.invoke("Hello", system_message="You are a teacher")
        
        call_args = mock_client.invoke.call_args[0][0]
        assert call_args[0]["role"] == "system"
        assert call_args[0]["content"] == "You are a teacher"


class TestLLMFactory:
    """Test LLMFactory class."""
    
    @patch('apps.ai_service.llm.base.settings')
    @patch('apps.ai_service.llm.base.ChatGroq')
    def test_create_chat_model_groq(self, mock_chatgroq, mock_settings):
        """Test factory creates Groq model."""
        mock_settings.GROQ_API_KEY = "test-key"
        mock_settings.LLM_MODEL = "llama-3.1-8b-instant"
        mock_settings.LLM_TEMPERATURE = 0.3
        mock_settings.LLM_MAX_TOKENS = 2000
        
        mock_client = MagicMock()
        mock_chatgroq.return_value = mock_client
        
        os.environ["GROQ_API_KEY"] = "test-key"
        os.environ["AI_MODE"] = "groq"
        
        from apps.ai_service.llm.base import LLMFactory
        
        client = LLMFactory.create_chat_model(provider="groq")
        
        mock_chatgroq.assert_called_once()
    
    @patch('apps.ai_service.llm.base.settings')
    @patch('apps.ai_service.llm.base.ChatGoogleGenerativeAI')
    def test_create_chat_model_gemini(self, mock_genai, mock_settings):
        """Test factory creates Gemini model."""
        mock_settings.GROQ_API_KEY = "test-key"
        mock_settings.GEMINI_API_KEY = "gemini-key"
        mock_settings.LLM_MODEL = "gemini-1.5-flash"
        mock_settings.LLM_TEMPERATURE = 0.3
        mock_settings.LLM_MAX_TOKENS = 2000
        
        mock_client = MagicMock()
        mock_genai.return_value = mock_client
        
        os.environ["GROQ_API_KEY"] = "test-key"
        os.environ["GEMINI_API_KEY"] = "gemini-key"
        os.environ["AI_MODE"] = "gemini"
        
        from apps.ai_service.llm.base import LLMFactory
        
        client = LLMFactory.create_chat_model(provider="gemini")
        
        mock_genai.assert_called_once()
    
    def test_singleton_pattern(self):
        """Test factory returns same instance."""
        from apps.ai_service.llm.base import LLMFactory
        
        LLMFactory._instance = None
        
        client1 = LLMFactory.get_client()
        client2 = LLMFactory.get_client()
        
        assert client1 is client2


class TestMessageHelper:
    """Test MessageHelper class."""
    
    def test_to_langchain_messages(self):
        """Test converting dict messages to LangChain messages."""
        from apps.ai_service.llm.base import MessageHelper
        
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "system", "content": "You are helpful"}
        ]
        
        result = MessageHelper.to_langchain_messages(messages)
        
        assert len(result) == 3
        assert result[0].type == "human"
        assert result[1].type == "ai"
        assert result[2].type == "system"
    
    def test_from_langchain_messages(self):
        """Test converting LangChain messages back to dict."""
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        from apps.ai_service.llm.base import MessageHelper
        
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there"),
            SystemMessage(content="You are helpful")
        ]
        
        result = MessageHelper.from_langchain_messages(messages)
        
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"
        assert result[2]["role"] == "system"
        assert result[0]["content"] == "Hello"