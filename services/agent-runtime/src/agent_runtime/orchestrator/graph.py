"""LangGraph anomaly-detector agent graph.

Nodes:
  ingest_signals       — validate and normalize incoming BehaviorSignal dicts
  score_anomaly        — compute IsolationForest anomaly score
  retrieve_mitre_context — RAG lookup for the detected tactic/technique
  escalate_to_responder — prepare T2 escalation payload (when score > 0.8)
  generate_alert       — produce the structured alert report

Conditional edge after score_anomaly:
  score > ESCALATION_THRESHOLD → escalate_to_responder → retrieve_mitre_context
  otherwise                    → retrieve_mitre_context

All nodes end at generate_alert → END.
"""
import logging
from datetime import datetime
from typing import Any

import numpy as np
from langgraph.graph import END, StateGraph
from opentelemetry import trace
from sklearn.ensemble import IsolationForest

from agent_runtime.orchestrator.state import AgentState

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

ESCALATION_THRESHOLD = 0.8


# ---------------------------------------------------------------------------
# Node implementations
# ---------------------------------------------------------------------------


def ingest_signals(state: AgentState) -> dict:
    """Node: validate and normalise incoming behavioral signals."""
    with tracer.start_as_current_span("node.ingest_signals") as span:
        raw_signals: list[dict] = state.get("signals", [])
        span.set_attribute("signal_count", len(raw_signals))

        processed: list[dict] = []
        for s in raw_signals:
            tool_calls = s.get("tool_calls", [])
            processed.append(
                {
                    "token_count": max(0, int(s.get("token_count", 0))),
                    "retrieval_count": max(0, int(s.get("retrieval_count", 0))),
                    "tool_call_count": sum(
                        max(0, int(t.get("invocation_count", 0))) for t in tool_calls
                    ),
                    "avg_tool_latency": (
                        float(np.mean([t.get("avg_latency_ms", 0.0) for t in tool_calls]))
                        if tool_calls
                        else 0.0
                    ),
                    "tool_diversity": len(tool_calls),
                    "window_seconds": max(1, int(s.get("window_seconds", 60))),
                    "timestamp": s.get("timestamp", datetime.utcnow().isoformat()),
                }
            )

        return {
            "signals": processed,
            "iteration_count": state.get("iteration_count", 0) + 1,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        f"Ingested {len(processed)} behavioral signal(s) "
                        f"for principal '{state.get('principal_id', 'unknown')}'"
                    ),
                }
            ],
        }


def score_anomaly(state: AgentState) -> dict:
    """Node: compute anomaly score using IsolationForest."""
    with tracer.start_as_current_span("node.score_anomaly") as span:
        signals = state.get("signals", [])

        if not signals:
            return {
                "anomaly_score": 0.0,
                "is_anomaly": False,
                "risk_factors": [],
                "mitre_tactic": "unknown",
                "mitre_technique": "T0000",
                "messages": [{"role": "assistant", "content": "No signals to score."}],
            }

        features_list = [
            [
                float(s["token_count"]),
                float(s["retrieval_count"]),
                float(s["tool_call_count"]),
                float(s["avg_tool_latency"]),
                float(s["tool_diversity"]),
                float(s["window_seconds"]),
            ]
            for s in signals
        ]
        latest = features_list[-1]

        if len(features_list) < 2:
            # Heuristic fallback for single-signal sessions
            normalized_score = 0.0
            risk_factors: list[str] = []
            if latest[0] > 100_000:
                normalized_score = max(normalized_score, 0.6)
                risk_factors.append("excessive_token_consumption")
            if latest[1] > 500:
                normalized_score = max(normalized_score, 0.65)
                risk_factors.append("mass_retrieval")
            if latest[2] > 50:
                normalized_score = max(normalized_score, 0.55)
                risk_factors.append("high_tool_invocation")
            is_anomaly = normalized_score >= 0.6
        else:
            X = np.array(features_list, dtype=float)
            clf = IsolationForest(contamination=0.1, random_state=42, n_estimators=100)
            clf.fit(X)
            raw = float(clf.score_samples([latest])[0])
            normalized_score = max(0.0, min(1.0, 1.0 - (raw + 0.5) / 0.5))
            is_anomaly = clf.predict([latest])[0] == -1
            risk_factors = []
            if latest[0] > 100_000:
                risk_factors.append("excessive_token_consumption")
            if latest[1] > 500:
                risk_factors.append("mass_retrieval")

        tactic, technique = _map_mitre(latest, normalized_score)

        span.set_attribute("anomaly_score", normalized_score)
        span.set_attribute("is_anomaly", is_anomaly)
        span.set_attribute("mitre_tactic", tactic)

        return {
            "anomaly_score": normalized_score,
            "is_anomaly": is_anomaly,
            "risk_factors": risk_factors,
            "mitre_tactic": tactic,
            "mitre_technique": technique,
            "messages": [
                {
                    "role": "assistant",
                    "content": (
                        f"Anomaly score: {normalized_score:.3f} | "
                        f"is_anomaly={is_anomaly} | "
                        f"MITRE: {tactic}/{technique}"
                    ),
                }
            ],
        }


