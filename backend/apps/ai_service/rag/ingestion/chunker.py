# Better chunking (sentence-aware)
import re

def chunk_text(text, chunk_size=400):
    sentences = re.split(r'(?<=[.!?]) +', text)
    
    chunks = []
    current = ""

    for sent in sentences:
        if len(current) + len(sent) < chunk_size:
            current += " " + sent
        else:
            chunks.append(current.strip())
            current = sent

    if current:
        chunks.append(current.strip())

    return chunks