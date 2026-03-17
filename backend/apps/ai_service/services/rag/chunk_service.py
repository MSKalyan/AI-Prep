def chunk_text(text, chunk_size=120, overlap=30):

    text = " ".join(text.split())

    # split by sentences instead of words
    import re
    sentences = re.split(r'(?<=[.!?]) +', text)

    chunks = []
    current_chunk = []

    current_len = 0

    for sentence in sentences:

        words = sentence.split()
        length = len(words)

        if current_len + length > chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = current_chunk[-overlap:] if overlap < len(current_chunk) else current_chunk
            current_len = len(current_chunk)

        current_chunk.extend(words)
        current_len += length

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks