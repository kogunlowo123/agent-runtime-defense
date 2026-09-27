"""Per-session and per-agent budget enforcement."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Budget:
    max_tokens: int
    max_tool_calls: int
    max_wall_seconds: float
    tokens_used: int = 0
    tool_calls_made: int = 0
    wall_seconds_elapsed: float = 0.0

    def remaining_tokens(self) -> int:
        return max(0, self.max_tokens - self.tokens_used)

    def is_exhausted(self) -> bool:
        return (
            self.tokens_used >= self.max_tokens
            or self.tool_calls_made >= self.max_tool_calls
            or self.wall_seconds_elapsed >= self.max_wall_seconds
        )

    def consume(self, tokens: int = 0, tool_calls: int = 0, seconds: float = 0.0) -> None:
        self.tokens_used += tokens
        self.tool_calls_made += tool_calls
        self.wall_seconds_elapsed += seconds


class BudgetRegistry:
    """Tracks Budget instances keyed by session_id."""

    def __init__(self) -> None:
        self._budgets: dict[str, Budget] = {}

    def create(
        self,
        session_id: str,
        max_tokens: int = 50_000,
        max_tool_calls: int = 100,
        max_wall_seconds: float = 300.0,
    ) -> Budget:
        budget = Budget(
            max_tokens=max_tokens,
            max_tool_calls=max_tool_calls,
            max_wall_seconds=max_wall_seconds,
        )
        self._budgets[session_id] = budget
        return budget

    def get(self, session_id: str) -> Budget | None:
        return self._budgets.get(session_id)

    def remove(self, session_id: str) -> None:
        self._budgets.pop(session_id, None)
