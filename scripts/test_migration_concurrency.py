#!/usr/bin/env python3
"""Check concurrent Store bootstrap without touching business rows."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app_data_store import AppDataStore
from backend.billing_store import BillingStore
from backend.chat_import_store import ChatImportStore
from backend.config import Settings
from backend.voice_store import VoiceCloneStore


def bootstrap(database_url: str) -> str:
    AppDataStore(database_url)
    BillingStore(database_url)
    VoiceCloneStore(database_url)
    ChatImportStore(database_url)
    return "ok"


def main() -> None:
    database_url = Settings.from_env().database_url
    if not database_url:
        raise SystemExit("DATABASE_URL is required")
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert list(pool.map(lambda _: bootstrap(database_url), range(8))) == ["ok"] * 8
    with psycopg.connect(database_url) as connection:
        duplicate = connection.execute(
            """
            SELECT version, COUNT(*)
            FROM weiguang_schema_migrations
            GROUP BY version
            HAVING COUNT(*) > 1
            """
        ).fetchall()
        assert not duplicate, duplicate
    print("PASS concurrent Store bootstrap serialized by versioned advisory-lock migrations")


if __name__ == "__main__":
    main()
