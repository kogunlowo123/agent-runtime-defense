"""Hybrid retrieval: combine vector search with keyword BM25 via RRF."""
from __future__ import annotations

from ..stores.vector_base import BaseVectorStore, SearchResult


class HybridRetriever:
    """Merges dense vector retrieval and sparse keyword retrieval using RRF."""

    def __init__(
        self,
        vector_store: BaseVectorStore,
        alpha: float = 0.7,
        top_k: int = 10,
    ) -> None:
        self._store = vector_store
        self._alpha = alpha  # weight for vector vs keyword
        self._top_k = top_k

    def retrieve(
        self,
        query_vector: list[float],
        query_text: str,
        filters: dict | None = None,
    ) -> list[SearchResult]:
        """Return merged results from vector and BM25 keyword retrieval."""
        vector_results = self._store.search(
            query_vector=query_vector,
            top_k=self._top_k * 2,
            filters=filters,
        )
        keyword_results = self._keyword_search(query_text, top_k=self._top_k * 2)
        merged = self._rrf_merge(vector_results, keyword_results)
        return merged[: self._top_k]

    def _keyword_search(self, query: str, top_k: int) -> list[SearchResult]:
        """Placeholder BM25 keyword search — production wires to OpenSearch."""
        return []

    def _rrf_merge(
        self,
        vector_results: list[SearchResult],
        keyword_results: list[SearchResult],
        k: int = 60,
    ) -> list[SearchResult]:
        from .rrf import reciprocal_rank_fusion

        return reciprocal_rank_fusion(
            ranked_lists=[vector_results, keyword_results],
            alpha=self._alpha,
            k=k,
        )
