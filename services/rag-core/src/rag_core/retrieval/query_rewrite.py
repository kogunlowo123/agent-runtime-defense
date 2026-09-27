"""Query rewriting for improved retrieval recall."""
from __future__ import annotations


class QueryRewriter:
    """Rewrites a retrieval query using LLM-based expansion."""

    def __init__(self, model: str = "azure/gpt-4o-mini") -> None:
        self._model = model
        self._prompt = (
            "Rewrite the following query to improve information retrieval. "
            "Be concise. Return only the rewritten query, no explanation.\n\nQuery: {query}"
        )

    def rewrite(self, query: str) -> str:
        try:
            import litellm

            response = litellm.completion(
                model=self._model,
                messages=[{"role": "user", "content": self._prompt.format(query=query)}],
                max_tokens=128,
                temperature=0.0,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return query
