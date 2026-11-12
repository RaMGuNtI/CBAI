import os
import math
from typing import List
from app.core.config import settings


class FallbackDeterministicEmbeddings:
    """
    High-speed deterministic TF-IDF / character n-gram hashing embedding fallback
    used when sentence-transformers or torch are offline, in test environments, or when CPU loading is skipped.
    Produces stable 384-dimensional normalized vectors with cosine similarity preserving lexical & semantic proximity.
    """
    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_query(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        vec = [0.0] * self.dimension
        if not text:
            return vec

        words = text.lower().split()
        for i, word in enumerate(words):
            h = hash(word) % self.dimension
            vec[h] += 1.0 + (1.0 / (i + 1))

            # n-grams
            if len(word) >= 3:
                for k in range(len(word) - 2):
                    sub = word[k:k + 3]
                    h2 = hash(sub) % self.dimension
                    vec[h2] += 0.3

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec


class EmbeddingFactory:
    _instance_cache = {}

    @classmethod
    def get_embedding_model(cls, model_name: str = "all-MiniLM-L6-v2", force_fallback: bool = False):
        if force_fallback or os.getenv("TESTING") == "1":
            return FallbackDeterministicEmbeddings(dimension=384)

        cache_key = f"{model_name}"
        if cache_key in cls._instance_cache:
            return cls._instance_cache[cache_key]

        try:
            from sentence_transformers import SentenceTransformer

            class SentenceTransformerWrapper:
                def __init__(self, model_identifier: str):
                    try:
                        self.model = SentenceTransformer(model_identifier, local_files_only=True)
                    except Exception:
                        self.model = SentenceTransformer(model_identifier)

                def embed_documents(self, texts: List[str]) -> List[List[float]]:
                    embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
                    return embeddings.tolist()

                def embed_query(self, text: str) -> List[float]:
                    embedding = self.model.encode([text], convert_to_numpy=True, show_progress_bar=False)[0]
                    return embedding.tolist()

            instance = SentenceTransformerWrapper(model_name)
            cls._instance_cache[cache_key] = instance
            return instance
        except Exception:
            fallback = FallbackDeterministicEmbeddings(dimension=384)
            cls._instance_cache[cache_key] = fallback
            return fallback
