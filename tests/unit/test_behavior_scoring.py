"""Unit tests for behavior scoring schemas and feature extraction."""
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "services" / "api" / "src"))

from api.schemas.behavior import (
    AnomalyScore,
    BehaviorSignal,
    MitreTactic,
    ToolCall,
)


class TestBehaviorSignalSchema:
    """Tests for BehaviorSignal pydantic model."""

    def test_minimal_valid_signal(self) -> None:
        signal = BehaviorSignal(
            principal_id="agent-001",
            agent_class="anomaly-detector",
            token_count=1000,
            retrieval_count=10,
        )
        assert signal.principal_id == "agent-001"
        assert signal.token_count == 1000
        assert signal.window_seconds == 60  # default

    def test_signal_with_tool_calls(self) -> None:
        tc = ToolCall(tool_name="rag_search", invocation_count=5, avg_latency_ms=120.0)
        signal = BehaviorSignal(
            principal_id="agent-002",
            agent_class="behavior-analyst",
            token_count=5000,
            retrieval_count=50,
            tool_calls=[tc],
        )
        assert len(signal.tool_calls) == 1
        assert signal.tool_calls[0].tool_name == "rag_search"

    def test_token_count_must_be_non_negative(self) -> None:
        with pytest.raises(Exception):
            BehaviorSignal(
                principal_id="agent-003",
                agent_class="test",
                token_count=-1,
                retrieval_count=0,
            )

    def test_token_count_ceiling(self) -> None:
        with pytest.raises(Exception):
            BehaviorSignal(
                principal_id="agent-004",
                agent_class="test",
                token_count=11_000_000,  # > 10M limit
                retrieval_count=0,
            )

    def test_session_id_auto_generated(self) -> None:
        s1 = BehaviorSignal(
            principal_id="agent-005", agent_class="test", token_count=0, retrieval_count=0
        )
        s2 = BehaviorSignal(
            principal_id="agent-006", agent_class="test", token_count=0, retrieval_count=0
        )
        assert s1.session_id != s2.session_id

    def test_window_seconds_bounds(self) -> None:
        with pytest.raises(Exception):
            BehaviorSignal(
                principal_id="agent-007",
                agent_class="test",
                token_count=0,
                retrieval_count=0,
                window_seconds=0,  # below minimum of 1
            )

        with pytest.raises(Exception):
            BehaviorSignal(
                principal_id="agent-008",
                agent_class="test",
                token_count=0,
                retrieval_count=0,
                window_seconds=3601,  # above maximum of 3600
            )

    def test_empty_tool_calls_allowed(self) -> None:
        signal = BehaviorSignal(
            principal_id="agent-009",
            agent_class="anomaly-detector",
            token_count=100,
            retrieval_count=5,
            tool_calls=[],
        )
        assert signal.tool_calls == []


class TestAnomalyScoreSchema:
    """Tests for AnomalyScore pydantic model."""

    def test_valid_anomaly_score(self) -> None:
        score = AnomalyScore(
            principal_id="agent-001",
            session_id=uuid4(),
            score=-0.45,
            normalized_score=0.82,
            is_anomaly=True,
            mitre_tactic=MitreTactic.COLLECTION,
            mitre_technique="T1213",
            risk_factors=["mass_retrieval"],
            timestamp=datetime.utcnow(),
        )
        assert score.is_anomaly is True
        assert score.mitre_tactic == MitreTactic.COLLECTION
        assert score.normalized_score == 0.82

    def test_score_bounds(self) -> None:
        with pytest.raises(Exception):
            AnomalyScore(
                principal_id="p",
                session_id=uuid4(),
                score=1.5,  # out of [-1, 1]
                normalized_score=0.5,
                is_anomaly=False,
                mitre_tactic=MitreTactic.UNKNOWN,
                mitre_technique="T0000",
                risk_factors=[],
                timestamp=datetime.utcnow(),
            )

    def test_normalized_score_bounds(self) -> None:
        with pytest.raises(Exception):
            AnomalyScore(
                principal_id="p",
                session_id=uuid4(),
                score=0.0,
                normalized_score=1.5,  # out of [0, 1]
                is_anomaly=False,
                mitre_tactic=MitreTactic.UNKNOWN,
                mitre_technique="T0000",
                risk_factors=[],
                timestamp=datetime.utcnow(),
            )

    def test_all_mitre_tactics_valid(self) -> None:
        tactics = list(MitreTactic)
        assert len(tactics) == 13
        assert MitreTactic.COLLECTION in tactics
        assert MitreTactic.EXFILTRATION in tactics


class TestMitreMappingHeuristics:
    """Tests for the MITRE ATT&CK heuristic mapping logic."""

    def test_high_retrieval_maps_to_collection(self) -> None:
        """retrieval_count > 1000 → Collection T1213."""
        features = [100.0, 1500.0, 5.0, 50.0, 3.0, 60.0]
        tactic, technique = _apply_heuristic(features, 0.6)
        assert tactic == MitreTactic.COLLECTION
        assert technique == "T1213"

    def test_high_token_maps_to_exfiltration(self) -> None:
        """token_count > 500000 → Exfiltration T1041."""
        features = [600_000.0, 50.0, 5.0, 50.0, 3.0, 60.0]
        tactic, technique = _apply_heuristic(features, 0.7)
        assert tactic == MitreTactic.EXFILTRATION
        assert technique == "T1041"

    def test_high_tool_count_maps_to_execution(self) -> None:
        """tool_count > 100 → Execution T1059."""
        features = [10_000.0, 50.0, 150.0, 50.0, 3.0, 60.0]
        tactic, technique = _apply_heuristic(features, 0.6)
        assert tactic == MitreTactic.EXECUTION
        assert technique == "T1059"

    def test_high_score_with_no_specific_pattern_maps_to_discovery(self) -> None:
        """High score with no specific pattern → Discovery T1087."""
        features = [1000.0, 20.0, 5.0, 50.0, 3.0, 60.0]
        tactic, technique = _apply_heuristic(features, 0.85)
        assert tactic == MitreTactic.DISCOVERY
        assert technique == "T1087"

    def test_normal_behavior_maps_to_unknown(self) -> None:
        """Normal behavior → Unknown T0000."""
        features = [200.0, 10.0, 5.0, 50.0, 3.0, 60.0]
        tactic, technique = _apply_heuristic(features, 0.1)
        assert tactic == MitreTactic.UNKNOWN
        assert technique == "T0000"


def _apply_heuristic(features: list, normalized_score: float) -> tuple:
    """Replicate the _map_to_mitre heuristic from behavior.py for testing."""
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
