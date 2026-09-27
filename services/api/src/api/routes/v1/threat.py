"""Threat signal ingestion endpoint."""
from datetime import datetime
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends
from opentelemetry import trace

from api.config import Settings, get_settings
from api.schemas.threat import ThreatSignal, ThreatSignalResponse, ThreatSeverity

router = APIRouter(prefix="/threat", tags=["threat"])
tracer = trace.get_tracer(__name__)
logger = structlog.get_logger(__name__)

# In-memory threat signal store: signal_id -> ThreatSignal
_signals: dict[UUID, ThreatSignal] = {}


@router.post("/signal", response_model=ThreatSignalResponse, status_code=201)
async def ingest_threat_signal(
    signal: ThreatSignal,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ThreatSignalResponse:
    """
    Ingest an external threat signal from CISA, MITRE, ISACs, or internal sources.
    Critical signals are automatically escalated.
    """
    with tracer.start_as_current_span("threat.ingest_signal") as span:
        span.set_attribute("signal_id", str(signal.signal_id))
        span.set_attribute("severity", signal.severity.value)
        span.set_attribute("source", signal.source.value)

        # Persist in-memory
        _signals[signal.signal_id] = signal

        escalated = signal.severity == ThreatSeverity.CRITICAL

        logger.info(
            "threat_signal_received",
            signal_id=str(signal.signal_id),
            severity=signal.severity.value,
            source=signal.source.value,
            escalated=escalated,
            affected_agent_classes=signal.affected_agent_classes,
        )

        if escalated:
            span.set_attribute("escalated", True)
            logger.warning(
                "critical_threat_signal_escalated",
                signal_id=str(signal.signal_id),
                title=signal.title,
            )

        # Count how many currently active signals affect the same agent classes
        affected_count = sum(
            1
            for s in _signals.values()
            if any(ac in s.affected_agent_classes for ac in signal.affected_agent_classes)
        )

        return ThreatSignalResponse(
            signal_id=signal.signal_id,
            status="accepted",
            indexed=True,
            escalated=escalated,
            affected_count=affected_count,
            timestamp=datetime.utcnow(),
        )
