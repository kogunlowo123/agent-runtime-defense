# STRIDE Threat Model: Agent Runtime Defense

**Version:** 0.1.0
**Date:** 2024-01-15
**Author:** Security Team
**Scope:** API gateway, behavior scoring pipeline, LangGraph agent orchestration, T2 approval gate

---

## System Architecture

```
[External Agent] → [API Gateway] → [Behavior Score API] → [IsolationForest] → [Alert]
                                                                        ↓ (score > 0.8)
[Threat Signal]  → [Threat API]  → [LangGraph Orchestrator] → [T2 Approval Gate] → [Isolation]
                                         ↓
                                   [RAG / MITRE ATT&CK]
```

---

## Threat Analysis

### Spoofing

| ID | Threat | Mitigation |
|----|--------|-----------|
| S1 | Attacker forges a JWT token with T2 scope | RS256 signature + short TTL (1h) + JWKS rotation |
| S2 | Adversarial agent impersonates another principal | principal_id validated against JWT sub claim |
| S3 | Threat actor spoofs a CISA threat signal source | Source field validated; manual signals require T1 auth |

### Tampering

| ID | Threat | Mitigation |
|----|--------|-----------|
| T1 | Attacker manipulates behavior signal to suppress anomaly score | Input validation; IsolationForest is outlier-resistant |
| T2 | Adversary injects prompt into RAG retrieval to manipulate MITRE mapping | Input screener; grounding check on all RAG outputs |
| T3 | Terraform state file tampered to weaken Key Vault ACLs | Remote state with integrity hashing; Sentinel alert on KV policy changes |

### Repudiation

| ID | Threat | Mitigation |
|----|--------|-----------|
| R1 | Agent denies performing actions | Immutable audit log via Azure Monitor + OpenTelemetry traces |
| R2 | Approver denies granting T2 approval | Approval tokens include approver identity; stored in audit ledger |

### Information Disclosure

| ID | Threat | Mitigation |
|----|--------|-----------|
| I1 | Behavior baselines leak agent architecture details | Baselines scoped to principal; require T1 auth to read |
| I2 | RAG context leaks sensitive content | PII tagger on ingestion; ACL filter on retrieval |
| I3 | LangGraph state serialized to logs | State sanitization before logging; PII scrub processor in OTel |

### Denial of Service

| ID | Threat | Mitigation |
|----|--------|-----------|
| D1 | Flooding behavior/score endpoint to exhaust memory | Rate limit 100/min per IP; in-memory baseline capped at 500 entries |
| D2 | Large payload in BehaviorSignal (tool_calls list) | Pydantic validation; token_count ceiling 10M |

### Elevation of Privilege

| ID | Threat | Mitigation |
|----|--------|-----------|
| E1 | T1 caller bypasses T2 approval gate | OPA policy enforces: T2 scope + anomaly_score > 0.7 + approval exists |
| E2 | Container escape from AKS pod | Non-root containers; Kyverno policies; Azure Defender for Containers |
| E3 | Key Vault RBAC misconfiguration grants excess access | RBAC-only mode; role assignments managed by Terraform; alert on unusual reads |

---

## Residual Risks

1. **Model evasion**: A sophisticated attacker could craft behavior signals that evade IsolationForest by staying within the training distribution. Mitigation: ensemble model (LOF + IsolationForest) planned for v0.2.
2. **Approval token replay**: A stolen approval token can be replayed within its TTL window. Mitigation: approval tokens are single-use (tracked in ledger).
