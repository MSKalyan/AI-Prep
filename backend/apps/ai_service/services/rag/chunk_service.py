def chunk_text(text, chunk_size=400, overlap=80):

    words = text.split()

    chunks = []

    step = chunk_size - overlap

    for i in range(0, len(words), step):

        chunk_words = words[i:i + chunk_size]

        if not chunk_words:
            break

        chunk = " ".join(chunk_words)

        chunks.append(chunk)

    return chunks