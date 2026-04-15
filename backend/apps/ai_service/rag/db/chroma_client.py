import chromadb

def get_chroma_client():
    return chromadb.Client(
        chromadb.config.Settings(
            is_persistent=True,
            persist_directory="./chroma_db"
        )
    )

def get_collection(name="documents"):
    client = get_chroma_client()
    return client.get_or_create_collection(name=name)