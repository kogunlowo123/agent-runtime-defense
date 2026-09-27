# Runbook: Agent Isolation Procedure

**Version:** 0.1.0
**Owner:** Platform Security Team

---

## Overview

This runbook covers the complete agent isolation lifecycle:
1. Pre-isolation checks
2. Isolation execution (T2 approval gate)
3. Isolation verification
4. Post-isolation monitoring
5. Safe re-enablement

---

## Pre-Isolation Checks

Before isolating, confirm:

- [ ] Anomaly score > 0.7 (or manual security decision)
- [ ] Principal ID is correct (check session ledger)
- [ ] Isolation will not break critical business process
- [ ] T2 approval has been obtained

```bash
# Verify principal exists and get current session
curl -H "Authorization: Bearer <jwt>" \
  https://your-api/api/v1/behavior/<principal-id>
```

---

## Isolation Execution

```bash
# Step 1: Get T2 approval
APPROVAL=$(curl -s -X POST https://approval-service/approvals \
  -H "Authorization: Bearer <security-jwt>" \
  -d "{ \"principal_id\": \"<id>\", \"action\": \"isolate\", \"reason\": \"...\", \"requestor_id\": \"<you>\" }" \
  | jq -r '.approval_token')

# Step 2: Execute isolation
curl -X POST https://your-api/api/v1/response/isolate \
  -H "Authorization: Bearer <your-jwt>" \
  -H "Content-Type: application/json" \
  -d "{
    \"principal_id\": \"<id>\",
    \"action\": \"isolate\",
    \"reason\": \"Security incident: <description>\",
    \"requestor_id\": \"<your-id>\",
    \"approval_token\": \"$APPROVAL\",
    \"ttl_seconds\": 7200
  }"
```

---

## Isolation Verification

Verify the isolation took effect:

```bash
# Should return status: isolated
curl -H "Authorization: Bearer <jwt>" \
  https://your-api/api/v1/behavior/<principal-id>

# Check audit trail in Azure Monitor
# Azure Log Analytics query:
# customEvents
# | where name == "isolation_executed"
# | where customDimensions.principal_id == "<id>"
# | order by timestamp desc | take 1
```

---

## Safe Re-Enablement

1. Root cause confirmed resolved
2. Agent JWT rotated
3. New behavioral baseline established (submit 10+ normal signals)
4. Security sign-off obtained

```bash
# Lift isolation
curl -X POST https://your-api/api/v1/response/isolate \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -d "{
    \"principal_id\": \"<id>\",
    \"action\": \"monitor\",
    \"reason\": \"Root cause resolved; returning to monitored state\",
    \"requestor_id\": \"<your-id>\"
  }"
```