def _map_mitre(features: list[float], score: float) -> tuple[str, str]:
    """Heuristic MITRE ATT&CK tactic/technique mapping."""
    token_count, retrieval_count, tool_count = features[0], features[1], features[2]
    if retrieval_count > 1000:
        return "collection", "T1213"
    if token_count > 500_000:
        return "exfiltration", "T1041"
    if tool_count > 100:
        return "execution", "T1059"
    if score > 0.8:
        return "discovery", "T1087"
    return "unknown", "T0000"


def retrieve_mitre_context(state: AgentState) -> dict:
    """Node: RAG retrieval of MITRE ATT&CK context for the detected tactic."""
    with tracer.start_as_current_span("node.retrieve_mitre_context") as span:
        tactic = state.get("mitre_tactic", "unknown")
        technique = state.get("mitre_technique", "T0000")
        span.set_attribute("mitre_tactic", tactic)
        span.set_attribute("mitre_technique", technique)

        # In production this calls the rag-core service / Azure AI Search.
        # Here we return a deterministic mock so the graph is self-contained.
        context = [
            {
                "source": "MITRE ATT&CK Enterprise",
                "technique_id": technique,
                "tactic": tactic,
                "description": (
                    f"Behavioral anomaly matching the '{tactic}' tactic was detected. "
                    f"Technique {technique} involves patterns consistent with the "
                    "observed signal deviations from established baselines."
                ),
                "mitigations": [
                    "Enforce per-agent token budget limits (M1038)",
                    "Monitor retrieval operation volume (M1048)",
                    "Require MFA for privileged agent actions (M1032)",
                    "Implement agent-to-agent communication controls (M1037)",
                ],
                "detection": (
                    "Behavioral anomaly scoring via IsolationForest on token consumption, "
                    "retrieval volume, and tool invocation patterns."
                ),
                "severity": "high" if state.get("anomaly_score", 0.0) > 0.7 else "medium",
            }
        ]

        return {
            "retrieved_context": context,
            "citations": [f"MITRE ATT&CK {technique} ({tactic})"],
            "messages": [
                {
                    "role": "assistant",
                    "content": f"Retrieved {len(context)} MITRE ATT&CK context entry/entries.",
                }
            ],
        }


def escalate_to_responder(state: AgentState) -> dict:
    """Node: prepare T2 escalation payload for the threat-responder agent."""
    with tracer.start_as_current_span("node.escalate_to_responder") as span:
        score = state.get("anomaly_score", 0.0)
        principal_id = state.get("principal_id", "unknown")
        span.set_attribute("principal_id", principal_id)
        span.set_attribute("anomaly_score", score)

        logger.warning(
            "escalating_to_t2_responder",
            principal_id=principal_id,
            anomaly_score=score,
            mitre_tactic=state.get("mitre_tactic", "unknown"),
        )

        return {
            "escalate_to_t2": True,
            "response_action": "isolate",
            "approval_required": True,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        f"ESCALATION: anomaly_score={score:.3f} exceeds threshold "
                        f"{ESCALATION_THRESHOLD}. Routing to T2 threat-responder. "
                        f"Approval required before isolation."
                    ),
                }
            ],
        }


