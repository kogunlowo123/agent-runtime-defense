"""Pydantic schemas for behavioral signal scoring."""
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class MitreTactic(str, Enum):
    INITIAL_ACCESS = "initial-access"
    EXECUTION = "execution"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege-escalation"
    DEFENSE_EVASION = "defense-evasion"
    CREDENTIAL_ACCESS = "credential-access"
    DISCOVERY = "discovery"
    LATERAL_MOVEMENT = "lateral-movement"
    COLLECTION = "collection"
    EXFILTRATION = "exfiltration"
    IMPACT = "impact"
    RESOURCE_DEVELOPMENT = "resource-development"
    UNKNOWN = "unknown"


class ToolCall(BaseModel):
    tool_name: str = Field(..., min_length=1, max_length=256)
    invocation_count: int = Field(..., ge=0)
    avg_latency_ms: float = Field(..., ge=0.0)


class BehaviorSignal(BaseModel):
    principal_id: str = Field(
        ..., min_length=1, max_length=256, description="Agent or session identifier"
    )
    agent_class: str = Field(..., min_length=1, max_length=128)
    token_count: int = Field(..., ge=0, description="Total tokens consumed in this window")
    retrieval_count: int = Field(..., ge=0, description="Vector retrieval operations count")
    tool_calls: list[ToolCall] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: UUID = Field(default_factory=uuid4)
    window_seconds: int = Field(default=60, ge=1, le=3600)

    @field_validator("token_count")
    @classmethod
    def token_count_reasonable(cls, v: int) -> int:
        if v > 10_000_000:
            raise ValueError("token_count exceeds maximum reasonable value of 10M")
        return v


class AnomalyScore(BaseModel):
    principal_id: str
    session_id: UUID
    score: float = Field(
        ..., ge=-1.0, le=1.0, description="Raw anomaly score; negative = more anomalous"
    )
    normalized_score: float = Field(..., ge=0.0, le=1.0, description="Normalized 0-1 risk score")
    is_anomaly: bool
    mitre_tactic: MitreTactic
    mitre_technique: str = Field(..., description="MITRE ATT&CK technique ID e.g. T1213")
    risk_factors: list[str]
    timestamp: datetime
    model_version: str = "1.0.0"


class BehaviorBaseline(BaseModel):
    principal_id: str
    agent_class: str
    avg_token_count: float
    p95_token_count: float
    avg_retrieval_count: float
    p95_retrieval_count: float
    common_tools: list[str]
    baseline_window_days: int
    sample_count: int
    last_updated: datetime
    is_established: bool = Field(
        default=False, description="True when enough samples have been collected"
    )
