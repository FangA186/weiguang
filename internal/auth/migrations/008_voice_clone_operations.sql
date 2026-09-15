-- Durable cross-system voice-clone operation ledger.  It deliberately stores
-- identifiers and stable error codes only: no OSS URL, credential, or raw
-- provider error body belongs in this recovery table.

CREATE TABLE IF NOT EXISTS voice_clone_operations (
    id BIGSERIAL PRIMARY KEY,
    request_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    operation_type TEXT NOT NULL CHECK (operation_type IN ('create', 'delete')),
    voice_id TEXT,
    provider_prefix TEXT,
    status TEXT NOT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    error_code TEXT,
    claim_token TEXT,
    claim_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    provider_succeeded_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    CONSTRAINT uq_voice_clone_operation_request UNIQUE (user_id, request_id, operation_type)
);

-- Existing local databases may already have created this table from the first
-- version of 008. Keep the startup-applied migration safely repeatable.
ALTER TABLE voice_clone_operations
    ADD COLUMN IF NOT EXISTS provider_prefix TEXT;

CREATE INDEX IF NOT EXISTS idx_voice_clone_operations_reconcile
    ON voice_clone_operations (user_id, status, claim_expires_at, id);

CREATE INDEX IF NOT EXISTS idx_voice_clone_operations_voice
    ON voice_clone_operations (user_id, voice_id, operation_type, status);
