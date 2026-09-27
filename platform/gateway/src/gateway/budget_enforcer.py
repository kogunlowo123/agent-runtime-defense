"""Budget enforcement for the platform gateway."""
from dataclasses import dataclass, field


@dataclass
class BudgetState:
    agent_id: str
    tokens_used: int = 0
    requests_made: int = 0
    cost_usd: float = 0.0


class BudgetEnforcer:
    """Tracks and enforces per-agent budget limits at the gateway level."""

    def __init__(self, max_tokens: int = 100_000, max_requests: int = 1000) -> None:
        self._max_tokens = max_tokens
        self._max_requests = max_requests
        self._state: dict[str, BudgetState] = {}

    def check_and_consume(self, agent_id: str, tokens: int = 0) -> bool:
        """Returns True if within budget; False if budget exceeded."""
        state = self._state.setdefault(agent_id, BudgetState(agent_id=agent_id))
        if state.tokens_used + tokens > self._max_tokens:
            return False
        if state.requests_made >= self._max_requests:
            return False
        state.tokens_used += tokens
        state.requests_made += 1
        return True

    def get_remaining(self, agent_id: str) -> dict:
        state = self._state.get(agent_id, BudgetState(agent_id=agent_id))
        return {
            "tokens_remaining": max(0, self._max_tokens - state.tokens_used),
            "requests_remaining": max(0, self._max_requests - state.requests_made),
        }
