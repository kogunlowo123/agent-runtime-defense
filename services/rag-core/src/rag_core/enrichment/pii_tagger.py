"""PII detection and tagging for ingested documents."""
from __future__ import annotations

import re


_PII_PATTERNS: dict[str, re.Pattern] = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "phone_us": re.compile(r"\b(\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]?){13,19}\b"),
}


def detect_pii(text: str) -> dict[str, list[str]]:
    """Scan text for PII patterns. Returns dict of {pii_type: [matches]}."""
    findings: dict[str, list[str]] = {}
    for pii_type, pattern in _PII_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            findings[pii_type] = [str(m) for m in matches]
    return findings


def tag_pii(metadata: dict, text: str) -> dict:
    """Add pii_types and pii_detected flag to metadata in place."""
    findings = detect_pii(text)
    metadata["pii_detected"] = bool(findings)
    metadata["pii_types"] = list(findings.keys())
    return metadata
