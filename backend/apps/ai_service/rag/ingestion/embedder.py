from typing import List
from sentence_transformers import SentenceTransformer

def get_embeddings(texts: List[str]) -> List[List[float]]:
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    return model.encode(texts).tolist()