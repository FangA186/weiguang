CREATE TABLE IF NOT EXISTS user_quota_adjustments (
    user_id TEXT NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    metric TEXT NOT NULL,
    extra_limit DOUBLE PRECISION NOT NULL DEFAULT 0,
    reason TEXT NOT NULL DEFAULT '',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, metric)
);
