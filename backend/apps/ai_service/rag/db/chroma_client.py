import chromadb
from chromadb.api.client import Client as ChromaClient
from chromadb.api.client import Collection as ChromaCollection

def get_chroma_client() -> ChromaClient:
    return chromadb.Client(
        chromadb.config.Settings(
            is_persistent=True,
            persist_directory="./chroma_db"
        )
    )

def get_collection(name: str = "documents") -> ChromaCollection:
    client = get_chroma_client()
    return client.get_or_create_collection(name=name)