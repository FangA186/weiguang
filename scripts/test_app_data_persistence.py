from __future__ import annotations

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app_data_store import AppDataStore
from backend.config import Settings


def main() -> None:
    store = AppDataStore(Settings.from_env().database_url)
    suffix = uuid.uuid4().hex[:10]
    user_id = f"migration-test-{suffix}"
    email = f"migration-{suffix}@example.invalid"
    try:
        profile, token, counts = store.migrate_legacy(
            {
                "profile": {"id": user_id, "email": email, "nickname": "迁移测试"},
                "profile_id": user_id,
                "voice_settings": {"speaker": "test-voice", "character_manifest": "测试角色"},
                "chat_history": [
                    {"id": 1, "role": "user", "content": "你好", "kind": "text", "status": "completed"},
                    {"id": 2, "role": "ai", "content": "我在", "kind": "text", "status": "completed"},
                ],
                "stories": [{"id": "story-1", "quote": "测试寄语"}],
            }
        )
        assert profile["id"] == user_id
        assert store.user_id_for_session(token) == user_id
        assert counts == {"messages": 2, "stories": 1, "settings": 1}
        assert len(store.history(user_id)["messages"]) == 2
        assert store.get_voice_settings(user_id)["speaker"] == "test-voice"

        registered, _ = store.register(email, "Database-password1!", "数据库用户")
        assert registered["id"] == user_id
        logged_in, _ = store.login(email, "Database-password1!")
        assert logged_in["id"] == user_id
    finally:
        with store._connect() as connection:
            connection.execute("DELETE FROM app_users WHERE id = %s", (user_id,))


if __name__ == "__main__":
    main()
