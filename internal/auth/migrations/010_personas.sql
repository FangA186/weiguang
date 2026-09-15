-- 010_personas.sql: Ex-Skill 5-layer persona distillation & memory store

CREATE TABLE IF NOT EXISTS personas (
    id                TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id           TEXT NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    slug              TEXT NOT NULL,
    name              TEXT NOT NULL,
    avatar_url        TEXT,
    persona           JSONB NOT NULL DEFAULT '{}'::jsonb,
    memories          JSONB NOT NULL DEFAULT '{}'::jsonb,
    voice_id          TEXT NOT NULL DEFAULT '',
    compiled_prompt   TEXT NOT NULL DEFAULT '',
    status            TEXT NOT NULL DEFAULT 'ready',
    source_type       TEXT NOT NULL DEFAULT 'manual',
    source_import_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_active         BOOLEAN NOT NULL DEFAULT false,
    is_builtin        BOOLEAN NOT NULL DEFAULT false,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, slug)
);

CREATE INDEX IF NOT EXISTS idx_personas_user_id ON personas(user_id);
CREATE INDEX IF NOT EXISTS idx_personas_active ON personas(user_id, is_active) WHERE is_active = true;

CREATE TABLE IF NOT EXISTS persona_versions (
    id              BIGSERIAL PRIMARY KEY,
    persona_id      TEXT NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    version_tag     TEXT NOT NULL,
    persona         JSONB NOT NULL DEFAULT '{}'::jsonb,
    memories        JSONB NOT NULL DEFAULT '{}'::jsonb,
    compiled_prompt TEXT NOT NULL DEFAULT '',
    message         TEXT NOT NULL DEFAULT '',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_persona_versions_persona_id ON persona_versions(persona_id);

CREATE TABLE IF NOT EXISTS persona_corrections (
    id              BIGSERIAL PRIMARY KEY,
    persona_id      TEXT NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    user_id         TEXT NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    correction_type TEXT NOT NULL DEFAULT 'linguistic',
    user_feedback   TEXT NOT NULL,
    rule_text       TEXT NOT NULL,
    target_layer    TEXT NOT NULL DEFAULT 'L2',
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_persona_corrections_persona_id ON persona_corrections(persona_id);
