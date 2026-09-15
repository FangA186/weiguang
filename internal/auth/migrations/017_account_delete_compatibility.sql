-- Older development boots may have run the experimental 016 foreign keys.
-- Remove only those optional constraints so legacy ledgers remain compatible;
-- app_users-owned tables retain their original cascading foreign keys.
ALTER TABLE IF EXISTS voice_clones DROP CONSTRAINT IF EXISTS fk_voice_clones_user;
ALTER TABLE IF EXISTS chat_attachments DROP CONSTRAINT IF EXISTS fk_chat_attachments_user;
ALTER TABLE IF EXISTS chat_import_batches DROP CONSTRAINT IF EXISTS fk_chat_import_batches_user;
ALTER TABLE IF EXISTS usage_events DROP CONSTRAINT IF EXISTS fk_usage_events_user;
ALTER TABLE IF EXISTS subscription_grants DROP CONSTRAINT IF EXISTS fk_subscription_grants_user;
ALTER TABLE IF EXISTS voice_clone_operations DROP CONSTRAINT IF EXISTS fk_voice_clone_operations_user;
