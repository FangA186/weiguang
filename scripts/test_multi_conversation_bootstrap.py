"""Replay bootstrap migrations after multiple chats exist; rollback test schema."""
import sys
from pathlib import Path
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import psycopg
from psycopg import sql
from backend.config import Settings

root = Path(__file__).resolve().parents[1]
with psycopg.connect(Settings.from_env().database_url) as connection:
    try:
        schema = 'bootstrap_test_' + uuid4().hex
        connection.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
        connection.execute(sql.SQL('SET LOCAL search_path TO {}').format(sql.Identifier(schema)))
        bootstrap = (root/'backend/migrations/005_app_data_persistence.sql').read_text()
        multiple = (root/'internal/auth/migrations/012_multi_conversations.sql').read_text()
        connection.execute(bootstrap)
        connection.execute(multiple)
        connection.execute("INSERT INTO app_users(id,email,nickname) VALUES('u','fixture@example.invalid','fixture')")
        connection.execute("INSERT INTO chat_conversations(id,user_id) VALUES('a','u'),('b','u')")
        for _ in range(2):
            connection.execute(bootstrap)
            connection.execute(multiple)
        assert connection.execute('SELECT count(*) FROM chat_conversations').fetchone()[0] == 2
        assert connection.execute("SELECT to_regclass('uq_chat_conversations_active_user')").fetchone()[0] is None
    finally:
        connection.rollback()
print('PASS fresh install and repeated bootstrap with multiple chats; test schema rolled back')
