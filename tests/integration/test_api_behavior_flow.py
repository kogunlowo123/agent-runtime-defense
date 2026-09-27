"""Integration tests for the behavior scoring API flow."""
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parents[2] / "services" / "api" / "src"))

from api.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=True)


class TestHealthEndpoints:
    """Tests for /health and /readiness."""

    def test_health_returns_200(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"
        assert "timestamp" in data

    def test_readiness_returns_200(self, client: TestClient) -> None:
        response = client.get("/readiness")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("ok", "degraded")
        assert "checks" in data
        assert "api" in data["checks"]


class TestBehaviorScoreEndpoint:
    """Tests for POST /api/v1/behavior/score."""

    def _make_payload(self, **overrides) -> dict:
        base = {
            "principal_id": f"test-agent-{int(time.time() * 1000)}",
            "agent_class": "anomaly-detector",
            "token_count": 1000,
            "retrieval_count": 10,
            "tool_calls": [
                {"tool_name": "rag_search", "invocation_count": 3, "avg_latency_ms": 120.0}
            ],
            "window_seconds": 60,
        }
        base.update(overrides)
        return base

    def test_score_normal_behavior_returns_200(self, client: TestClient) -> None:
        response = client.post("/api/v1/behavior/score", json=self._make_payload())
        assert response.status_code == 200
        data = response.json()
        assert "score" in data
        assert "normalized_score" in data
        assert "is_anomaly" in data
        assert "mitre_tactic" in data
        assert "mitre_technique" in data
        assert "risk_factors" in data
        assert "principal_id" in data

    def test_score_response_schema_compliance(self, client: TestClient) -> None:
        payload = self._make_payload(principal_id="schema-test-agent", token_count=500)
        response = client.post("/api/v1/behavior/score", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert -1.0 <= data["score"] <= 1.0
        assert 0.0 <= data["normalized_score"] <= 1.0
        assert isinstance(data["is_anomaly"], bool)
        assert isinstance(data["risk_factors"], list)

    def test_score_excessive_token_flags_risk_factor(self, client: TestClient) -> None:
        payload = self._make_payload(
            principal_id="high-token-agent",
            token_count=200_000,
        )
        response = client.post("/api/v1/behavior/score", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "excessive_token_consumption" in data["risk_factors"]

    def test_score_mass_retrieval_flags_risk_factor(self, client: TestClient) -> None:
        payload = self._make_payload(
            principal_id="mass-retrieval-agent",
            retrieval_count=1000,
        )
        response = client.post("/api/v1/behavior/score", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "mass_retrieval" in data["risk_factors"]

    def test_score_invalid_payload_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/behavior/score",
            json={"principal_id": "", "agent_class": "test", "token_count": -1, "retrieval_count": 0},
        )
        assert response.status_code == 422

    def test_score_missing_required_fields_returns_422(self, client: TestClient) -> None:
        response = client.post("/api/v1/behavior/score", json={"token_count": 100})
        assert response.status_code == 422

    def test_baseline_not_found_before_first_score(self, client: TestClient) -> None:
        principal = f"never-seen-agent-{int(time.time() * 1000)}"
        response = client.get(f"/api/v1/behavior/{principal}")
        assert response.status_code == 404

    def test_baseline_available_after_sufficient_scores(self, client: TestClient) -> None:
        principal = f"baseline-build-agent-{int(time.time() * 1000)}"
        # Submit enough signals to establish a baseline
        for i in range(15):
            client.post(
                "/api/v1/behavior/score",
                json={
                    "principal_id": principal,
                    "agent_class": "anomaly-detector",
                    "token_count": 1000 + i * 50,
                    "retrieval_count": 10 + i,
                    "window_seconds": 60,
                },
            )

        response = client.get(f"/api/v1/behavior/{principal}")
        assert response.status_code == 200
        data = response.json()
        assert data["is_established"] is True
        assert data["sample_count"] == 15
        assert data["avg_token_count"] > 0


class TestThreatSignalEndpoint:
    """Tests for POST /api/v1/threat/signal."""

    def test_ingest_signal_returns_201(self, client: TestClient) -> None:
        payload = {
            "source": "cisa",
            "severity": "high",
            "title": "Agent credential harvesting campaign detected",
            "description": "Threat actors exploiting LLM agents to harvest credentials via retrieval abuse.",
            "mitre_techniques": ["T1078", "T1213"],
            "affected_agent_classes": ["behavior-analyst"],
        }
        response = client.post("/api/v1/threat/signal", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "accepted"
        assert data["indexed"] is True
        assert "signal_id" in data

    def test_critical_signal_escalated(self, client: TestClient) -> None:
        payload = {
            "source": "internal",
            "severity": "critical",
            "title": "Active exploitation of T2 approval bypass",
            "description": "Active exploitation detected: T2 approval gate bypass in threat-responder agent.",
        }
        response = client.post("/api/v1/threat/signal", json=payload)
        assert response.status_code == 201
        assert response.json()["escalated"] is True

    def test_non_critical_signal_not_escalated(self, client: TestClient) -> None:
        payload = {
            "source": "manual",
            "severity": "low",
            "title": "Minor policy deviation in tool invocation pattern",
            "description": "Low-severity policy deviation observed in tool invocation patterns.",
        }
        response = client.post("/api/v1/threat/signal", json=payload)
        assert response.status_code == 201
        assert response.json()["escalated"] is False


class TestResponseIsolateEndpoint:
    """Tests for POST /api/v1/response/isolate."""

    def test_alert_action_executes_immediately(self, client: TestClient) -> None:
        payload = {
            "principal_id": "agent-to-alert",
            "action": "alert",
            "reason": "Anomaly score exceeded threshold for extended period",
            "requestor_id": "system-monitor",
        }
        response = client.post("/api/v1/response/isolate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["requires_approval"] is False

    def test_isolate_without_token_returns_pending(self, client: TestClient) -> None:
        payload = {
            "principal_id": "agent-to-isolate",
            "action": "isolate",
            "reason": "Critical anomaly detected - initiating isolation protocol",
            "requestor_id": "anomaly-detector",
        }
        response = client.post("/api/v1/response/isolate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending_approval"
        assert data["requires_approval"] is True
        assert data["approval_url"] is not None
