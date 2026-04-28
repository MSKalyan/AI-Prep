from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
EMBEDDINGS_MODEL = "BAAI/bge-small-en-v1.5"
PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "documents"
def get_embeddings():
    return HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)
def get_vectorstore(collection_name=COLLECTION_NAME):
    return Chroma(
        collection_name=collection_name,
        embedding_function=get_embeddings(),
        persist_directory=PERSIST_DIR
    )
def get_retriever(collection_name=COLLECTION_NAME, search_type="similarity", k=5):
    vectorstore = get_vectorstore(collection_name)
    return vectorstore.as_retriever(
        search_type=search_type,
        search_kwargs={"k": k}
    )
def get_collection(collection_name=COLLECTION_NAME):
    return get_vectorstore(collection_name)