from unittest import result

from google import genai
from google.genai import types
import os

# Initialize client once
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def generate_embedding(text: str, is_query: bool = False):
    """
    Generate embeddings using Gemini

    is_query=True  → query embedding
    is_query=False → document embedding
    """

    task_type = (
        "RETRIEVAL_QUERY" if is_query else "RETRIEVAL_DOCUMENT"
    )

    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(task_type=task_type)
    )
    print("Embedding length:", len(result.embeddings[0].values))
    return result.embeddings[0].values