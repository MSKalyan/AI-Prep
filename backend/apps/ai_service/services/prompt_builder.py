def build_system_prompt(context, exam_type, strict=True):
    if strict:
        base = "You are a strict exam assistant. Answer ONLY from provided context."
    else:
        base = (
            "You are a helpful exam assistant. Use the provided context if it contains the answer, "
            "otherwise answer from general knowledge. Do not invent facts."
        )
    if context:
        base += f"\nContext hint: {context}"
    if exam_type:
        base += f"\nExam: {exam_type}"
    return base


def build_user_prompt(question, context_text="", strict=True):
    if strict:
        return f"""You are a strict exam assistant.

Rules:
- Answer ONLY from the context
- Do NOT assume anything
- If answer is not present, say "Not found".

Context:
{context_text}

Question:
{question}

Answer:
"""
    else:
        if context_text:
            return f"""You are a helpful exam assistant.

Rules:
- Use the provided context if it contains the answer.
- If the answer is not in the context, answer from general knowledge.
- Do NOT invent facts.

Context:
{context_text}

Question:
{question}

Answer:
"""
        return f"""You are a helpful exam assistant.

Rules:
- Answer the question from general knowledge.
- Do NOT invent facts.

Question:
{question}

Answer:
"""


def should_fallback(text):
    normalized = text.strip().lower()
    triggers = [
        "not found",
        "no relevant information found",
        "can't find",
        "cannot find",
        "don't know",
        "unable to",
        "no answer",
    ]
    return (
        not normalized
        or any(trigger in normalized for trigger in triggers)
        or len(normalized) < 50
    )