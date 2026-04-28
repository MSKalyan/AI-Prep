from langchain_huggingface import HuggingFaceEmbeddings
MODEL_NAME = "BAAI/bge-small-en-v1.5"
def get_embeddings():
    return HuggingFaceEmbeddings(model_name=MODEL_NAME)
def embed_texts(texts):
    model = get_embeddings()
    return model.embed_documents(texts)
def embed_query(query):
    model = get_embeddings()
    return model.embed_query(query)