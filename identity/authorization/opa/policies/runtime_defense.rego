package agent.runtime.defense

import future.keywords.if
import future.keywords.in

# ---------------------------------------------------------------------------
# Default deny
# ---------------------------------------------------------------------------

default allow := false

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Anomaly score threshold required to permit isolation
isolation_score_threshold := 0.7

# Scopes that qualify as T2 (isolation/revocation)
t2_scopes := {"T2", "admin"}

# Actions that require T2 scope and approval
t2_actions := {"isolate", "revoke"}

# ---------------------------------------------------------------------------
# Allow T1 read-only actions (behavior scoring, threat signal ingestion)
# ---------------------------------------------------------------------------

allow if {
    input.action in {"score", "get_baseline", "ingest_signal"}
    _has_valid_token
    _caller_has_scope("T1")
}

# ---------------------------------------------------------------------------
# Allow T2 isolation / revocation
# All three conditions must hold:
#   1. Caller has a T2+ token
#   2. The anomaly score exceeds the threshold
#   3. A valid approval record exists for this request
# ---------------------------------------------------------------------------

allow if {
    input.action in t2_actions
    _has_valid_token
    _caller_has_t2_scope
    _anomaly_score_exceeds_threshold
    _approval_exists
}

# ---------------------------------------------------------------------------
# Allow T2 alert (T1 scope sufficient, no approval needed)
# ---------------------------------------------------------------------------

allow if {
    input.action == "alert"
    _has_valid_token
    _caller_has_scope("T1")
}

# ---------------------------------------------------------------------------
# Allow T2 monitor and throttle with T1 scope
# ---------------------------------------------------------------------------

allow if {
    input.action in {"monitor", "throttle"}
    _has_valid_token
    _caller_has_scope("T1")
}

# ---------------------------------------------------------------------------
# Helper rules
# ---------------------------------------------------------------------------

_has_valid_token if {
    input.token.valid == true
    not input.token.expired
}

_caller_has_scope(scope) if {
    scope in input.token.scopes
}

_caller_has_t2_scope if {
    some scope in input.token.scopes
    scope in t2_scopes
}

_anomaly_score_exceeds_threshold if {
    input.anomaly_score >= isolation_score_threshold
}

_approval_exists if {
    input.approval.exists == true
    input.approval.principal_id == input.principal_id
    input.approval.action == input.action
    not input.approval.expired
}

# ---------------------------------------------------------------------------
# Deny reasons (for audit logging)
# ---------------------------------------------------------------------------

deny_reason := reason if {
    not allow
    input.action in t2_actions
    _has_valid_token
    not _caller_has_t2_scope
    reason := "caller_lacks_t2_scope"
}

deny_reason := reason if {
    not allow
    input.action in t2_actions
    _has_valid_token
    _caller_has_t2_scope
    not _anomaly_score_exceeds_threshold
    reason := sprintf(
        "anomaly_score_below_threshold: %.3f < %.3f",
        [input.anomaly_score, isolation_score_threshold],
    )
}

deny_reason := reason if {
    not allow
    input.action in t2_actions
    _has_valid_token
    _caller_has_t2_scope
    _anomaly_score_exceeds_threshold
    not _approval_exists
    reason := "missing_or_invalid_approval"
}

deny_reason := reason if {
    not allow
    not _has_valid_token
    reason := "invalid_or_expired_token"
}
