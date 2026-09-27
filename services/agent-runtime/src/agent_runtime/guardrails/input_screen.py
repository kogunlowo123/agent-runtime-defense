"""Input screening: detect prompt injection and jailbreak attempts."""
from __future__ import annotations

import re
from dataclasses import dataclass


_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions?", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+DAN", re.IGNORECASE),
    re.compile(r"pretend\s+you\s+(are|have)\s+no\s+(rules|guidelines|restrictions)", re.IGNORECASE),
    re.compile(r"system\s*prompt\s*leak", re.IGNORECASE),
    re.compile(r"<\s*/?sys\s*>", re.IGNORECASE),
    re.compile(r"\[INST\].*\[/INST\]", re.IGNORECASE),
]


@dataclass
class ScreenResult:
    allowed: bool
    reason: str = ""
    matched_pattern: str = ""


def screen_input(text: str, max_tokens: int = 8192) -> ScreenResult:
    """Check input text for prompt injection or policy violations."""
    if not text:
        return ScreenResult(allowed=True)

    # Rough token estimate: 4 chars ≈ 1 token
    estimated_tokens = len(text) // 4
    if estimated_tokens > max_tokens:
        return ScreenResult(
            allowed=False,
            reason="input_too_long",
            matched_pattern=f"estimated_tokens={estimated_tokens}",
        )

    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            return ScreenResult(
                allowed=False,
                reason="prompt_injection_detected",
                matched_pattern=pattern.pattern,
            )

    return ScreenResult(allowed=True)
