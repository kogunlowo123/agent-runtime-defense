"""T2 approval gate: holds actions pending human or automated approval."""
from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass, field
from enum import Enum


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class ApprovalRequest:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action: str = ""
    principal_id: str = ""
    reason: str = ""
    context: dict = field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: str = field(
        default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z"
    )
    resolved_at: str = ""
    resolved_by: str = ""
    ttl_seconds: int = 3600


class ApprovalStore:
    """In-memory store for pending T2 approval requests."""

    def __init__(self) -> None:
        self._store: dict[str, ApprovalRequest] = {}

    def create(
        self,
        action: str,
        principal_id: str,
        reason: str,
        context: dict | None = None,
        ttl_seconds: int = 3600,
    ) -> ApprovalRequest:
        req = ApprovalRequest(
            action=action,
            principal_id=principal_id,
            reason=reason,
            context=context or {},
            ttl_seconds=ttl_seconds,
        )
        self._store[req.request_id] = req
        return req

    def get(self, request_id: str) -> ApprovalRequest | None:
        req = self._store.get(request_id)
        if req and req.status == ApprovalStatus.PENDING:
            created = datetime.datetime.fromisoformat(req.created_at.rstrip("Z"))
            age = (datetime.datetime.utcnow() - created).total_seconds()
            if age > req.ttl_seconds:
                req.status = ApprovalStatus.EXPIRED
        return req

    def resolve(
        self, request_id: str, approved: bool, resolved_by: str
    ) -> ApprovalRequest | None:
        req = self.get(request_id)
        if req is None or req.status != ApprovalStatus.PENDING:
            return req
        req.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        req.resolved_at = datetime.datetime.utcnow().isoformat() + "Z"
        req.resolved_by = resolved_by
        return req
