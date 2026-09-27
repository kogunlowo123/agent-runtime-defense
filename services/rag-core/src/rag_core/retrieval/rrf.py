"""Reciprocal Rank Fusion (RRF) for merging ranked retrieval lists."""
from __future__ import annotations

from ..stores.vector_base import SearchResult


def reciprocal_rank_fusion(
    ranked_lists: list[list[SearchResult]],
    alpha: float = 0.7,
    k: int = 60,
) -> list[SearchResult]:
    """
    Merge multiple ranked lists using RRF.

    alpha weights the first list (typically vector results) relative to remaining lists.
    RRF score = sum(weight_i / (k + rank_i)) across lists.
    """
    weights = [alpha] + [(1.0 - alpha) / max(1, len(ranked_lists) - 1)] * (len(ranked_lists) - 1)
    scores: dict[str, float] = {}
    docs: dict[str, SearchResult] = {}

    for list_idx, ranked_list in enumerate(ranked_lists):
        weight = weights[list_idx] if list_idx < len(weights) else 1.0 / len(ranked_lists)
        for rank, result in enumerate(ranked_list, start=1):
            scores[result.id] = scores.get(result.id, 0.0) + weight / (k + rank)
            if result.id not in docs:
                docs[result.id] = result

    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)
    return [
        SearchResult(
            id=doc_id,
            text=docs[doc_id].text,
            score=scores[doc_id],
            metadata=docs[doc_id].metadata,
        )
        for doc_id in sorted_ids
    ]
