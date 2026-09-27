# ADR-0001: IsolationForest for Behavioral Anomaly Detection Baseline

**Status:** Accepted
**Date:** 2024-01-15
**Deciders:** Platform Security Team

## Context

We need an unsupervised anomaly detection algorithm for agent behavioral baselines. The system must:
- Work without labeled training data (no prior attack examples)
- Scale to per-principal baselines with low memory
- Support incremental updates as new behavior is observed
- Be interpretable (explainable feature weights)

## Decision

Use `scikit-learn` `IsolationForest` as the primary anomaly detection model, with a configurable contamination parameter (default: 10%).

Feature vector dimensions: `[token_count, retrieval_count, tool_call_count, avg_tool_latency_ms, tool_diversity, window_seconds]`

## Rationale

| Criterion | IsolationForest | LOF | One-Class SVM | Autoencoder |
|-----------|----------------|-----|---------------|-------------|
| Unsupervised | Yes | Yes | Yes | Yes |
| Low memory | Yes (trees) | No (all data) | Moderate | High |
| Fast inference | Yes (O(log n)) | No (O(n)) | Moderate | Fast |
| Interpretable | Partial | Low | Low | Low |
| Sklearn native | Yes | Yes | Yes | No |

IsolationForest's isolation mechanism is particularly well-suited for detecting the extreme-valued anomalies typical of attack patterns (mass retrieval, token burn), where anomalous samples are isolated with fewer random splits.

## Consequences

**Positive:**
- Low memory: O(n_estimators × max_samples) per principal
- Fast inference: sub-millisecond per signal
- No labeled data required

**Negative:**
- Susceptible to model evasion by adversaries who learn the normal distribution
- Contamination parameter requires tuning per deployment

**Planned Evolution (v0.2):**
- Ensemble: IsolationForest + LOF for reduced false positives
- Online learning: incremental updates without full refit
- Per-agent-class contamination tuning via configuration
