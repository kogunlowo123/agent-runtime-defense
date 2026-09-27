#!/usr/bin/env bash
# Break-glass emergency procedure: bypass normal approval flow for critical incident
# IMPORTANT: Use only for P0 incidents. All actions are logged.
set -euo pipefail

PRINCIPAL_ID="${1:-}"
REASON="${2:-Emergency break-glass isolation}"
REQUESTOR="${3:-break-glass-operator}"

if [[ -z "$PRINCIPAL_ID" ]]; then
    echo "Usage: $0 <principal-id> [reason] [requestor-id]"
    echo "Example: $0 agent-abc-123 'Active data exfiltration detected' 'incident-commander'"
    exit 1
fi

echo "==================================================================="
echo "BREAK GLASS PROCEDURE"
echo "Principal: $PRINCIPAL_ID"
echo "Reason:    $REASON"
echo "Requestor: $REQUESTOR"
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "==================================================================="
echo ""
echo "WARNING: This procedure bypasses the normal T2 approval gate."
echo "All actions will be logged to Azure Monitor and Sentinel."
echo ""
read -r -p "Type 'CONFIRM' to proceed: " confirmation

if [[ "$confirmation" != "CONFIRM" ]]; then
    echo "Aborted."
    exit 0
fi

API_URL="${ARD_API_URL:-http://localhost:8000}"
API_TOKEN="${ARD_BREAK_GLASS_TOKEN:-}"

if [[ -z "$API_TOKEN" ]]; then
    echo "ERROR: ARD_BREAK_GLASS_TOKEN environment variable not set"
    exit 1
fi

echo "Executing isolation..."
curl -sf -X POST "$API_URL/api/v1/response/isolate" \
    -H "Authorization: Bearer $API_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"principal_id\": \"$PRINCIPAL_ID\",
        \"action\": \"isolate\",
        \"reason\": \"BREAK GLASS: $REASON\",
        \"requestor_id\": \"$REQUESTOR\",
        \"ttl_seconds\": 7200
    }"

echo ""
echo "Isolation request submitted. Verify status in Azure Monitor."
echo "Incident must be documented within 30 minutes per security policy."
