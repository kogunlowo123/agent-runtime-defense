"""Audit logging for the platform gateway."""
import datetime
import json
import logging
from dataclasses import asdict, dataclass

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    timestamp: str
    agent_id: str
    path: str
    method: str
    status_code: int
    tokens_consumed: int
    latency_ms: float
    action: str = ""


class AuditLogger:
    """Writes structured audit entries for every gateway request."""

    def log(self, entry: AuditEntry) -> None:
        logger.info(json.dumps(asdict(entry)))

    def record(
        self,
        agent_id: str,
        path: str,
        method: str,
        status_code: int,
        tokens_consumed: int,
        latency_ms: float,
        action: str = "",
    ) -> None:
        entry = AuditEntry(
            timestamp=datetime.datetime.utcnow().isoformat() + "Z",
            agent_id=agent_id,
            path=path,
            method=method,
            status_code=status_code,
            tokens_consumed=tokens_consumed,
            latency_ms=latency_ms,
            action=action,
        )
        self.log(entry)
