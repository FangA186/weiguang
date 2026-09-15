-- A free trial is granted once per account, never renewed after expiry.
ALTER TABLE user_subscriptions
    ADD COLUMN IF NOT EXISTS free_trial_started_at TIMESTAMPTZ;

-- Every existing account has already had access to the former renewable free plan.
UPDATE user_subscriptions
SET free_trial_started_at = created_at
WHERE free_trial_started_at IS NULL;

ALTER TABLE user_subscriptions
    ALTER COLUMN free_trial_started_at SET DEFAULT NOW(),
    ALTER COLUMN free_trial_started_at SET NOT NULL;