def generate_alert(state: AgentState) -> dict:
    """Node: generate the structured alert report."""
    with tracer.start_as_current_span("node.generate_alert") as span:
        principal_id = state.get("principal_id", "unknown")
        score = state.get("anomaly_score", 0.0)
        span.set_attribute("principal_id", principal_id)

        risk_level = "CRITICAL" if score > 0.9 else "HIGH" if score > 0.7 else "MEDIUM" if score > 0.4 else "LOW"

        context_block = "\n".join(
            f"- [{ctx['technique_id']}] {ctx['description']}"
            for ctx in state.get("retrieved_context", [])
        )
        mitigation_block = ""
        for ctx in state.get("retrieved_context", []):
            for m in ctx.get("mitigations", []):
                mitigation_block += f"  • {m}\n"

        escalation_note = (
            "**ACTION REQUIRED**: Escalated to T2 threat-responder. Isolation pending approval."
            if state.get("escalate_to_t2")
            else "Continued behavioral monitoring recommended."
        )

        report = f"""# Agent Behavioral Anomaly Alert

**Principal:** {principal_id}
**Session:** {state.get('session_id', 'unknown')}
**Generated:** {datetime.utcnow().isoformat()}Z

## Risk Assessment

| Field | Value |
|-------|-------|
| Anomaly Score | {score:.3f} |
| Risk Level | {risk_level} |
| Is Anomaly | {state.get('is_anomaly', False)} |
| MITRE Tactic | {state.get('mitre_tactic', 'unknown')} |
| MITRE Technique | {state.get('mitre_technique', 'T0000')} |
| Risk Factors | {', '.join(state.get('risk_factors', [])) or 'none'} |

## MITRE ATT&CK Context

{context_block or 'No context retrieved.'}

## Recommended Mitigations

{mitigation_block or '  • No specific mitigations identified.'}

## Recommended Response

{escalation_note}

## Citations

{chr(10).join(f'- {c}' for c in state.get('citations', []))}
"""

        return {
            "report": report,
            "completed_at": datetime.utcnow().isoformat(),
            "messages": [{"role": "assistant", "content": "Alert report generated."}],
        }


# ---------------------------------------------------------------------------
# Conditional routing
# ---------------------------------------------------------------------------


def should_escalate(state: AgentState) -> str:
    """Conditional edge: route to escalation if anomaly score exceeds threshold."""
    score = state.get("anomaly_score")
    if score is not None and score > ESCALATION_THRESHOLD:
        return "escalate"
    return "alert"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def build_anomaly_detector_graph() -> Any:
    """Build and compile the anomaly-detector LangGraph."""
    workflow: StateGraph = StateGraph(AgentState)

    workflow.add_node("ingest_signals", ingest_signals)
    workflow.add_node("score_anomaly", score_anomaly)
    workflow.add_node("retrieve_mitre_context", retrieve_mitre_context)
    workflow.add_node("escalate_to_responder", escalate_to_responder)
    workflow.add_node("generate_alert", generate_alert)

    workflow.set_entry_point("ingest_signals")

    workflow.add_edge("ingest_signals", "score_anomaly")
    workflow.add_conditional_edges(
        "score_anomaly",
        should_escalate,
        {
            "escalate": "escalate_to_responder",
            "alert": "retrieve_mitre_context",
        },
    )
    workflow.add_edge("escalate_to_responder", "retrieve_mitre_context")
    workflow.add_edge("retrieve_mitre_context", "generate_alert")
    workflow.add_edge("generate_alert", END)

    return workflow.compile()


# Module-level compiled graph
anomaly_detector_graph = build_anomaly_detector_graph()
