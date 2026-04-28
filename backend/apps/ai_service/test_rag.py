import os
import pytest
from unittest.mock import patch, MagicMock

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.test_settings")

import django
django.setup()


class TestPrompts:
    """Test prompt templates."""
    
    def test_prompt_templates_exist(self):
        """Test all prompt templates are defined."""
        from apps.ai_service.llm import PROMPT_TEMPLATES
        
        assert "exam_strict" in PROMPT_TEMPLATES
        assert "exam_helpful" in PROMPT_TEMPLATES
        assert "exam_precise" in PROMPT_TEMPLATES
        assert "summarizer" in PROMPT_TEMPLATES
    
    def test_get_prompt(self):
        """Test get_prompt function."""
        from apps.ai_service.llm.prompts import get_prompt
        
        prompt = get_prompt("exam_strict")
        
        assert "exam assistant" in prompt.lower()
        assert "context" in prompt.lower()
    
    def test_build_rag_prompt(self):
        """Test build_rag_prompt function."""
        from apps.ai_service.llm.prompts import build_rag_prompt
        
        prompt = build_rag_prompt(
            question="What is AI?",
            context="AI stands for Artificial Intelligence.",
            strict=True
        )
        
        assert "What is AI?" in prompt
        assert "AI stands for Artificial Intelligence" in prompt
    
    def test_system_exam_strict_contains_rules(self):
        """Test SYSTEM_EXAM_STRICT has required rules."""
        from apps.ai_service.llm.prompts import SYSTEM_EXAM_STRICT
        
        assert "Answer ONLY" in SYSTEM_EXAM_STRICT
        assert "context" in SYSTEM_EXAM_STRICT.lower()


class TestChromaClient:
    """Test ChromaDB client."""
    
    @patch('apps.ai_service.rag.db.chroma_client.Chroma')
    def test_get_vectorstore(self, mock_chroma):
        """Test get_vectorstore creates Chroma instance."""
        mock_client = MagicMock()
        mock_chroma.return_value = mock_client
        
        from apps.ai_service.rag.db.chroma_client import get_vectorstore
        
        result = get_vectorstore()
        
        mock_chroma.assert_called_once()
        assert result == mock_client
    
    @patch('apps.ai_service.rag.db.chroma_client.Chroma')
    def test_get_embeddings(self, mock_chroma):
        """Test get_embeddings creates HuggingFaceEmbeddings."""
        from apps.ai_service.rag.db.chroma_client import get_embeddings
        
        embeddings = get_embeddings()
        
        assert embeddings is not None
    
    @patch('apps.ai_service.rag.db.chroma_client.get_vectorstore')
    def test_get_retriever(self, mock_get_vectorstore):
        """Test get_retriever creates retriever."""
        mock_vs = MagicMock()
        mock_retriever = MagicMock()
        mock_vs.as_retriever.return_value = mock_retriever
        mock_get_vectorstore.return_value = mock_vs
        
        from apps.ai_service.rag.db.chroma_client import get_retriever
        
        retriever = get_retriever(k=5)
        
        mock_vs.as_retriever.assert_called_once()


class TestEmbedder:
    """Test embedding functions."""
    
    @patch('apps.ai_service.rag.ingestion.embedder.HuggingFaceEmbeddings')
    def test_get_embeddings(self, mock_hf):
        """Test get_embeddings function."""
        mock_model = MagicMock()
        mock_model.embed_documents.return_value = [[0.1, 0.2, 0.3]]
        mock_hf.return_value = mock_model
        
        from apps.ai_service.rag.ingestion.embedder import get_embeddings
        
        result = get_embeddings()
        
        assert result is not None
    
    @patch('apps.ai_service.rag.ingestion.embedder.HuggingFaceEmbeddings')
    def test_embed_texts(self, mock_hf):
        """Test embed_texts returns embeddings."""
        mock_model = MagicMock()
        mock_model.embed_documents.return_value = [[0.1, 0.2, 0.3]]
        mock_hf.return_value = mock_model
        
        from apps.ai_service.rag.ingestion.embedder import embed_texts
        
        result = embed_texts(["test text"])
        
        assert result == [[0.1, 0.2, 0.3]]


class TestHybridRetriever:
    """Test hybrid retriever."""
    
    @patch('apps.ai_service.rag.retrieval.hybrid_retriever.get_vectorstore')
    def test_hybrid_retrieve(self, mock_get_vs):
        """Test hybrid_retrieve function."""
        mock_vs = MagicMock()
        mock_retriever = MagicMock()
        
        mock_doc = MagicMock()
        mock_doc.page_content = "Test content"
        mock_doc.metadata = {"source": "test"}
        
        mock_retriever.invoke.return_value = [mock_doc]
        mock_vs.as_retriever.return_value = mock_retriever
        mock_get_vs.return_value = mock_vs
        
        from apps.ai_service.rag.retrieval.hybrid_retriever import hybrid_retrieve
        
        results = hybrid_retrieve("test query", top_k=5)
        
        assert len(results) == 1
        assert results[0]["text"] == "Test content"
        assert results[0]["metadata"] == {"source": "test"}
    
    @patch('apps.ai_service.rag.retrieval.hybrid_retriever.get_vectorstore')
    def test_hybrid_retrieve_with_filter(self, mock_get_vs):
        """Test hybrid_retrieve with filters."""
        mock_vs = MagicMock()
        mock_retriever = MagicMock()
        mock_doc = MagicMock()
        mock_doc.page_content = "Test"
        mock_doc.metadata = {}
        
        mock_retriever.invoke.return_value = [mock_doc]
        mock_vs.as_retriever.return_value = mock_retriever
        mock_get_vs.return_value = mock_vs
        
        from apps.ai_service.rag.retrieval.hybrid_retriever import hybrid_retrieve
        
        results = hybrid_retrieve(
            "test query",
            top_k=5,
            exam_type="GATE",
            subject="CS"
        )
        
        mock_vs.as_retriever.assert_called_once()


class TestStore:
    """Test document storage."""
    
    @patch('apps.ai_service.rag.ingestion.store.get_vectorstore')
    def test_store_chunks(self, mock_get_vs):
        """Test store_chunks function."""
        mock_vs = MagicMock()
        mock_get_vs.return_value = mock_vs
        
        from apps.ai_service.rag.ingestion.store import store_chunks
        
        chunks = ["chunk1", "chunk2"]
        metadata = {"document_id": 1, "title": "Test"}
        
        result = store_chunks(chunks, metadata)
        
        assert result == 2
        mock_vs.add_documents.assert_called_once()


class TestGenerator:
    """Test LLM generator."""
    
    @patch('apps.ai_service.rag.llm.generator.LLMFactory')
    def test_generate_answer(self, mock_factory):
        """Test generate_answer function."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test answer"
        mock_client.invoke.return_value = mock_response
        mock_factory.create_chat_model.return_value = mock_client
        
        from apps.ai_service.rag.llm.generator import generate_answer
        
        result = generate_answer("What is AI?", "AI is artificial intelligence.")
        
        assert "Test answer" in result
        mock_client.invoke.assert_called_once()
    
    @patch('apps.ai_service.rag.llm.generator.LLMFactory')
    def test_generate_summary(self, mock_factory):
        """Test generate_summary function."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Summary"
        mock_client.invoke.return_value = mock_response
        mock_factory.create_chat_model.return_value = mock_client
        
        from apps.ai_service.rag.llm.generator import generate_summary
        
        text = "Long text here"
        result = generate_summary(text, "What is this?")
        
        assert "Summary" in result