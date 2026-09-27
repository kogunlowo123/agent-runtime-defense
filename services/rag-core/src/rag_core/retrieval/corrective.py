"""Corrective RAG: grades retrieved documents and falls back to rewrite if needed."""
from __future__ import annotations

from ..stores.vector_base import SearchResult


class CorrectiveRetriever:
    """
    Grades each retrieved document for relevance to the query.
    Documents scoring below the threshold trigger a query rewrite and re-retrieval.
    """

    _GRADE_PROMPT = (
        "Does this passage directly answer or support the query?\n"
        "Query: {query}\nPassage: {passage}\n"
        "Answer with a single word: yes or no."
    )

    def __init__(
        self,
        inner_retriever,
        rewriter,
        model: str = "azure/gpt-4o-mini",
        relevance_threshold: float = 0.5,
    ) -> None:
        self._retriever = inner_retriever
        self._rewriter = rewriter
        self._model = model
        self._threshold = relevance_threshold

    def retrieve(
        self,
        query_vector: list[float],
        query_text: str,
        filters: dict | None = None,
    ) -> list[SearchResult]:
        results = self._retriever.retrieve(query_vector, query_text, filters)
        relevant = [r for r in results if self._grade(query_text, r.text)]
        if not relevant:
            rewritten = self._rewriter.rewrite(query_text)
            if rewritten != query_text:
                results = self._retriever.retrieve(query_vector, rewritten, filters)
                relevant = [r for r in results if self._grade(rewritten, r.text)]
        return relevant or results

    def _grade(self, query: str, passage: str) -> bool:
        try:
            import litellm

            resp = litellm.completion(
                model=self._model,
                messages=[{"role": "user", "content": self._GRADE_PROMPT.format(query=query, passage=passage[:512])}],
                max_tokens=4,
                temperature=0.0,
            )
            answer = resp.choices[0].message.content.strip().lower()
            return answer.startswith("yes")
        except Exception:
            return True
