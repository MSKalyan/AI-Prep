from ml_utils import ModelLoader
import numpy as np

model = ModelLoader.get_model()


def generate_embedding(text: str):

    embedding = model.encode(text)

    embedding = np.array(embedding).astype("float32")

    # normalize for cosine similarity
    embedding = embedding / np.linalg.norm(embedding)

    return embedding.tolist()