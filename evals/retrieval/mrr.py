"""Mean Reciprocal Rank (MRR) evaluation metric for RAG retrieval."""
from evals.retrieval.recall_at_k import RetrievalResult


def reciprocal_rank(result: RetrievalResult) -> float:
    """1/rank of the first relevant document in the retrieved list. 0 if none found."""
    relevant = set(result.relevant_ids)
    for rank, doc_id in enumerate(result.retrieved_ids, start=1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0


def mean_reciprocal_rank(results: list[RetrievalResult]) -> float:
    """Compute MRR over a list of retrieval results."""
    if not results:
        return 0.0
    return sum(reciprocal_rank(r) for r in results) / len(results)
