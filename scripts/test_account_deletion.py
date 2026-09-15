#!/usr/bin/env python3
"""Exercise self-service account deletion with a disposable database fixture."""

from __future__ import annotations

import uuid
import sys
from pathlib import Path

import psycopg
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app import SESSION_COOKIE, app, app_data_store
from backend.config import Settings


def main() -> None:
    if not app_data_store:
        raise SystemExit("DATABASE_URL is required")
    suffix = uuid.uuid4().hex
    email = f"delete-{suffix}@example.invalid"
    profile, token = app_data_store.register(email, "DeleteFixture123!", "注销测试")
    user_id = str(profile["id"])
    try:
        with app_data_store._connect() as connection:
            connection.execute(
                "INSERT INTO user_voice_settings(user_id, character_manifest) VALUES(%s, %s)",
                (user_id, "fixture"),
            )
            connection.execute(
                "INSERT INTO chat_conversations(id, user_id, title) VALUES(%s, %s, %s)",
                (f"delete-{suffix}", user_id, "fixture"),
            )
            connection.execute(
                """
                INSERT INTO chat_messages(conversation_id, user_id, legacy_id, role, content)
                VALUES(%s, %s, 1, 'user', 'fixture')
                """,
                (f"delete-{suffix}", user_id),
            )
            connection.execute(
                "INSERT INTO community_stories(user_id, legacy_id, story_json) VALUES(%s, %s, %s::jsonb)",
                (user_id, suffix, '{"fixture":true}'),
            )
            connection.execute(
                "INSERT INTO usage_events(user_id, request_id, metric, quantity) VALUES(%s, %s, 'ai_reply', 1)",
                (user_id, f"delete-{suffix}"),
            )

        client = TestClient(app)
        client.cookies.set(SESSION_COOKIE, token)
        result = client.delete("/api/auth/me")
        assert result.status_code == 200, result.text
        body = result.json()
        assert body["status"] == "deleted"
        assert body["session"] == {"cookie_cleared": True, "revoked": True}
        assert body["remote_cleanup"]["status"] == "complete"
        assert body["deleted_counts"]["app_users"] == 1
        assert client.get("/api/auth/me").status_code == 401

        with psycopg.connect(Settings.from_env().database_url) as connection:
            for table in (
                "app_sessions",
                "user_voice_settings",
                "chat_conversations",
                "chat_messages",
                "community_stories",
                "usage_events",
            ):
                assert connection.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE user_id = %s", (user_id,)
                ).fetchone()[0] == 0, table
            assert connection.execute("SELECT COUNT(*) FROM app_users WHERE id = %s", (user_id,)).fetchone()[0] == 0
    finally:
        # Safe if the endpoint already removed the disposable fixture.
        with app_data_store._connect() as connection:
            connection.execute("DELETE FROM app_users WHERE id = %s", (user_id,))
    print("PASS DELETE /api/auth/me local cascade, session revocation and stable response")


if __name__ == "__main__":
    main()
