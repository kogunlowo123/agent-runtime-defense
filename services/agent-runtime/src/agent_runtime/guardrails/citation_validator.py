"""Citation validator: ensure LLM responses cite real retrieved sources."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class CitationResult:
    valid: bool
    cited_ids: list[str]
    missing_citations: bool
    hallucinated_ids: list[str]


def validate_citations(
    response_text: str,
    valid_source_ids: list[str],
    min_sources: int = 1,
) -> CitationResult:
    """
    Check that citations in response_text reference valid_source_ids.
    Citations expected as [source_id] or (source_id) in text.
    """
    citation_pattern = re.compile(r"[\[\(]([A-Za-z0-9_\-]+)[\]\)]")
    cited = citation_pattern.findall(response_text)
    valid_set = set(valid_source_ids)
    hallucinated = [c for c in cited if c not in valid_set and not c.isdigit()]

    return CitationResult(
        valid=len(cited) >= min_sources and not hallucinated,
        cited_ids=cited,
        missing_citations=len(cited) < min_sources,
        hallucinated_ids=hallucinated,
    )
