import traceback
from ..db.chroma_client import get_vectorstore, get_embeddings
import chromadb


def store_chunks(chunks, metadata):
    try:
        vectorstore = get_vectorstore()

        documents = []
        metadatas = []
        ids = []

        for i, chunk in enumerate(chunks):
            doc_id = f"{metadata['document_id']}_{i}"
            ids.append(doc_id)

            metadatas.append({
                "document_id": str(metadata["document_id"]),
                "title": metadata.get("title", ""),
                "subject": metadata.get("subject", ""),
                "exam_type": metadata.get("exam_type", ""),
                "topic": metadata.get("topic", ""),
                "chunk_index": i,
            })
            documents.append(chunk)

        vectorstore.add_documents(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        return len(chunks)

    except Exception as e:
        error_msg = f"Error in store_chunks: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)

        # Fallback: use raw chromadb client
        try:
            client = chromadb.PersistentClient(path="./chroma_db")
            collection = client.get_or_create_collection("documents")

            embedding_fn = get_embeddings()
            embeddings = embedding_fn.embed_documents(chunks)

            ids = [f"{metadata['document_id']}_{i}" for i in range(len(chunks))]
            metadatas = [{
                "document_id": str(metadata["document_id"]),
                "title": metadata.get("title", ""),
                "subject": metadata.get("subject", ""),
                "exam_type": metadata.get("exam_type", ""),
                "topic": metadata.get("topic", ""),
                "chunk_index": i,
            } for i in range(len(chunks))]

            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas
            )

            return len(chunks)

        except Exception as fallback_error:
            print(f"Fallback also failed: {type(fallback_error).__name__}: {str(fallback_error)}")
            raise