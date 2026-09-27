"""Faithfulness evaluation: checks that generated answers are grounded in context."""
from dataclasses import dataclass


@dataclass
class FaithfulnessResult:
    query: str
    answer: str
    context: list[str]
    faithfulness_score: float  # 0.0 = completely hallucinated, 1.0 = fully grounded
    unsupported_claims: list[str]


def check_faithfulness(
    answer: str,
    context: list[str],
    min_overlap_tokens: int = 3,
) -> FaithfulnessResult:
    """
    Heuristic faithfulness check: for each sentence in the answer, verify that
    at least one context document contains overlapping tokens.

    This is a lightweight proxy; a production implementation would use a
    cross-encoder or LLM-as-judge approach.
    """
    import re

    def tokenize(text: str) -> set[str]:
        return set(re.findall(r"\b\w{4,}\b", text.lower()))

    context_tokens = set()
    for doc in context:
        context_tokens |= tokenize(doc)

    sentences = [s.strip() for s in re.split(r"[.!?]", answer) if s.strip()]
    unsupported: list[str] = []

    for sentence in sentences:
        sentence_tokens = tokenize(sentence)
        overlap = len(sentence_tokens & context_tokens)
        if sentence_tokens and overlap < min_overlap_tokens:
            unsupported.append(sentence)

    faithfulness_score = (
        1.0 - len(unsupported) / len(sentences) if sentences else 1.0
    )

    return FaithfulnessResult(
        query="",
        answer=answer,
        context=context,
        faithfulness_score=faithfulness_score,
        unsupported_claims=unsupported,
    )
