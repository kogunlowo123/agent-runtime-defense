"""Pydantic schemas for isolation and response actions."""
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ResponseAction(str, Enum):
    ALERT = "alert"
    ISOLATE = "isolate"
    REVOKE = "revoke"
    THROTTLE = "throttle"
    MONITOR = "monitor"


class ResponseStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class IsolationRequest(BaseModel):
    principal_id: str = Field(..., min_length=1, max_length=256)
    action: ResponseAction
    reason: str = Field(..., min_length=10, max_length=2048)
    anomaly_score_ref: UUID | None = None
    requestor_id: str = Field(..., min_length=1, max_length=256)
    approval_token: str | None = Field(
        default=None, description="Required for T2 actions (ISOLATE, REVOKE)"
    )
    ttl_seconds: int = Field(default=3600, ge=60, le=86400)


class IsolationResponse(BaseModel):
    response_id: UUID = Field(default_factory=uuid4)
    principal_id: str
    action: ResponseAction
    status: ResponseStatus
    requires_approval: bool
    approval_url: str | None = None
    executed_at: datetime | None = None
    expires_at: datetime | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
