from langchain_core.prompts import ChatPromptTemplate

SYSTEM_EXAM_STRICT = "You are a strict exam assistant. Answer ONLY from provided context."
SYSTEM_EXAM_HELPFUL = "You are a helpful exam assistant..."
SYSTEM_SUMMARIZER = "You are a concise summarization assistant."
SYSTEM_EXAM_PRECISE = "You are a precise exam assistant."
PROMPT_TEMPLATES = {
    "exam_strict": SYSTEM_EXAM_STRICT,
    "exam_helpful": SYSTEM_EXAM_HELPFUL,
    "exam_precise": SYSTEM_EXAM_PRECISE,
    "summarizer": SYSTEM_SUMMARIZER,
}
def get_prompt(key: str) -> str:
    return PROMPT_TEMPLATES.get(key, PROMPT_TEMPLATES["exam_helpful"])
def build_rag_prompt(question: str, context: str, strict: bool = True) -> str:
    system = SYSTEM_EXAM_STRICT if strict else SYSTEM_EXAM_HELPFUL
    return f"{system}\n\nContext:\n{context}\n\nQuestion:\n{question}\n\nAnswer:\n"