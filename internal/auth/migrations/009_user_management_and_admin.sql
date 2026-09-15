-- User management and administrative status migration.
-- Repeatable migration applied at startup.

ALTER TABLE app_users
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'disabled')),
    ADD COLUMN IF NOT EXISTS disabled_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS admin_note TEXT NOT NULL DEFAULT '';

CREATE INDEX IF NOT EXISTS idx_app_users_status
    ON app_users (status);

CREATE INDEX IF NOT EXISTS idx_app_users_created_at
    ON app_users (created_at DESC);
