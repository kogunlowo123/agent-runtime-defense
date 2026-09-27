# Agent Runtime Defense

[![CI](https://github.com/kogunlowo123/agent-runtime-defense/actions/workflows/ci.yml/badge.svg)](https://github.com/kogunlowo123/agent-runtime-defense/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-brightgreen.svg)](https://python.org)
[![Azure](https://img.shields.io/badge/cloud-Azure-0078D4.svg)](https://azure.microsoft.com)

Enterprise AI security platform for **agent runtime defense** — real-time anomaly detection, behavioral analysis, and automated threat response for AI agents at runtime.

## Overview

Agent Runtime Defense monitors AI agent behavior in real time, detects deviations from established baselines, maps threats to MITRE ATT&CK, and executes automated T1/T2 responses (alert, isolate, revoke). It is deployed on Azure and exposes a REST API for signal ingestion and response orchestration.

```
┌─────────────────────────────────────────────────────────────────┐
│                     Agent Runtime Defense                       │
│                                                                 │
│  ┌──────────────┐   ┌──────────────────┐   ┌───────────────┐  │
│  │  Behavior    │   │  LangGraph       │   │  Threat       │  │
│  │  Signal API  │──▶│  Agent Graphs    │──▶│  Responder    │  │
│  └──────────────┘   │                  │   └───────────────┘  │
│                     │  anomaly-detector│                       │
│  ┌──────────────┐   │  behavior-analyst│   ┌───────────────┐  │
│  │  Threat      │   │  threat-responder│   │  MITRE RAG    │  │
│  │  Signal API  │──▶│                  │──▶│  (pgvector +  │  │
│  └──────────────┘   └──────────────────┘   │  AI Search)   │  │
│                                            └───────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Azure: OpenAI · AI Search · PostgreSQL Flex · Service   │ │
│  │         Bus · AKS · Key Vault · Sentinel · Monitor       │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Families

| Family | Tier | Capabilities |
|--------|------|-------------|
| `anomaly-detector` | T1 | Behavioral signal ingestion, IsolationForest scoring, MITRE mapping, RAG context |
| `behavior-analyst` | T1 | Deep behavior pattern analysis, baseline comparison, RAG-grounded reporting |
| `threat-responder` | T2 | Isolation, revocation, approval-gated response execution |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/behavior/score` | Score behavioral signals, return anomaly score + MITRE tactic |
| `POST` | `/api/v1/threat/signal` | Ingest external threat signal |
| `POST` | `/api/v1/response/isolate` | T2: isolate agent or session (requires approval token) |
| `GET` | `/api/v1/behavior/{principal}` | Retrieve behavioral baseline for principal |
| `GET` | `/api/v1/health` | Liveness check |
| `GET` | `/api/v1/readiness` | Readiness check with sub-system status |

## Quick Start

```bash
# Prerequisites: Python 3.12+, uv, Docker

# Clone
git clone https://github.com/kogunlowo123/agent-runtime-defense.git
cd agent-runtime-defense

# Copy and configure environment
cp .env.example .env
# Edit .env with your Azure credentials

# Install dependencies
uv sync --all-extras

# Start infrastructure (postgres, opensearch, redis)
docker compose up -d postgres opensearch redis

# Run API server
uv run uvicorn services.api.src.api.main:app --reload --port 8000
```

### Example: Score Behavioral Signals

```bash
curl -X POST http://localhost:8000/api/v1/behavior/score \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-jwt>" \
  -d '{
    "principal_id": "agent-abc-123",
    "agent_class": "anomaly-detector",
    "token_count": 150000,
    "retrieval_count": 750,
    "tool_calls": [
      {"tool_name": "rag_search", "invocation_count": 25, "avg_latency_ms": 120.5}
    ],
    "window_seconds": 60
  }'
```

Response:
```json
{
  "principal_id": "agent-abc-123",
  "session_id": "...",
  "score": -0.45,
  "normalized_score": 0.82,
  "is_anomaly": true,
  "mitre_tactic": "collection",
  "mitre_technique": "T1213",
  "risk_factors": ["excessive_token_consumption", "mass_retrieval"],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## MITRE ATT&CK Mapping

The platform maps detected agent behavioral anomalies to MITRE ATT&CK for Containers and Enterprise:

| Signal Pattern | Tactic | Technique |
|----------------|--------|-----------|
| High retrieval volume (>1000 ops/window) | Collection | T1213 |
| Excessive token consumption (>500K/window) | Exfiltration | T1041 |
| Mass tool invocations (>100/window) | Execution | T1059 |
| General anomaly (score >0.8) | Discovery | T1087 |

## Azure Deployment

```bash
# Initialize Terraform for your environment
cd infra/envs/azure/dev
terraform init
terraform plan
terraform apply

# Deploy to AKS via Helm
helm upgrade --install agent-runtime-defense deploy/helm/umbrella/ \
  --namespace agent-runtime-defense \
  --create-namespace \
  --values deploy/helm/umbrella/values.yaml
```

## Development

```bash
# Run tests
make test

# Lint and format
make lint
make format

# Type check
make type-check
```

## Security

See [SECURITY.md](SECURITY.md) for the vulnerability reporting policy.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache 2.0 — see [LICENSE](LICENSE).
