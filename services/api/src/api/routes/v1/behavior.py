"""Behavior scoring and baseline retrieval endpoints."""
from datetime import datetime
from typing import Annotated

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from opentelemetry import trace
from sklearn.ensemble import IsolationForest

from api.config import Settings, get_settings
from api.schemas.behavior import (
    AnomalyScore,
    BehaviorBaseline,
    BehaviorSignal,
    MitreTactic,
)

router = APIRouter(prefix="/behavior", tags=["behavior"])
tracer = trace.get_tracer(__name__)

# In-memory baseline store — indexed by principal_id
# Each value is a list of feature vectors (list[list[float]])
_baselines: dict[str, list[list[float]]] = {}
_baseline_meta: dict[str, dict] = {}  # stores agent_class and tool names


def _extract_feature_vector(signal: BehaviorSignal) -> list[float]:
    """Extract a numeric feature vector from a BehaviorSignal."""
    tool_call_total = sum(tc.invocation_count for tc in signal.tool_calls)
    avg_tool_latency: float = (
        float(np.mean([tc.avg_latency_ms for tc in signal.tool_calls]))
        if signal.tool_calls
        else 0.0
    )
    return [
        float(signal.token_count),
        float(signal.retrieval_count),
        float(tool_call_total),
        float(avg_tool_latency),
        float(len(signal.tool_calls)),
        float(signal.window_seconds),
    ]


def _score_with_isolation_forest(
    features: list[float],
    principal_id: str,
    contamination: float = 0.1,
) -> tuple[float, bool]:
    """Fit IsolationForest on accumulated history and score latest observation."""
    history = _baselines.get(principal_id, [])
    history.append(features)
    # Keep most recent 500 observations to cap memory
    _baselines[principal_id] = history[-500:]

    if len(history) < 10:
        # Insufficient history — use simple heuristic threshold
        token_count = features[0]
        retrieval_count = features[1]
        tool_total = features[2]

        normalized = 0.0
        if token_count > 100_000:
            normalized = max(normalized, 0.6)
        if retrieval_count > 500:
            normalized = max(normalized, 0.65)
        if tool_total > 50:
            normalized = max(normalized, 0.55)
        return normalized, normalized >= 0.6

    X = np.array(_baselines[principal_id], dtype=float)
    model = IsolationForest(contamination=contamination, random_state=42, n_estimators=100)
    model.fit(X)

    raw_score = float(model.score_samples([features])[0])
    # score_samples returns average anomaly score; more negative means more anomalous.
    # Typical range ~ [-0.5, 0]. Map to [0, 1] with 0 = normal, 1 = maximally anomalous.
    normalized = max(0.0, min(1.0, 1.0 - (raw_score + 0.5) / 0.5))
    is_anomaly = model.predict([features])[0] == -1
    return normalized, is_anomaly


def _map_to_mitre(features: list[float], normalized_score: float) -> tuple[MitreTactic, str]:
    """Heuristic mapping from behavioral features to MITRE ATT&CK tactic/technique."""
    token_count, retrieval_count, tool_total = features[0], features[1], features[2]

    if retrieval_count > 1000:
        return MitreTactic.COLLECTION, "T1213"
    if token_count > 500_000:
        return MitreTactic.EXFILTRATION, "T1041"
    if tool_total > 100:
        return MitreTactic.EXECUTION, "T1059"
    if normalized_score > 0.8:
        return MitreTactic.DISCOVERY, "T1087"
    return MitreTactic.UNKNOWN, "T0000"


def _collect_risk_factors(signal: BehaviorSignal) -> list[str]:
    """Identify human-readable risk factors from a signal."""
    factors: list[str] = []
    if signal.token_count > 100_000:
        factors.append("excessive_token_consumption")
    if signal.retrieval_count > 500:
        factors.append("mass_retrieval")
    if len(signal.tool_calls) > 50:
        factors.append("high_tool_diversity")
    if any(tc.avg_latency_ms < 1.0 for tc in signal.tool_calls):
        factors.append("suspiciously_fast_tool_calls")
    return factors


@router.post("/score", response_model=AnomalyScore, status_code=200)
async def score_behavior(
    signal: BehaviorSignal,
    settings: Annotated[Settings, Depends(get_settings)],
) -> AnomalyScore:
    """
    Score behavioral signals for a principal and return an anomaly score
    with MITRE ATT&CK tactic mapping.
    """
    with tracer.start_as_current_span("behavior.score") as span:
        span.set_attribute("principal_id", signal.principal_id)
        span.set_attribute("agent_class", signal.agent_class)
        span.set_attribute("token_count", signal.token_count)
        span.set_attribute("retrieval_count", signal.retrieval_count)

        # Record agent class metadata
        _baseline_meta[signal.principal_id] = {
            "agent_class": signal.agent_class,
            "tools": [tc.tool_name for tc in signal.tool_calls],
        }

        features = _extract_feature_vector(signal)
        normalized_score, is_anomaly = _score_with_isolation_forest(
            features,
            signal.principal_id,
            contamination=settings.anomaly_detection_contamination,
        )
        mitre_tactic, mitre_technique = _map_to_mitre(features, normalized_score)
        risk_factors = _collect_risk_factors(signal)

        # Convert normalized score back to [-1, 1] for the AnomalyScore.score field
        raw_score = (1.0 - normalized_score) * 2 - 1.0

        span.set_attribute("is_anomaly", is_anomaly)
        span.set_attribute("normalized_score", normalized_score)
        span.set_attribute("mitre_tactic", mitre_tactic.value)

        return AnomalyScore(
            principal_id=signal.principal_id,
            session_id=signal.session_id,
            score=raw_score,
            normalized_score=normalized_score,
            is_anomaly=is_anomaly,
            mitre_tactic=mitre_tactic,
            mitre_technique=mitre_technique,
            risk_factors=risk_factors,
            timestamp=datetime.utcnow(),
        )


@router.get("/{principal_id}", response_model=BehaviorBaseline)
async def get_baseline(principal_id: str) -> BehaviorBaseline:
    """Retrieve the behavioral baseline statistics for a given principal."""
    with tracer.start_as_current_span("behavior.get_baseline") as span:
        span.set_attribute("principal_id", principal_id)

        history = _baselines.get(principal_id)
        if not history:
            raise HTTPException(
                status_code=404,
                detail=f"No behavioral baseline found for principal: {principal_id}",
            )

        arr = np.array(history, dtype=float)
        # Column layout: [token_count, retrieval_count, tool_total, avg_latency, diversity, window]
        meta = _baseline_meta.get(principal_id, {})

        return BehaviorBaseline(
            principal_id=principal_id,
            agent_class=meta.get("agent_class", "unknown"),
            avg_token_count=float(np.mean(arr[:, 0])),
            p95_token_count=float(np.percentile(arr[:, 0], 95)),
            avg_retrieval_count=float(np.mean(arr[:, 1])),
            p95_retrieval_count=float(np.percentile(arr[:, 1], 95)),
            common_tools=list(meta.get("tools", [])),
            baseline_window_days=7,
            sample_count=len(history),
            last_updated=datetime.utcnow(),
            is_established=len(history) >= 10,
        )
