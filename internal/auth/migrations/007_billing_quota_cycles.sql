-- Keep the current quota cycle separate from queued subscription access grants.
-- This migration is intentionally repeatable because the Python stores apply
-- the project's SQL files at startup.

ALTER TABLE usage_events
    ADD COLUMN IF NOT EXISTS reserved_until TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS released_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS expired_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS period_start TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS plan_code TEXT;

ALTER TABLE user_subscriptions
    ADD COLUMN IF NOT EXISTS access_end TIMESTAMPTZ;

UPDATE user_subscriptions
SET access_end = period_end
WHERE access_end IS NULL;

-- Existing data used ``user_subscriptions.period_end`` as both the active
-- cycle boundary and the paid-access horizon.  Grants are the durable source
-- for queued access, so recover the horizon before correcting active cycles.
WITH access_horizons AS (
    SELECT
        subscriptions.user_id,
        GREATEST(
            subscriptions.period_end,
            COALESCE(MAX(grants.period_end), subscriptions.period_end)
        ) AS access_end
    FROM user_subscriptions AS subscriptions
    LEFT JOIN subscription_grants AS grants
        ON grants.user_id = subscriptions.user_id
    GROUP BY subscriptions.user_id, subscriptions.period_end
)
UPDATE user_subscriptions AS subscriptions
SET access_end = access_horizons.access_end
FROM access_horizons
WHERE subscriptions.user_id = access_horizons.user_id
  AND subscriptions.access_end IS DISTINCT FROM access_horizons.access_end;

-- If an old same-tier renewal had extended one quota period beyond 30 days,
-- select the grant active now as the authoritative current quota cycle.
WITH active_grants AS (
    SELECT DISTINCT ON (user_id)
        user_id,
        plan_code,
        period_start,
        period_end
    FROM subscription_grants
    WHERE period_start <= NOW()
      AND period_end > NOW()
    ORDER BY user_id, period_start DESC
)
UPDATE user_subscriptions AS subscriptions
SET
    plan_code = active_grants.plan_code,
    status = 'active',
    period_start = active_grants.period_start,
    period_end = active_grants.period_end,
    updated_at = NOW()
FROM active_grants
WHERE subscriptions.user_id = active_grants.user_id
  AND (
      subscriptions.plan_code IS DISTINCT FROM active_grants.plan_code
      OR subscriptions.period_start IS DISTINCT FROM active_grants.period_start
      OR subscriptions.period_end IS DISTINCT FROM active_grants.period_end
  );

-- Legacy completed events retain their historical occurred_at value.  Events
-- in the recovered current cycle gain an explicit boundary for new summaries.
UPDATE usage_events AS events
SET period_start = subscriptions.period_start,
    plan_code = subscriptions.plan_code,
    completed_at = COALESCE(events.completed_at, events.occurred_at)
FROM user_subscriptions AS subscriptions
WHERE events.user_id = subscriptions.user_id
  AND events.period_start IS NULL
  AND events.occurred_at >= subscriptions.period_start
  AND events.occurred_at < subscriptions.period_end;

UPDATE usage_events
SET completed_at = COALESCE(completed_at, occurred_at)
WHERE status = 'completed';

CREATE INDEX IF NOT EXISTS idx_usage_events_user_cycle_metric_status
    ON usage_events (user_id, period_start, metric, status);

CREATE INDEX IF NOT EXISTS idx_usage_events_active_reservations
    ON usage_events (user_id, period_start, metric, reserved_until)
    WHERE status = 'reserved';

CREATE INDEX IF NOT EXISTS idx_subscription_grants_user_period
    ON subscription_grants (user_id, period_start, period_end);
