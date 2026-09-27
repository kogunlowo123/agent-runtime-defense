"""Auto-tagger: generates content tags using LLM."""
from __future__ import annotations


def auto_tag(text: str, model: str = "azure/gpt-4o-mini") -> list[str]:
    """Generate up to 5 descriptive tags for a document chunk."""
    try:
        import litellm

        prompt = (
            "Generate up to 5 short topic tags for the following text. "
            "Return a JSON array of strings, nothing else.\n\nText:\n" + text[:1000]
        )
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=64,
            temperature=0.0,
        )
        import json

        raw = response.choices[0].message.content.strip()
        return json.loads(raw)
    except Exception:
        return []


def tag_document(metadata: dict, text: str, model: str = "azure/gpt-4o-mini") -> dict:
    """Attach auto-generated tags to metadata."""
    metadata["auto_tags"] = auto_tag(text, model=model)
    return metadata
