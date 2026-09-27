"""Response execution tool: triggers T2 response actions via the response API."""
from __future__ import annotations

import time

import httpx

from .base import BaseTool, ToolResult


class ResponseExecuteTool(BaseTool):
    """Executes a response action (isolate, revoke, alert) via the response API."""

    def __init__(
        self,
        api_base_url: str,
        auth_token: str,
        approval_token: str = "",
    ) -> None:
        self._base_url = api_base_url.rstrip("/")
        self._token = auth_token
        self._approval_token = approval_token

    @property
    def name(self) -> str:
        return "response_execute"

    @property
    def description(self) -> str:
        return "Execute a T2 response action such as isolating or revoking an agent."

    def execute(
        self,
        principal_id: str,
        action: str,
        reason: str,
        ttl_seconds: int = 3600,
        **kwargs,
    ) -> ToolResult:
        start = time.monotonic()
        payload: dict = {
            "principal_id": principal_id,
            "action": action,
            "reason": reason,
            "ttl_seconds": ttl_seconds,
        }
        if self._approval_token:
            payload["approval_token"] = self._approval_token

        try:
            response = httpx.post(
                f"{self._base_url}/api/v1/response/isolate",
                json=payload,
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=15.0,
            )
            response.raise_for_status()
            data = response.json()
            latency = (time.monotonic() - start) * 1000
            return ToolResult(success=True, data=data, latency_ms=latency)
        except Exception as exc:
            latency = (time.monotonic() - start) * 1000
            return ToolResult(success=False, data=None, error=str(exc), latency_ms=latency)
