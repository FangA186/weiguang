ALTER TABLE chat_import_batches
    ADD COLUMN IF NOT EXISTS left_avatar_object_key TEXT,
    ADD COLUMN IF NOT EXISTS right_avatar_object_key TEXT;

ALTER TABLE chat_messages
    ADD COLUMN IF NOT EXISTS import_meta JSONB NOT NULL DEFAULT '{}'::jsonb;
