from typing import List

import re


def chunk_text(text: str, chunk_size: int = 400) -> List[str]:
    sentences = re.split(r'(?<=[.!?]) +', text)
    
    chunks: List[str] = []
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