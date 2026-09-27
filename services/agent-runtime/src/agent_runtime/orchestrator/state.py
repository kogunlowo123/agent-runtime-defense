"""LangGraph agent state definition for anomaly-detector and threat-responder."""
import operator
from typing import Annotated, TypedDict


class AgentState(TypedDict):
    """Shared state threaded through the LangGraph execution."""

    # --- Input ---
    principal_id: str
    session_id: str
    signals: list[dict]  # raw BehaviorSignal dicts

    # --- Processing ---
    baseline: dict | None
    anomaly_score: float | None
    is_anomaly: bool
    risk_factors: list[str]

    # --- MITRE ATT&CK ---
    mitre_tactic: str
    mitre_technique: str
    retrieved_context: list[dict]  # RAG results from MITRE ATT&CK knowledge base

    # --- Output ---
    report: str
    citations: list[str]

    # --- Control Flow ---
    escalate_to_t2: bool
    response_action: str | None
    approval_required: bool

    # --- Conversation ---
    messages: Annotated[list[dict], operator.add]

    # --- Metadata ---
    iteration_count: int
    started_at: str
    completed_at: str | None
    error: str | None
