from groq import Groq
import os

MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_answer(query, context):
    prompt = f"""
Answer strictly based on the provided context.
If answer is not in context, say "Not found".

Context:
{context}

Question:
{query}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a precise exam assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content


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

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a concise summarization assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content