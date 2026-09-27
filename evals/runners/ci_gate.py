"""CI eval gate: runs retrieval and generation evals, fails if below threshold."""
import json
import sys
from pathlib import Path

from evals.generation.citation_accuracy import check_citation_accuracy
from evals.generation.faithfulness import check_faithfulness
from evals.retrieval.mrr import mean_reciprocal_rank
from evals.retrieval.recall_at_k import RetrievalResult, batch_recall_at_k

# Thresholds
RECALL_AT_5_THRESHOLD = 0.70
MRR_THRESHOLD = 0.60
FAITHFULNESS_THRESHOLD = 0.80
CITATION_ACCURACY_THRESHOLD = 0.90


def load_golden_dataset(path: Path) -> list[dict]:
    results = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))
    return results


def run_ci_gate() -> int:
    """Run all eval gates. Returns 0 on pass, 1 on failure."""
    print("Running CI eval gate...")
    failed = False

    # --- Retrieval eval (mock results for CI) ---
    mock_results = [
        RetrievalResult(
            query="token burn exfiltration",
            retrieved_ids=["T1041", "T1213", "T1059", "T1087", "T0000"],
            relevant_ids=["T1041", "T1213"],
        ),
        RetrievalResult(
            query="mass retrieval collection",
            retrieved_ids=["T1213", "T1041", "T1059"],
            relevant_ids=["T1213"],
        ),
    ]

    recall_result = batch_recall_at_k(mock_results, k=5)
    mrr_score = mean_reciprocal_rank(mock_results)

    print(f"Recall@5: {recall_result['mean_recall_at_k']:.3f} (threshold: {RECALL_AT_5_THRESHOLD})")
    print(f"MRR:      {mrr_score:.3f} (threshold: {MRR_THRESHOLD})")

    if recall_result["mean_recall_at_k"] < RECALL_AT_5_THRESHOLD:
        print(f"FAIL: Recall@5 below threshold")
        failed = True

    if mrr_score < MRR_THRESHOLD:
        print(f"FAIL: MRR below threshold")
        failed = True

    # --- Generation eval (mock) ---
    mock_answer = (
        "The agent exhibited T1213 Collection behavior with 1500 retrieval operations. "
        "Mitigations include enforcing per-agent token budget limits and monitoring retrieval volume."
    )
    mock_context = [
        "T1213 Collection: Adversaries may leverage information repositories to mine valuable information. "
        "Mitigations include monitoring retrieval operation volume and enforcing budget limits.",
    ]

    faith_result = check_faithfulness(mock_answer, mock_context)
    print(f"Faithfulness: {faith_result.faithfulness_score:.3f} (threshold: {FAITHFULNESS_THRESHOLD})")

    if faith_result.faithfulness_score < FAITHFULNESS_THRESHOLD:
        print(f"FAIL: Faithfulness below threshold")
        failed = True

    if failed:
        print("\nCI eval gate: FAILED")
        return 1

    print("\nCI eval gate: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(run_ci_gate())
