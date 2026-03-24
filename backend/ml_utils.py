from sentence_transformers import SentenceTransformer

class ModelLoader:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            print("--- Initializing Sentence Transformer ---")
            cls._model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        return cls._model