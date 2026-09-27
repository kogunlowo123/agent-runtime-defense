"""Recall@K evaluation metric for RAG retrieval."""
from dataclasses import dataclass


@dataclass
class RetrievalResult:
    query: str
    retrieved_ids: list[str]
    relevant_ids: list[str]


def recall_at_k(result: RetrievalResult, k: int) -> float:
    """
    Recall@K: fraction of relevant documents retrieved in the top-k results.

    recall@k = |retrieved_top_k ∩ relevant| / |relevant|
    """
    if not result.relevant_ids:
        return 0.0
    top_k = set(result.retrieved_ids[:k])
    relevant = set(result.relevant_ids)
    return len(top_k & relevant) / len(relevant)


def batch_recall_at_k(results: list[RetrievalResult], k: int) -> dict[str, float]:
    """Compute per-result and mean recall@k over a batch."""
    scores = [recall_at_k(r, k) for r in results]
    return {
        "mean_recall_at_k": sum(scores) / len(scores) if scores else 0.0,
        "k": float(k),
        "n": float(len(scores)),
    }
