"""Local BGE embedding provider using sentence-transformers."""
from __future__ import annotations

from functools import lru_cache

from .base import BaseEmbedder


class LocalBGEEmbedder(BaseEmbedder):
    """Embeds text using a locally-loaded BGE model via sentence-transformers."""

    def __init__(self, model_name: str = "BAAI/bge-large-en-v1.5") -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)
        self._dimensions = self._model.get_sentence_embedding_dimension()

    def embed(self, text: str) -> list[float]:
        vector = self._model.encode(text, normalize_embeddings=True)
        return vector.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, normalize_embeddings=True, batch_size=32)
        return [v.tolist() for v in vectors]

    @property
    def dimensions(self) -> int:
        return self._dimensions
