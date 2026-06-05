import logging
from django.db import DatabaseError

from ..models import Conversation, Message, Document
from ..serializers import (
    AskAISerializer,
    ConversationSerializer,
)
from ..services.services import AIService
from apps.ai_service.rag.services.rag_service import RAGService

logger = logging.getLogger(__name__)


def ask_ai(request):
    """
    Main entry point for AI question answering.
    
    WHY ASYNC HERE:
    - LLM API calls are network I/O bound (waiting for HTTP response)
    - Using async_to_sync → async LLM client allows better concurrency
    - While waiting for Groq API response, the thread isn't blocked
    - Performance benefit: multiple simultaneous LLM requests handled better
    
    I/O-BOUND: Network calls to Groq API (HTTP wait, not CPU work)
    
    RISKS: None - async_to_sync properly bridges to sync context
    """
    from asgiref.sync import async_to_sync
    
    serializer = AskAISerializer(data=request.data)

    if not serializer.is_valid():
        return None, serializer.errors, 400

    try:
        result = async_to_sync(_ask_ai_async)(
            user=request.user,
            question=serializer.validated_data["question"],
            context=serializer.validated_data.get("context", ""),
            conversation_id=serializer.validated_data.get("conversation_id"),
            exam_type=serializer.validated_data.get("exam_type", ""),
        )
        return result, None, 200

    except Conversation.DoesNotExist:
        return None, {"error": "Conversation not found"}, 404
    except Exception as e:
        logger.error("Ask AI request failed", exc_info=True)
        return None, {"error": f"AI service error: {str(e)}"}, 500


async def _ask_ai_async(user, question, context, conversation_id, exam_type):
    """
    Async core for AI question answering.
    
    Uses async LLM client for non-blocking HTTP calls.
    ORM operations use sync_to_async for thread-safe DB access.
    """
    from asgiref.sync import sync_to_async
    
    ai_service = AIService()
    
    # Sync ORM calls wrapped with sync_to_async
    # WHY: Django ORM is sync, needs thread pool for async context
    conversation = await sync_to_async(
        ai_service._get_or_create_conversation,
        thread_sensitive=True
    )(user, conversation_id, question, context)
    
    previous_messages = await sync_to_async(
        lambda: list(
            conversation.messages.all().order_by("-created_at")[:5]
        )[::-1]
    )()
    
    # RAG query (sync, but fast - in-memory)
    rag_result = ai_service.rag.query(query=question, exam_type=exam_type, subject=context)
    retrieved_docs = rag_result.get("documents", [])
    answer = rag_result.get("answer", "").strip()
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    
    # Async LLM call - THIS IS WHERE THE PERFORMANCE BENEFIT IS
    # WHY: Non-blocking HTTP to Groq API
    answer, usage = await _resolve_answer_async(
        ai_service, retrieved_docs, answer, question, previous_messages, context, exam_type
    )
    
    # Save messages (sync ORM via sync_to_async)
    await sync_to_async(ai_service._save_messages)(
        conversation, question, answer, retrieved_docs
    )
    
    return {
        "answer": answer,
        "mode": "rag",
        "confidence": 1.0 if retrieved_docs else 0.5,
        "conversation_id": conversation.id,
        "tokens_used": usage.get("total_tokens", 0),
        "sources": retrieved_docs[:3],
    }


async def _resolve_answer_async(ai_service, retrieved_docs, answer, question, previous_messages, context, exam_type):
    """Async resolution - uses async LLM calls."""
    from ..services.llm_client import LLMClient
    
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    
    if not retrieved_docs:
        return await _call_fallback_async(ai_service, question, previous_messages, context, exam_type, strict=False)
    
    # Check if should fallback to LLM
    from ..services.prompt_builder import should_fallback
    if should_fallback(answer):
        return await _call_with_context_async(ai_service, question, retrieved_docs, previous_messages, context, exam_type)
    
    return answer, usage


async def _call_fallback_async(ai_service, question, previous_messages, context, exam_type, strict=True):
    """Async LLM fallback call."""
    from ..services.llm_client import LLMClient
    from ..services.prompt_builder import build_system_prompt, build_user_prompt
    
    llm = LLMClient()
    system_prompt = build_system_prompt(context, exam_type, strict)
    user_prompt = build_user_prompt(question, strict=strict)
    messages = ai_service._build_messages(system_prompt, user_prompt, previous_messages)
    
    # ASYNC LLM CALL - This is the performance optimization
    response = await llm.call_async(messages)
    answer = response.get("choices", [{}])[0].get("message", {}).get("content", "")
    usage = response.get("usage", {})
    return answer, usage


async def _call_with_context_async(ai_service, question, retrieved_docs, previous_messages, context, exam_type):
    """Async LLM call with context."""
    from ..services.llm_client import LLMClient
    from ..services.prompt_builder import build_system_prompt, build_user_prompt, should_fallback
    
    llm = LLMClient()
    context_text = "\n\n".join(retrieved_docs[:3])
    system_prompt = build_system_prompt(context, exam_type)
    user_prompt = build_user_prompt(question, context_text)
    messages = ai_service._build_messages(system_prompt, user_prompt, previous_messages)
    
    # ASYNC LLM CALL
    response = await llm.call_async(messages)
    answer = response.get("choices", [{}])[0].get("message", {}).get("content", "")
    usage = response.get("usage", {})
    
    from ..services.prompt_builder import should_fallback as check_fallback
    if check_fallback(answer):
        answer, usage = await _call_fallback_async(ai_service, question, previous_messages, context, exam_type, strict=False)
    
    return answer, usage


def get_conversations(user):
    """Sync ORM - no async benefit for simple DB queries."""
    conversations = Conversation.objects.filter(user=user)[:20]
    return ConversationSerializer(conversations, many=True).data


def get_conversation_messages(request, conversation_id):
    """Sync ORM - no async benefit for simple DB queries."""
    try:
        conversation = Conversation.objects.get(id=conversation_id, user=request.user)
    except Conversation.DoesNotExist:
        return None, {"error": "Conversation not found"}, 404

    try:
        limit = int(request.query_params.get("limit", "10"))
    except (ValueError, TypeError):
        limit = 10

    limit = max(1, min(limit, 100))

    qs = (
        Message.objects.filter(conversation=conversation)
        .order_by("-created_at")
        .only("role", "content", "retrieved_documents", "created_at")
    )[:limit]

    messages = list(qs)[::-1]

    return [
        {
            "role": m.role,
            "content": m.content,
            "retrieved_documents": m.retrieved_documents,
            "created_at": m.created_at,
        }
        for m in messages
    ], None, None


def upload_document(request):
    """Sync ORM + file handling - no async benefit."""
    from ..serializers import DocumentUploadSerializer

    serializer = DocumentUploadSerializer(data=request.data, context={"request": request})

    if not serializer.is_valid():
        return None, serializer.errors, 400

    document = serializer.save()
    return {
        "id": document.id,
        "title": document.title,
        "processed": document.processed,
    }, None, 201


def process_document(request):
    """Sync ORM + RAG - no async benefit for single document."""
    document_id = request.data.get("document_id")
    if not document_id:
        return None, {"error": "document_id is required"}, 400

    try:
        document = Document.objects.get(id=document_id, user=request.user)
        if document.processed:
            return {"message": "Document already processed"}, None, 200

        rag = RAGService()
        rag.ingest_document(document)
        document.processed = True
        document.save()
        return {"message": "Document processed successfully"}, None, 200

    except Document.DoesNotExist:
        return None, {"error": "Document not found"}, 404
    except Exception as e:
        logger.error("Document processing failed", exc_info=True)
        return None, {"error": str(e)}, 500




