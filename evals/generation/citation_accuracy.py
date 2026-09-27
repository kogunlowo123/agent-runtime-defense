"""Citation accuracy evaluation for RAG-generated answers."""
from dataclasses import dataclass


@dataclass
class CitationAccuracyResult:
    total_citations: int
    verified_citations: int
    unverified_citations: list[str]
    accuracy: float


def check_citation_accuracy(
    citations: list[str],
    retrieved_context: list[dict],
) -> CitationAccuracyResult:
    """
    Verify that each citation string matches at least one retrieved document.
    A citation is considered verified if it appears as a substring of any
    retrieved document's source, technique_id, or description.
    """
    verified: list[str] = []
    unverified: list[str] = []

    for citation in citations:
        citation_lower = citation.lower()
        found = False
        for doc in retrieved_context:
            doc_text = " ".join(
                str(v) for v in doc.values() if isinstance(v, str)
            ).lower()
            if citation_lower in doc_text:
                found = True
                break
        if found:
            verified.append(citation)
        else:
            unverified.append(citation)

    total = len(citations)
    accuracy = len(verified) / total if total > 0 else 1.0

    return CitationAccuracyResult(
        total_citations=total,
        verified_citations=len(verified),
        unverified_citations=unverified,
        accuracy=accuracy,
    )
