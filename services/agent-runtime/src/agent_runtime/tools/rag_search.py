"""RAG search tool for the agent runtime."""
from __future__ import annotations

import time

import httpx

from .base import BaseTool, ToolResult


class RagSearchTool(BaseTool):
    """Searches the RAG knowledge base via the RAG core HTTP API."""

    def __init__(self, rag_base_url: str, auth_token: str = "") -> None:
        self._base_url = rag_base_url.rstrip("/")
        self._token = auth_token

    @property
    def name(self) -> str:
        return "rag_search"

    @property
    def description(self) -> str:
        return "Search the MITRE ATT&CK and threat intelligence knowledge base."

    def execute(self, query: str, top_k: int = 5, **kwargs) -> ToolResult:
        start = time.monotonic()
        headers = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        try:
            response = httpx.post(
                f"{self._base_url}/retrieve",
                json={"query": query, "top_k": top_k},
                headers=headers,
                timeout=15.0,
            )
            response.raise_for_status()
            data = response.json()
            latency = (time.monotonic() - start) * 1000
            return ToolResult(success=True, data=data, latency_ms=latency)
        except Exception as exc:
            latency = (time.monotonic() - start) * 1000
            return ToolResult(success=False, data=None, error=str(exc), latency_ms=latency)
