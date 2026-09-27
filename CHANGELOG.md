# Changelog

All notable changes to Agent Runtime Defense will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2024-01-15

### Added

- Initial platform implementation for agent runtime behavioral defense
- FastAPI service with behavior scoring, threat signal ingestion, and isolation endpoints
- IsolationForest-based anomaly detection with configurable contamination threshold
- MITRE ATT&CK heuristic mapping for detected behavioral anomalies
- LangGraph agent graph for anomaly-detector (T1) with escalation to T2
- Behavioral baseline establishment and retrieval per principal
- T2 threat-responder with approval gate enforcement
- OPA policy for isolation authorization (T2+ token + anomaly score + approval)
- Azure infrastructure: AKS, PostgreSQL Flex + pgvector, Azure AI Search, Service Bus, Key Vault, Sentinel
- Helm charts for API and agent-runtime services
- ArgoCD app-of-apps configuration for GitOps deployment
- OpenTelemetry tracing with OTLP export
- SIGMA detection rules: token-burn-anomaly, scope-violation, mass-retrieval
- KQL detections for Azure Sentinel: Entra agent anomaly, Key Vault unusual reads
- Identity registry with JWT issuance and TTL policies
- RAG core pipeline: BGE local embeddings, pgvector store, hybrid retrieval with RRF
- CloudEvents emission for anomaly.detected, response.executed, threat.signal.received
- GitHub Actions CI: lint, type-check, unit tests, integration tests, security scans
- Terraform modules for all Azure resources with dev/staging/prod environments
- ADRs: IsolationForest baseline selection, MITRE ATT&CK mapping strategy
- Runbooks: anomaly response, agent isolation procedures

[Unreleased]: https://github.com/kogunlowo123/agent-runtime-defense/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/kogunlowo123/agent-runtime-defense/releases/tag/v0.1.0
