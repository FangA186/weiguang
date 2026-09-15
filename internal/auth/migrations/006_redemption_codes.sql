CREATE TABLE IF NOT EXISTS redemption_batches (
    id BIGSERIAL PRIMARY KEY,
    batch_code TEXT NOT NULL UNIQUE,
    channel TEXT NOT NULL DEFAULT 'ldxp',
    product_code TEXT NOT NULL CHECK (product_code IN ('plus_30d', 'pro_30d')),
    created_by TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'frozen', 'closed')),
    expires_at TIMESTAMPTZ NOT NULL,
    uploaded_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS redemption_codes (
    id BIGSERIAL PRIMARY KEY,
    batch_id BIGINT NOT NULL REFERENCES redemption_batches(id),
    code_hash CHAR(64) NOT NULL UNIQUE,
    product_code TEXT NOT NULL CHECK (product_code IN ('plus_30d', 'pro_30d')),
    status TEXT NOT NULL DEFAULT 'issued' CHECK (status IN ('issued', 'redeemed', 'revoked')),
    expires_at TIMESTAMPTZ NOT NULL,
    redeemed_by_user_id TEXT,
    redeemed_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_redemption_codes_batch_status
    ON redemption_codes (batch_id, status);

CREATE INDEX IF NOT EXISTS idx_redemption_codes_redeemed_user
    ON redemption_codes (redeemed_by_user_id, redeemed_at DESC)
    WHERE redeemed_by_user_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS subscription_grants (
    id BIGSERIAL PRIMARY KEY,
    redemption_code_id BIGINT NOT NULL UNIQUE REFERENCES redemption_codes(id),
    user_id TEXT NOT NULL,
    plan_code TEXT NOT NULL CHECK (plan_code IN ('plus', 'pro')),
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    source_channel TEXT NOT NULL DEFAULT 'ldxp',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (period_end > period_start)
);

CREATE INDEX IF NOT EXISTS idx_subscription_grants_user_created
    ON subscription_grants (user_id, created_at DESC);
