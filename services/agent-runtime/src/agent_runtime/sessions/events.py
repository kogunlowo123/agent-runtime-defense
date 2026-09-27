"""CloudEvents for session lifecycle and anomaly events."""
from __future__ import annotations

import datetime
import json
import uuid
from dataclasses import asdict, dataclass


@dataclass
class CloudEvent:
    specversion: str = "1.0"
    type: str = ""
    source: str = "agent-runtime-defense/sessions"
    id: str = ""
    time: str = ""
    datacontenttype: str = "application/json"
    data: dict = None

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.time:
            self.time = datetime.datetime.utcnow().isoformat() + "Z"
        if self.data is None:
            self.data = {}

    def to_json(self) -> str:
        return json.dumps(asdict(self))


def session_started_event(session_id: str, principal_id: str) -> CloudEvent:
    return CloudEvent(
        type="agent.runtime.session.started",
        data={"session_id": session_id, "principal_id": principal_id},
    )


def session_terminated_event(session_id: str, reason: str) -> CloudEvent:
    return CloudEvent(
        type="agent.runtime.session.terminated",
        data={"session_id": session_id, "reason": reason},
    )


def anomaly_detected_event(
    session_id: str,
    principal_id: str,
    score: float,
    mitre_tactics: list[str],
) -> CloudEvent:
    return CloudEvent(
        type="anomaly.detected",
        data={
            "session_id": session_id,
            "principal_id": principal_id,
            "anomaly_score": score,
            "mitre_tactics": mitre_tactics,
        },
    )
