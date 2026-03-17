from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")


def generate_embedding(text: str):

    embedding = model.encode(text)

    embedding = np.array(embedding).astype("float32")

    # normalize for cosine similarity
    embedding = embedding / np.linalg.norm(embedding)

    return embedding.tolist()