import hashlib
import numpy as np
from typing import List
from backend.app.core.config import settings
from backend.app.core.logging import logger

class EmbeddingService:
    def __init__(self, model_name: str = settings.EMBEDDING_MODEL_NAME, use_mock: bool = settings.USE_MOCK_MODELS):
        self.model_name = model_name
        self.use_mock = use_mock
        self.model = None
        self.dimension = 384  # Standard dimension for BGE-small / MiniLM

        if not self.use_mock:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading dense embedding model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
                self.dimension = self.model.get_sentence_embedding_dimension()
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer model ({e}). Falling back to deterministic embedding vectorizer.")
                self.use_mock = True

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if not self.use_mock and self.model:
            embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            return embeddings.tolist()
        return [self._deterministic_mock_embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        if not self.use_mock and self.model:
            embedding = self.model.encode([text], normalize_embeddings=True, show_progress_bar=False)[0]
            return embedding.tolist()
        return self._deterministic_mock_embed(text)

    def _deterministic_mock_embed(self, text: str) -> List[float]:
        """
        Deterministic pseudo-semantic embedding based on hashed token n-grams,
        ensuring real cosine similarity without needing 2GB model weights during test runs.
        """
        vec = np.zeros(self.dimension, dtype=np.float32)
        words = text.lower().split()
        for i, word in enumerate(words):
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            idx = h % self.dimension
            weight = 1.0 / (1.0 + np.log(1 + i))
            vec[idx] += weight
            # Bigrams
            if i + 1 < len(words):
                bi = f"{word}_{words[i+1]}"
                bi_h = int(hashlib.md5(bi.encode()).hexdigest(), 16)
                vec[bi_h % self.dimension] += 1.5

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

embedding_service = EmbeddingService()
