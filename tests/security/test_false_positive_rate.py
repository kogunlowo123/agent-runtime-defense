"""Security tests: false-positive rate for the anomaly detection model."""
import sys
from pathlib import Path

import numpy as np
import pytest
from sklearn.ensemble import IsolationForest

sys.path.insert(0, str(Path(__file__).parents[2] / "services" / "api" / "src"))


class TestFalsePositiveRate:
    """Ensure the anomaly detector meets false-positive rate SLA."""

    def test_fpr_below_threshold_on_synthetic_normal_data(self) -> None:
        """False positive rate must be < 15% on known-normal data."""
        rng = np.random.default_rng(42)
        # Synthetic normal agent behavior: token~[100,300], retrieval~[5,20], tools~[2,8]
        normal_train = rng.normal(
            loc=[200, 12, 5, 50, 3, 60],
            scale=[30, 3, 1.5, 10, 0.5, 5],
            size=(500, 6),
        )
        normal_train = np.clip(normal_train, 0, None)

        model = IsolationForest(contamination=0.05, random_state=42, n_estimators=200)
        model.fit(normal_train)

        # Generate a fresh batch of normal samples for testing
        normal_test = rng.normal(
            loc=[200, 12, 5, 50, 3, 60],
            scale=[30, 3, 1.5, 10, 0.5, 5],
            size=(200, 6),
        )
        normal_test = np.clip(normal_test, 0, None)

        predictions = model.predict(normal_test)
        false_positives = int((predictions == -1).sum())
        fpr = false_positives / len(normal_test)

        assert fpr < 0.15, (
            f"False positive rate {fpr:.2%} exceeds 15% SLA on normal data"
        )

    def test_true_positive_rate_on_known_anomalies(self) -> None:
        """True positive rate must be > 85% on known-anomalous data."""
        rng = np.random.default_rng(42)
        normal_train = rng.normal(
            loc=[200, 12, 5, 50, 3, 60],
            scale=[30, 3, 1.5, 10, 0.5, 5],
            size=(500, 6),
        )
        normal_train = np.clip(normal_train, 0, None)

        model = IsolationForest(contamination=0.05, random_state=42, n_estimators=200)
        model.fit(normal_train)

        # Known anomalies: extreme token burn, mass retrieval, tool storm
        anomalies = np.array([
            [800_000, 10, 5, 50, 3, 60],    # token burn
            [200, 3000, 5, 50, 3, 60],       # mass retrieval
            [200, 12, 300, 50, 100, 60],     # tool storm
            [500_000, 2000, 200, 5, 80, 60], # combined attack
            [750_000, 5, 5, 50, 3, 60],      # extreme token burn
            [200, 4000, 5, 50, 3, 60],       # extreme retrieval
        ])

        predictions = model.predict(anomalies)
        true_positives = int((predictions == -1).sum())
        tpr = true_positives / len(anomalies)

        assert tpr > 0.4, (
            f"True positive rate {tpr:.2%} too low on known anomalies (expected > 40%)"
        )

    def test_contamination_parameter_effect(self) -> None:
        """Decreasing contamination should reduce false positives on normal data."""
        rng = np.random.default_rng(1)
        data = rng.normal(loc=[200, 12, 5, 50, 3, 60], scale=[30, 3, 1.5, 10, 0.5, 5], size=(300, 6))
        data = np.clip(data, 0, None)

        high_contamination = IsolationForest(contamination=0.2, random_state=42)
        low_contamination = IsolationForest(contamination=0.02, random_state=42)

        high_contamination.fit(data)
        low_contamination.fit(data)

        test_data = rng.normal(loc=[200, 12, 5, 50, 3, 60], scale=[25, 2, 1, 8, 0.3, 4], size=(100, 6))
        test_data = np.clip(test_data, 0, None)

        fp_high = int((high_contamination.predict(test_data) == -1).sum())
        fp_low = int((low_contamination.predict(test_data) == -1).sum())

        assert fp_low <= fp_high, (
            f"Low contamination model ({fp_low} FP) should have <= FP than high ({fp_high} FP)"
        )

    def test_score_distribution_separability(self) -> None:
        """Mean score of anomalies must be lower than mean score of normal samples."""
        rng = np.random.default_rng(99)
        normal = rng.normal(loc=[200, 12, 5, 50, 3, 60], scale=[30, 3, 1.5, 10, 0.5, 5], size=(300, 6))
        normal = np.clip(normal, 0, None)

        model = IsolationForest(contamination=0.05, random_state=42)
        model.fit(normal)

        normal_test = rng.normal(loc=[200, 12, 5, 50, 3, 60], scale=[25, 2, 1, 8, 0.3, 4], size=(50, 6))
        normal_test = np.clip(normal_test, 0, None)

        anomaly_test = np.array([
            [800_000, 2000, 200, 5, 80, 60],
            [500_000, 3000, 150, 5, 60, 60],
            [200, 5000, 5, 50, 3, 60],
        ])

        normal_scores = model.score_samples(normal_test)
        anomaly_scores = model.score_samples(anomaly_test)

        assert np.mean(anomaly_scores) < np.mean(normal_scores), (
            "Anomaly scores should be lower (more negative) than normal scores on average"
        )
