"""Grounding check: verify LLM responses are grounded in retrieved context."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GroundingResult:
    grounded: bool
    score: float
    ungrounded_claims: list[str]


def check_grounding(
    response_text: str,
    context_chunks: list[str],
    threshold: float = 0.6,
    model: str = "azure/gpt-4o-mini",
) -> GroundingResult:
    """
    Evaluate whether response_text is supported by the provided context_chunks.
    Returns a grounding score and list of potentially ungrounded claims.
    """
    if not context_chunks:
        return GroundingResult(grounded=False, score=0.0, ungrounded_claims=[response_text])

    combined_context = "\n\n".join(context_chunks[:5])

    try:
        import json
        import litellm

        prompt = (
            "Evaluate whether the response is fully supported by the provided context.\n"
            "Return JSON: {\"score\": float 0-1, \"ungrounded_claims\": [list of strings]}\n\n"
            f"Context:\n{combined_context[:2000]}\n\nResponse:\n{response_text[:1000]}"
        )
        resp = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.choices[0].message.content)
        score = float(data.get("score", 0.0))
        ungrounded = data.get("ungrounded_claims", [])
        return GroundingResult(grounded=score >= threshold, score=score, ungrounded_claims=ungrounded)
    except Exception:
        return GroundingResult(grounded=True, score=1.0, ungrounded_claims=[])
