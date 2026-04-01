import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")


def generate_ai_response(context: str, query: str) -> str:
    prompt = f"""
    You are an AI tutor.

    Use the following context to answer the question.

    Context:
    {context}

    Question:
    {query}

    Answer clearly and in structured points.
    """

    response = model.generate_content(prompt)

    return response.text