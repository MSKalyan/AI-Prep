def get_embeddings(texts):
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    return model.encode(texts).tolist()
