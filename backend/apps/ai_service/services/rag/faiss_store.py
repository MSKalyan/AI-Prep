import faiss
import numpy as np
import pickle
import os
from ...models import Document

INDEX_PATH = "faiss.index"
MAPPING_PATH = "faiss_mapping.pkl"


class FAISSVectorStore:

    def __init__(self, dim=None):
        self.dim = dim

        if os.path.exists(INDEX_PATH) and os.path.exists(MAPPING_PATH):
            self.index = faiss.read_index(INDEX_PATH)
            self.dim = self.index.d  # ✅ sync dimension
            with open(MAPPING_PATH, "rb") as f:
                self.id_map = pickle.load(f)
        else:
            self.index = None  # ✅ delay creation
            self.id_map = []

    # =====================================================
    # ADD EMBEDDINGS (FIXED)
    # =====================================================
    def add_embeddings(self, chunks):

        existing_ids = set(self.id_map)  # ✅ prevent duplicates

        new_vectors = []
        new_ids = []

        for chunk in chunks:

            if not chunk.embedding:
                continue

            if chunk.id in existing_ids:
                continue  # ❌ skip already indexed

            new_vectors.append(chunk.embedding)
            new_ids.append(chunk.id)

        if not new_vectors:
            return

        vectors = np.array(new_vectors).astype("float32")

        # 🔥 Initialize index dynamically
        if self.index is None:
            self.dim = vectors.shape[1]
            self.index = faiss.IndexFlatIP(self.dim)
        # normalize for cosine similarity
        faiss.normalize_L2(vectors)

        self.index.add(vectors)
        self.id_map.extend(new_ids)

        self._save()

    # =====================================================
    # SEARCH (OPTIMIZED)
    # =====================================================
    def search(self, query_embedding, top_k=5):

        if self.index is None or self.index.ntotal == 0:
            return []  # ✅ safe guard

        query_vector = np.array([query_embedding]).astype("float32")
        faiss.normalize_L2(query_vector)

        distances, indices = self.index.search(query_vector, top_k)

        results = []

        # ✅ batch fetch (avoid N queries)
        valid_ids = [
            self.id_map[idx]
            for idx in indices[0]
            if idx < len(self.id_map)
        ]

        chunks_map = {
            c.id: c
            for c in Document.objects.filter(id__in=valid_ids)
        }

        for score, idx in zip(distances[0], indices[0]):

            if idx >= len(self.id_map):
                continue

            chunk_id = self.id_map[idx]

            chunk = chunks_map.get(chunk_id)
            if not chunk:
                continue
            print("Query dim:", len(query_embedding))
            print("Index dim:", self.index.d)
            results.append((chunk, float(score)))

        return results

    # =====================================================
    # SAVE
    # =====================================================
    def _save(self):
        faiss.write_index(self.index, INDEX_PATH)
        with open(MAPPING_PATH, "wb") as f:
            pickle.dump(self.id_map, f)

    # =====================================================
    # RESET INDEX (VERY IMPORTANT)
    # =====================================================
    def reset(self):
        """Completely reset FAISS index"""
        self.index = None
        self.dim = None
        self.id_map = []
        self._save()    