# Runbook: Anomaly Response

**Version:** 0.1.0
**Owner:** Platform Security Team
**SLA:** P1 (Critical) — 15 min response, P2 (High) — 1 hour response

---

## Trigger

This runbook is triggered when `POST /api/v1/behavior/score` returns `is_anomaly: true`
or when the anomaly-detector LangGraph graph emits a `response_action: isolate`.

---

## Step 1: Triage (5 minutes)

1. Check the anomaly score:
   - `normalized_score < 0.5`: Low — continue monitoring, no immediate action
   - `0.5 - 0.7`: Medium — review agent session logs
   - `0.7 - 0.9`: High — prepare isolation request
   - `> 0.9`: Critical — isolate immediately

2. Check `mitre_tactic` and `mitre_technique`:
   - `T1213` (Collection/Mass Retrieval): Likely data harvesting — isolate
   - `T1041` (Exfiltration/Token Burn): Potential data exfiltration — isolate
   - `T1059` (Execution): Tool storm — throttle or isolate
   - `T1087` (Discovery): Reconnaissance pattern — monitor + alert

3. Check `risk_factors` in the response for contextual signals.

---

## Step 2: Get a T2 Approval Token (for ISOLATE/REVOKE)

```bash
# Request approval (requires security team member with T2 role)
curl -X POST https://your-approval-service/approvals \
  -H "Authorization: Bearer <security-team-jwt>" \
  -d '{
    "principal_id": "<agent-to-isolate>",
    "action": "isolate",
    "reason": "Anomaly score 0.92 — T1213 collection pattern detected",
    "requestor_id": "<your-id>",
    "ttl_seconds": 900
  }'
# Returns: { "approval_token": "eyJ...", "expires_in": 900 }
```

---

## Step 3: Execute Isolation

```bash
curl -X POST https://your-api/api/v1/response/isolate \
  -H "Authorization: Bearer <your-jwt>" \
  -H "Content-Type: application/json" \
  -d '{
    "principal_id": "<agent-id>",
    "action": "isolate",
    "reason": "Critical anomaly: normalized_score=0.92, T1213 collection pattern",
    "requestor_id": "<your-id>",
    "approval_token": "<approval-token>",
    "ttl_seconds": 3600
  }'
```

Expected response: `{ "status": "completed", "action": "isolate", "expires_at": "..." }`

---

## Step 4: Post-Isolation Investigation

1. Pull session logs from Azure Monitor:
   ```kql
   // Find all behavior signals for isolated principal
   customEvents
   | where name == "behavior_signal"
   | where customDimensions.principal_id == "<agent-id>"
   | where timestamp >= ago(2h)
   | project timestamp, customDimensions.token_count, customDimensions.retrieval_count
   | order by timestamp desc
   ```

2. Check for lateral movement: Look for signals from other principals with similar patterns.

3. File a security incident if confirmed malicious.

---

## Step 5: Recovery

1. Investigate root cause: compromised credentials, prompt injection, misconfiguration
2. Rotate agent JWT
3. Update behavioral baseline if agent behavior legitimately changed
4. Lift isolation: `POST /api/v1/response/isolate` with `action: monitor` and new approval
