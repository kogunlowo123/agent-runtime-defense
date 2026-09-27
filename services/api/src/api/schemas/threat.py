"""Pydantic schemas for threat signal ingestion."""
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ThreatSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatSignalSource(str, Enum):
    INTERNAL = "internal"
    CISA = "cisa"
    MITRE = "mitre"
    ISAC = "isac"
    MANUAL = "manual"


class ThreatSignal(BaseModel):
    signal_id: UUID = Field(default_factory=uuid4)
    source: ThreatSignalSource
    severity: ThreatSeverity
    title: str = Field(..., min_length=1, max_length=512)
    description: str = Field(..., min_length=1)
    iocs: list[str] = Field(default_factory=list, description="Indicators of compromise")
    affected_agent_classes: list[str] = Field(default_factory=list)
    mitre_techniques: list[str] = Field(default_factory=list)
    reference_urls: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    expiry: datetime | None = None
    tags: list[str] = Field(default_factory=list)


class ThreatSignalResponse(BaseModel):
    signal_id: UUID
    status: str
    indexed: bool
    escalated: bool
    affected_count: int
    timestamp: datetime
