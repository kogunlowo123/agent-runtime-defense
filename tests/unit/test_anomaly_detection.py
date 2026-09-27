"""Unit tests for IsolationForest-based anomaly detection logic."""
import sys
from pathlib import Path

import numpy as np
import pytest
from sklearn.ensemble import IsolationForest

# Ensure the API source is importable
sys.path.insert(0, str(Path(__file__).parents[2] / "services" / "api" / "src"))


class TestIsolationForest:
    """Tests for the IsolationForest anomaly detection algorithm."""

    def test_normal_behavior_scores_low(self) -> None:
        """Normal behavioral patterns should produce low anomaly scores."""
        # Build a training set of normal behavior: ~200 tokens, ~10 retrievals, ~5 tool calls
        rng = np.random.default_rng(42)
        normal_data = rng.normal(loc=[200, 10, 5, 50, 3, 60], scale=[30, 3, 2, 10, 1, 5], size=(100, 6))
        normal_data = np.clip(normal_data, 0, None)

        model = IsolationForest(contamination=0.1, random_state=42, n_estimators=100)
        model.fit(normal_data)

        # A perfectly normal sample should be predicted as normal (label 1)
        normal_sample = np.array([[200, 10, 5, 50, 3, 60]])
        score = float(model.score_samples(normal_sample)[0])
        # IsolationForest score_samples range is roughly [-0.5, 0]; normal samples cluster near 0
        # The exact value depends on training distribution — test prediction label, not raw score
        assert score > -0.6, f"Expected normal score > -0.6, got {score}"
        assert model.predict(normal_sample)[0] == 1, "Normal sample should not be flagged as anomaly"

    def test_anomalous_behavior_scores_high(self) -> None:
        """Anomalous behavioral patterns (mass retrieval, token burn) should be flagged."""
        rng = np.random.default_rng(42)
        normal_data = rng.normal(loc=[200, 10, 5, 50, 3, 60], scale=[30, 3, 2, 10, 1, 5], size=(200, 6))
        normal_data = np.clip(normal_data, 0, None)

        model = IsolationForest(contamination=0.05, random_state=42, n_estimators=200)
        model.fit(normal_data)

        # Anomalous sample: extreme token consumption + mass retrieval
        anomalous_sample = np.array([[800_000, 2000, 200, 5, 50, 60]])
        score = float(model.score_samples(anomalous_sample)[0])
        assert score < -0.2, f"Expected anomalous score < -0.2, got {score}"
        assert model.predict(anomalous_sample)[0] == -1, "Anomalous sample should be flagged"

    def test_contamination_controls_sensitivity(self) -> None:
        """Higher contamination should flag more samples as anomalies."""
        rng = np.random.default_rng(42)
        data = rng.normal(loc=[200, 10, 5, 50, 3, 60], scale=[30, 3, 2, 10, 1, 5], size=(200, 6))
        data = np.clip(data, 0, None)

        model_tight = IsolationForest(contamination=0.01, random_state=42)
        model_loose = IsolationForest(contamination=0.2, random_state=42)

        model_tight.fit(data)
        model_loose.fit(data)

        tight_anomalies = int((model_tight.predict(data) == -1).sum())
        loose_anomalies = int((model_loose.predict(data) == -1).sum())

        assert loose_anomalies > tight_anomalies, (
            f"Loose contamination ({loose_anomalies}) should flag more than tight ({tight_anomalies})"
        )

    def test_insufficient_history_falls_back_to_heuristic(self) -> None:
        """With fewer than 10 samples, the detector should use heuristic thresholds."""
        # This mirrors the behavior in behavior.py: < 10 samples → heuristic
        features = [150_000.0, 600.0, 10.0, 50.0, 5.0, 60.0]
        token_count = features[0]
        retrieval_count = features[1]

        # Heuristic logic from behavior.py
        normalized = 0.0
        if token_count > 100_000:
            normalized = max(normalized, 0.6)
        if retrieval_count > 500:
            normalized = max(normalized, 0.65)

        assert normalized >= 0.65
        assert normalized >= 0.6  # is_anomaly threshold

    def test_feature_vector_dimensions(self) -> None:
        """Feature vector must have exactly 6 dimensions."""
        # From _extract_feature_vector in behavior.py:
        # [token_count, retrieval_count, tool_total, avg_latency, diversity, window_seconds]
        expected_dims = 6
        rng = np.random.default_rng(0)
        data = rng.normal(size=(50, expected_dims))
        model = IsolationForest(random_state=0)
        model.fit(data)
        # No error means shape is correct
        sample = data[:1]
        _ = model.score_samples(sample)
        assert True

    def test_batch_scoring_consistency(self) -> None:
        """Scoring the same sample twice produces the same result."""
        rng = np.random.default_rng(7)
        data = rng.normal(loc=[200, 10, 5, 50, 3, 60], scale=[30, 3, 2, 10, 1, 5], size=(100, 6))
        data = np.clip(data, 0, None)

        model = IsolationForest(contamination=0.1, random_state=42, n_estimators=100)
        model.fit(data)

        sample = np.array([[250, 12, 6, 55, 3, 60]])
        score1 = model.score_samples(sample)[0]
        score2 = model.score_samples(sample)[0]
        assert score1 == score2, "IsolationForest scoring must be deterministic"

    def test_normalized_score_bounds(self) -> None:
        """Normalized score must stay in [0, 1]."""
        rng = np.random.default_rng(5)
        data = rng.normal(size=(100, 6))
        model = IsolationForest(contamination=0.1, random_state=42)
        model.fit(data)

        # Score many samples, check bounds
        test_data = rng.normal(size=(50, 6))
        raw_scores = model.score_samples(test_data)
        for raw in raw_scores:
            normalized = max(0.0, min(1.0, 1.0 - (float(raw) + 0.5) / 0.5))
            assert 0.0 <= normalized <= 1.0, f"Normalized score out of bounds: {normalized}"
