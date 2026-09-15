ALTER TABLE user_subscriptions
    ALTER COLUMN period_end SET DEFAULT (NOW() + INTERVAL '7 days');

UPDATE user_subscriptions AS subscription
SET period_end = LEAST(subscription.period_end, subscription.free_trial_started_at + INTERVAL '7 days'),
    access_end = CASE
        WHEN EXISTS (
            SELECT 1 FROM subscription_grants AS entitlement
            WHERE entitlement.user_id = subscription.user_id
              AND entitlement.period_end > subscription.free_trial_started_at + INTERVAL '7 days'
        ) THEN subscription.access_end
        ELSE LEAST(subscription.access_end, subscription.free_trial_started_at + INTERVAL '7 days')
    END,
    status = CASE
        WHEN NOW() >= subscription.free_trial_started_at + INTERVAL '7 days' THEN 'expired'
        ELSE subscription.status
    END,
    updated_at = NOW()
WHERE subscription.plan_code = 'free'
  AND subscription.free_trial_started_at IS NOT NULL
  AND subscription.period_end > subscription.free_trial_started_at + INTERVAL '7 days'
  AND NOT EXISTS (
      SELECT 1 FROM subscription_grants AS active_grant
      WHERE active_grant.user_id = subscription.user_id
        AND active_grant.period_start <= NOW()
        AND active_grant.period_end > NOW()
  );
