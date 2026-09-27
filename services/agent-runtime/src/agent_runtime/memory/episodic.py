"""Episodic memory: persists agent observations across sessions."""
from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass, field


@dataclass
class Episode:
    episode_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    principal_id: str = ""
    summary: str = ""
    key_events: list[str] = field(default_factory=list)
    anomaly_score: float = 0.0
    mitre_tactics: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z")


class EpisodicMemory:
    """In-memory episodic store with retrieval by principal_id."""

    def __init__(self, max_episodes_per_principal: int = 100) -> None:
        self._store: dict[str, list[Episode]] = {}
        self._max = max_episodes_per_principal

    def record(self, episode: Episode) -> None:
        episodes = self._store.setdefault(episode.principal_id, [])
        episodes.append(episode)
        if len(episodes) > self._max:
            episodes.pop(0)

    def recall(self, principal_id: str, limit: int = 10) -> list[Episode]:
        return self._store.get(principal_id, [])[-limit:]

    def clear(self, principal_id: str) -> None:
        self._store.pop(principal_id, None)
