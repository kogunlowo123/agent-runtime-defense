"""Cross-encoder reranker for post-retrieval result refinement."""
from __future__ import annotations

from ..stores.vector_base import SearchResult


class CrossEncoderReranker:
    """Reranks candidate passages using a cross-encoder model."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        from sentence_transformers import CrossEncoder

        self._model = CrossEncoder(model_name)

    def rerank(self, query: str, candidates: list[SearchResult], top_n: int = 3) -> list[SearchResult]:
        if not candidates:
            return []
        pairs = [(query, c.text) for c in candidates]
        scores = self._model.predict(pairs)
        ranked = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)
        return [
            SearchResult(id=c.id, text=c.text, score=float(s), metadata=c.metadata)
            for s, c in ranked[:top_n]
        ]
