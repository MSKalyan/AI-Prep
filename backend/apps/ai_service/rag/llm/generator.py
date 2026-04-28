from apps.ai_service.llm.base import LLMFactory
from apps.ai_service.llm.prompts import SYSTEM_EXAM_PRECISE
import os

MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
def _get_client():
    return LLMFactory.create_chat_model(model=MODEL, temperature=0.2)

def generate_answer(query, context):
    print(f"DEBUG generate_answer: query={query[:50]}, context_len={len(context)}")
    if not context or not context.strip():
        return "No relevant context found."
    
    prompt = f"""Based only on the context below, answer the question.
Context:
{context}
Question: {query}
Answer:"""
    
    client = _get_client()
    response = client.invoke([
        {"role": "system", "content": "You are a precise exam assistant. Answer ONLY from the provided context."},
        {"role": "user", "content": prompt}
    ])
    return response.content if hasattr(response, "content") else ""

def generate_summary(text, query=None):
    question_block = f"\nQuestion:\n{query}" if query else ""
    prompt = f"""
Summarize the excerpt below with a focus on the information relevant to the question.
If the question is not answered in the excerpt, say "Not found".

Excerpt:
{text}
{question_block}

Summary:
"""

    client = _get_client()
    messages = [
        {"role": "system", "content": "You are a concise summarization assistant."},
        {"role": "user", "content": prompt}
    ]
    response = client.invoke(messages)
    return response.content if hasattr(response, "content") else ""