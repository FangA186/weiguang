ALTER TABLE chat_import_batches ADD COLUMN IF NOT EXISTS voice_style JSONB NOT NULL DEFAULT '{}'::jsonb;
CREATE TABLE IF NOT EXISTS speech_turns (
    request_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    conversation_id TEXT,
    persona_id TEXT,
    voice TEXT NOT NULL,
    model TEXT NOT NULL,
    sample_rate INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    plan JSONB NOT NULL DEFAULT '[]'::jsonb,
    pcm BYTEA,
    audio_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_speech_turns_owner ON speech_turns(user_id, created_at DESC);
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS speech_turn_id TEXT;
