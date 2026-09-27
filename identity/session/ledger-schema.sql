-- Agent session ledger schema for PostgreSQL
-- Tracks all agent session lifecycle events for audit and forensics

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgvector;

-- Agent sessions
CREATE TABLE IF NOT EXISTS agent_sessions (
    session_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    principal_id    VARCHAR(256) NOT NULL,
    agent_class     VARCHAR(128) NOT NULL,
    tier            VARCHAR(4)   NOT NULL CHECK (tier IN ('T1', 'T2')),
    started_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    ended_at        TIMESTAMPTZ,
    status          VARCHAR(32)  NOT NULL DEFAULT 'active'
                      CHECK (status IN ('active', 'completed', 'isolated', 'revoked', 'expired')),
    isolation_reason TEXT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_sessions_principal ON agent_sessions (principal_id);
CREATE INDEX idx_agent_sessions_started   ON agent_sessions (started_at DESC);

-- Behavior signal events
CREATE TABLE IF NOT EXISTS behavior_signals (
    signal_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      UUID NOT NULL REFERENCES agent_sessions (session_id) ON DELETE CASCADE,
    principal_id    VARCHAR(256) NOT NULL,
    token_count     INTEGER NOT NULL CHECK (token_count >= 0),
    retrieval_count INTEGER NOT NULL CHECK (retrieval_count >= 0),
    tool_call_count INTEGER NOT NULL DEFAULT 0,
    window_seconds  INTEGER NOT NULL DEFAULT 60,
    anomaly_score   FLOAT,
    is_anomaly      BOOLEAN DEFAULT FALSE,
    mitre_tactic    VARCHAR(64),
    mitre_technique VARCHAR(16),
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_behavior_signals_session    ON behavior_signals (session_id);
CREATE INDEX idx_behavior_signals_principal  ON behavior_signals (principal_id, recorded_at DESC);
CREATE INDEX idx_behavior_signals_anomaly    ON behavior_signals (is_anomaly, recorded_at DESC)
    WHERE is_anomaly = TRUE;

-- Approval records for T2 actions
CREATE TABLE IF NOT EXISTS approval_records (
    approval_id     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      UUID REFERENCES agent_sessions (session_id),
    principal_id    VARCHAR(256) NOT NULL,
    action          VARCHAR(32)  NOT NULL,
    requestor_id    VARCHAR(256) NOT NULL,
    approver_id     VARCHAR(256),
    status          VARCHAR(32)  NOT NULL DEFAULT 'pending'
                      CHECK (status IN ('pending', 'approved', 'rejected', 'expired')),
    reason          TEXT,
    justification   TEXT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    decided_at      TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW() + INTERVAL '15 minutes'
);

CREATE INDEX idx_approval_records_principal ON approval_records (principal_id);
CREATE INDEX idx_approval_records_status    ON approval_records (status, expires_at);

-- Threat signals
CREATE TABLE IF NOT EXISTS threat_signals (
    signal_id       UUID PRIMARY KEY,
    source          VARCHAR(64)  NOT NULL,
    severity        VARCHAR(16)  NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    title           VARCHAR(512) NOT NULL,
    description     TEXT         NOT NULL,
    iocs            JSONB        NOT NULL DEFAULT '[]',
    mitre_techniques JSONB       NOT NULL DEFAULT '[]',
    received_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ
);

CREATE INDEX idx_threat_signals_severity   ON threat_signals (severity, received_at DESC);
CREATE INDEX idx_threat_signals_received   ON threat_signals (received_at DESC);
