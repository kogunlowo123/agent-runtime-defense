# ADR-0002: Heuristic MITRE ATT&CK Mapping Strategy

**Status:** Accepted
**Date:** 2024-01-15
**Deciders:** Platform Security Team

## Context

Detected behavioral anomalies must be mapped to MITRE ATT&CK tactics and techniques to enable:
- Correlation with SIEM (Azure Sentinel) detection rules
- Structured threat reporting
- Response playbook selection

We must choose between heuristic rules, ML-based classification, and RAG-grounded inference.

## Decision

**Phase 1 (current):** Heuristic rules based on feature thresholds.

```
retrieval_count > 1000  → Collection  / T1213
token_count > 500,000   → Exfiltration / T1041
tool_count > 100        → Execution   / T1059
score > 0.8 (generic)   → Discovery  / T1087
otherwise               → Unknown    / T0000
```

**Phase 2 (v0.2):** RAG-grounded mapping: embed the signal profile and retrieve the nearest MITRE technique from a pgvector-indexed knowledge base.

## Rationale

Heuristic rules are chosen for v0.1 because:
1. Zero latency overhead — no LLM call on the hot scoring path
2. Deterministic and auditable — easy to explain to security teams
3. Covers the most impactful attack patterns immediately

The RAG-grounded approach (Phase 2) will improve accuracy for novel attack patterns that don't fit simple threshold rules.

## Consequences

**Positive:**
- Zero-latency MITRE mapping
- Fully deterministic and testable

**Negative:**
- Limited coverage — only 4 techniques mapped in v0.1
- No nuance for mixed-signal attacks

**Monitoring:** Track `mitre_technique=T0000` rate; if >30% of anomalies map to Unknown, accelerate Phase 2.
