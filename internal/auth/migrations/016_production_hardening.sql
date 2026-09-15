-- Shared request limiting. Core account tables already use ON DELETE CASCADE;
-- legacy usage/voice ledgers intentionally keep their historical free-form
-- user ids because offline billing tests and recovery jobs can predate a row
-- in app_users. Account deletion explicitly clears those ledgers.

CREATE TABLE IF NOT EXISTS rate_limit_events (
    key_hash CHAR(64) PRIMARY KEY,
    window_started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rate_limit_events_updated_at
    ON rate_limit_events (updated_at);
