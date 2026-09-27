"""Sliding window turn buffer for agent conversation context."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass
class Turn:
    role: str  # "user" | "assistant" | "tool"
    content: str
    token_count: int = 0


class TurnBuffer:
    """Maintains a fixed-size sliding window of recent conversation turns."""

    def __init__(self, max_tokens: int = 4096) -> None:
        self._max_tokens = max_tokens
        self._turns: deque[Turn] = deque()
        self._total_tokens = 0

    def add(self, role: str, content: str, token_count: int | None = None) -> None:
        tokens = token_count if token_count is not None else max(1, len(content) // 4)
        turn = Turn(role=role, content=content, token_count=tokens)
        self._turns.append(turn)
        self._total_tokens += tokens
        while self._total_tokens > self._max_tokens and len(self._turns) > 1:
            evicted = self._turns.popleft()
            self._total_tokens -= evicted.token_count

    def get_messages(self) -> list[dict]:
        return [{"role": t.role, "content": t.content} for t in self._turns]

    def clear(self) -> None:
        self._turns.clear()
        self._total_tokens = 0

    @property
    def token_count(self) -> int:
        return self._total_tokens
