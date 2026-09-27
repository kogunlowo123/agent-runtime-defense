"""Behavior query tool: fetches anomaly scores from the behavior API."""
from __future__ import annotations

import time

import httpx

from .base import BaseTool, ToolResult


class BehaviorQueryTool(BaseTool):
    """Queries the behavior API to get the current anomaly score for a principal."""

    def __init__(self, api_base_url: str, auth_token: str = "") -> None:
        self._base_url = api_base_url.rstrip("/")
        self._token = auth_token

    @property
    def name(self) -> str:
        return "behavior_query"

    @property
    def description(self) -> str:
        return "Retrieve the anomaly score and baseline for an agent principal."

    def execute(self, principal_id: str, **kwargs) -> ToolResult:
        start = time.monotonic()
        headers = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        try:
            response = httpx.get(
                f"{self._base_url}/api/v1/behavior/{principal_id}",
                headers=headers,
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            latency = (time.monotonic() - start) * 1000
            return ToolResult(success=True, data=data, latency_ms=latency)
        except httpx.HTTPStatusError as exc:
            latency = (time.monotonic() - start) * 1000
            if exc.response.status_code == 404:
                return ToolResult(success=True, data={"baseline": None}, latency_ms=latency)
            return ToolResult(success=False, data=None, error=str(exc), latency_ms=latency)
        except Exception as exc:
            latency = (time.monotonic() - start) * 1000
            return ToolResult(success=False, data=None, error=str(exc), latency_ms=latency)
