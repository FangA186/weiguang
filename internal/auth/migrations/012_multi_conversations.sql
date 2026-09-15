DROP INDEX IF EXISTS uq_chat_conversations_active_user;

ALTER TABLE chat_conversations
    ADD COLUMN IF NOT EXISTS avatar_object_key TEXT;

CREATE INDEX IF NOT EXISTS idx_chat_conversations_user_updated
    ON chat_conversations (user_id, updated_at DESC)
    WHERE is_archived = FALSE;
