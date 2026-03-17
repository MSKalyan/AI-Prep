from .text_extractor import extract_text
from .document_cleaner import clean_document
from .document_chunker import create_chunks
from .embed_chunks import embed_document_chunks


def process_document(document):
    """
    Full RAG ingestion pipeline:
    extract → clean → chunk → embed (+ FAISS)
    """

    # 1. Extract text
    text = extract_text(document.file.path)
    document.content = text
    document.save()

    # 2. Clean
    clean_document(document)

    # 3. Chunk
    chunks = create_chunks(document)

    # 4. Embed + FAISS index
    embedded_count = embed_document_chunks(document)

    return {
        "chunks_created": len(chunks),
        "embeddings_created": embedded_count
    }