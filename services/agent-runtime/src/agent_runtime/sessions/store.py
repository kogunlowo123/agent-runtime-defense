"""Session store: manages agent session lifecycle."""
from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass, field
from enum import Enum


class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"


@dataclass
class Session:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    principal_id: str = ""
    agent_type: str = ""
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z")
    metadata: dict = field(default_factory=dict)
    token_count: int = 0
    tool_call_count: int = 0


class SessionStore:
    """In-memory session lifecycle manager."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create(self, principal_id: str, agent_type: str, metadata: dict | None = None) -> Session:
        session = Session(principal_id=principal_id, agent_type=agent_type, metadata=metadata or {})
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def update_status(self, session_id: str, status: SessionStatus) -> Session | None:
        session = self._sessions.get(session_id)
        if session:
            session.status = status
            session.updated_at = datetime.datetime.utcnow().isoformat() + "Z"
        return session

    def record_usage(self, session_id: str, tokens: int, tool_calls: int) -> None:
        session = self._sessions.get(session_id)
        if session:
            session.token_count += tokens
            session.tool_call_count += tool_calls
            session.updated_at = datetime.datetime.utcnow().isoformat() + "Z"

    def active_count(self) -> int:
        return sum(1 for s in self._sessions.values() if s.status == SessionStatus.ACTIVE)
