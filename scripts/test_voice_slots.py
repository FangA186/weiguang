#!/usr/bin/env python3
"""Regression checks for multi-voice ownership, deletion, and compensation.

The persistence check refuses non-loopback PostgreSQL and deletes every row it
creates. Provider checks use in-process fakes and never contact Bailian or OSS.
"""

from __future__ import annotations

import asyncio
import os
import re
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse
from typing import Any

from dotenv import load_dotenv
from fastapi import HTTPException

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.voice_store import VoiceCloneStore  # noqa: E402
from backend.billing_store import BillingStore  # noqa: E402
import backend.app as service  # noqa: E402


def local_database_url() -> str:
    load_dotenv(REPO_ROOT / ".env")
    value = os.getenv("VOICE_SLOT_TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not value:
        raise RuntimeError("set VOICE_SLOT_TEST_DATABASE_URL or a local DATABASE_URL")
    if urlparse(value).hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise RuntimeError("refusing non-local database for voice slot regression")
    return value


def assert_store_keeps_three_active(prefix: str) -> None:
    store = VoiceCloneStore(local_database_url())
    user_a = f"{prefix}-a"
    user_b = f"{prefix}-b"
    try:
        generated_prefix = VoiceCloneStore.provider_prefix_for_request(f"{prefix}-request")
        assert generated_prefix == VoiceCloneStore.provider_prefix_for_request(f"{prefix}-request")
        assert len(generated_prefix) == 10 and re.fullmatch(r"[A-Za-z0-9]{10}", generated_prefix)
        with store._connect() as connection:
            migration_row = connection.execute(
                "SELECT to_regclass('public.voice_clone_operations') AS table_name"
            ).fetchone()
        assert migration_row["table_name"] == "voice_clone_operations"
        for index in range(3):
            store.save(
                user_id=user_a,
                voice_id=f"{prefix}-voice-{index}",
                object_key=f"voice-references/{prefix}-{index}.wav",
                reference_filename=f"voice-{index}.wav",
                reference_size=100,
                reference_duration=10.0,
                target_model="fake-tts",
            )
        store.save(
            user_id=user_b,
            voice_id=f"{prefix}-other",
            object_key=f"voice-references/{prefix}-other.wav",
            reference_filename="other.wav",
            reference_size=100,
            reference_duration=10.0,
            target_model="fake-tts",
        )
        assert len(store.list_active(user_a)) == 3
        assert len(store.list_active(user_b)) == 1
        assert store.get_owned_active(user_b, f"{prefix}-voice-0") is None
        assert store.deactivate_owned(user_a, f"{prefix}-voice-0") is not None
        assert len(store.list_active(user_a)) == 2
    finally:
        with store._connect() as connection:  # test-only scoped cleanup
            connection.execute("DELETE FROM voice_clones WHERE user_id LIKE %s", (f"{prefix}%",))
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM voice_clones WHERE user_id LIKE %s", (f"{prefix}%",)
            ).fetchone()
        assert int(row["count"]) == 0


class FakeVoiceStore:
    def __init__(self) -> None:
        self.records: dict[str, dict[str, Any]] = {
            "voice-current": {"voice_id": "voice-current", "user_id": "user-a", "active": True},
            "voice-fallback": {"voice_id": "voice-fallback", "user_id": "user-a", "active": True},
            "voice-other": {"voice_id": "voice-other", "user_id": "user-b", "active": True},
        }
        self.fail_save = False

    def get_owned_active(self, user_id: str, voice_id: str) -> dict[str, Any] | None:
        record = self.records.get(voice_id)
        return dict(record) if record and record["user_id"] == user_id and record["active"] else None

    def list_active(self, user_id: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self.records.values() if row["user_id"] == user_id and row["active"]]

    def deactivate_owned(self, user_id: str, voice_id: str) -> dict[str, Any] | None:
        record = self.records.get(voice_id)
        if not record or record["user_id"] != user_id or not record["active"]:
            return None
        record["active"] = False
        return dict(record)

    def latest(self, user_id: str) -> dict[str, Any] | None:
        rows = self.list_active(user_id)
        return rows[0] if rows else None

    def save(self, **_: Any) -> dict[str, Any]:
        if self.fail_save:
            raise RuntimeError("simulated persistence failure")
        raise AssertionError("save was not expected")


class FakeAppDataStore:
    def __init__(self) -> None:
        self.settings = {"speaker": "voice-current", "character_manifest": "manifest", "settings_json": {}}

    def get_voice_settings(self, _: str) -> dict[str, Any]:
        return dict(self.settings)

    def save_voice_settings(self, _: str, data: dict[str, Any]) -> dict[str, Any]:
        self.settings.update(data)
        return dict(self.settings)


class FakeProvider:
    delete_calls: list[str] = []
    fail_delete = False
    list_calls: list[str] = []
    voices_by_prefix: dict[str, list[str]] = {}
    fail_list = False

    def __init__(self, _: Any) -> None:
        pass

    async def delete_voice(self, *, voice_id: str) -> dict[str, Any]:
        type(self).delete_calls.append(voice_id)
        if type(self).fail_delete:
            raise RuntimeError("simulated provider failure")
        return {"request_id": "fake-delete"}

    async def create_voice(self, **_: Any) -> dict[str, Any]:
        return {"voice_id": "voice-orphan", "target_model": "fake-tts", "request_id": "fake-create"}

    async def list_voices(self, *, prefix: str, **_: Any) -> list[str]:
        type(self).list_calls.append(prefix)
        if type(self).fail_list:
            raise RuntimeError("simulated list failure")
        return list(type(self).voices_by_prefix.get(prefix, []))

    async def voice_exists(self, *, voice_id: str) -> bool:
        if type(self).fail_list:
            raise RuntimeError("simulated query failure")
        return any(voice_id in voices for voices in type(self).voices_by_prefix.values())


class FakeOSS:
    def __init__(self, _: Any) -> None:
        pass

    def presign_object_download(self, _: str) -> str:
        return "https://example.invalid/reference.wav"


async def assert_endpoint_safety() -> None:
    fake_store = FakeVoiceStore()
    fake_app_data = FakeAppDataStore()
    service.voice_store = fake_store
    service.app_data_store = fake_app_data
    service.BailianVoiceCloneProvider = FakeProvider

    FakeProvider.delete_calls = []
    try:
        await service.delete_voice_clone("voice-other", user_id="user-a")
    except HTTPException as exc:
        assert exc.status_code == 404
    else:
        raise AssertionError("deleting another user's voice must fail")
    assert FakeProvider.delete_calls == []

    FakeProvider.fail_delete = True
    try:
        await service.delete_voice_clone("voice-current", user_id="user-a")
    except HTTPException as exc:
        assert exc.status_code == 502
    else:
        raise AssertionError("provider deletion failure must fail closed")
    assert fake_store.records["voice-current"]["active"] is True

    FakeProvider.fail_delete = False
    result = await service.delete_voice_clone("voice-current", user_id="user-a")
    assert fake_store.records["voice-current"]["active"] is False
    assert result["speaker"] == "voice-fallback"
    assert [item["voice_id"] for item in result["voice_clones"]] == ["voice-fallback"]

    try:
        await service.put_voice_settings(
            service.VoiceSettingsRequest(speaker="voice-other", character_manifest="manifest"),
            user_id="user-a",
        )
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("another user's voice cannot be persisted as speaker")

    # Provider creation succeeded but DB save failed: attempt compensating
    # remote deletion before returning a failure and releasing the reservation.
    fake_store.fail_save = True
    released: list[tuple[str, str]] = []

    async def fake_reserve(*_: Any, **__: Any) -> dict[str, Any]:
        return {"proceed": True}

    async def fake_release(user_id: str, request_id: str, *_: Any) -> None:
        released.append((user_id, request_id))

    original_reserve = service._reserve_usage
    original_release = service._release_usage
    original_oss = service.OSSProvider
    service._reserve_usage = fake_reserve
    service._release_usage = fake_release
    service.OSSProvider = FakeOSS
    FakeProvider.delete_calls = []
    try:
        await service.create_voice_clone(
            service.VoiceCloneRequest(request_id="clone-save-failure", object_key="voice-references/user-a/test.wav"),
            user_id="user-a",
        )
    except HTTPException as exc:
        assert exc.status_code == 502
    else:
        raise AssertionError("persistence failure must fail the clone request")
    finally:
        service._reserve_usage = original_reserve
        service._release_usage = original_release
        service.OSSProvider = original_oss
    assert FakeProvider.delete_calls == ["voice-orphan"]
    assert released == [("user-a", "clone-save-failure")]


class FailSaveStore:
    def __init__(self, inner: VoiceCloneStore) -> None:
        self.inner = inner

    def __getattr__(self, name: str) -> Any:
        return getattr(self.inner, name)

    def save(self, **_: Any) -> dict[str, Any]:
        raise RuntimeError("simulated local save failure")


class FailOnceDeactivateStore:
    def __init__(self, inner: VoiceCloneStore) -> None:
        self.inner = inner
        self.fail_once = True

    def __getattr__(self, name: str) -> Any:
        return getattr(self.inner, name)

    def ensure_deactivated_owned(self, user_id: str, voice_id: str) -> bool:
        if self.fail_once:
            self.fail_once = False
            return False
        return self.inner.ensure_deactivated_owned(user_id, voice_id)


def _assert_recovery_cleanup(store: VoiceCloneStore, billing: BillingStore, prefix: str) -> None:
    with store._connect() as connection:
        connection.execute("DELETE FROM usage_events WHERE user_id LIKE %s", (f"{prefix}%",))
        connection.execute("DELETE FROM voice_clone_operations WHERE user_id LIKE %s", (f"{prefix}%",))
        connection.execute("DELETE FROM voice_clones WHERE user_id LIKE %s", (f"{prefix}%",))
        connection.execute("DELETE FROM subscription_grants WHERE user_id LIKE %s", (f"{prefix}%",))
        connection.execute("DELETE FROM user_subscriptions WHERE user_id LIKE %s", (f"{prefix}%",))
        row = connection.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM usage_events WHERE user_id LIKE %s) AS usage_events,
                (SELECT COUNT(*) FROM voice_clone_operations WHERE user_id LIKE %s) AS operations,
                (SELECT COUNT(*) FROM voice_clones WHERE user_id LIKE %s) AS voices,
                (SELECT COUNT(*) FROM user_subscriptions WHERE user_id LIKE %s) AS subscriptions
            """,
            (f"{prefix}%", f"{prefix}%", f"{prefix}%", f"{prefix}%"),
        ).fetchone()
    assert all(int(row[key]) == 0 for key in row), dict(row)


async def assert_durable_recovery(prefix: str) -> None:
    database_url = local_database_url()
    store = VoiceCloneStore(database_url)
    billing = BillingStore(database_url, enforcement_mode="hard")
    user_id = f"{prefix}-create"
    request_id = f"{prefix}-create-request"
    original_voice_store = service.voice_store
    original_billing_store = service.billing_store
    original_provider = service.BailianVoiceCloneProvider
    original_oss = service.OSSProvider
    try:
        service.voice_store = FailSaveStore(store)
        service.billing_store = billing
        service.BailianVoiceCloneProvider = FakeProvider
        service.OSSProvider = FakeOSS
        FakeProvider.delete_calls = []
        FakeProvider.fail_delete = True

        # Remote create succeeds, local save fails, and all bounded delete
        # retries fail.  The durable operation must hold a slot after the
        # ordinary reservation expires.
        try:
            await service.create_voice_clone(
                service.VoiceCloneRequest(
                    request_id=request_id,
                    object_key=f"voice-references/{user_id}/source.wav",
                ),
                user_id=user_id,
            )
        except HTTPException as exc:
            assert exc.status_code == 502 and exc.detail == "Voice clone compensation failed"
        else:
            raise AssertionError("failed compensation must not report clone creation success")
        assert FakeProvider.delete_calls == ["voice-orphan"] * 3
        pending = store.claim_pending_operations(user_id, limit=1)
        assert pending and pending[0]["status"] == "compensation_pending"
        store.release_claim(int(pending[0]["id"]), str(pending[0]["claim_token"]), "test_pending")

        # The operation is durable but does not double count while its own
        # usage reservation is still active.
        assert billing.get_billing_summary(user_id)["metrics"]["voice_slot"] == {
            "used": 0,
            "reserved": 1,
            "limit": 1,
            "remaining": 0,
        }
        future = datetime.now(timezone.utc) + timedelta(minutes=11)
        summary = billing.get_billing_summary(user_id, now=future)
        assert summary["metrics"]["voice_slot"] == {"used": 1, "reserved": 0, "limit": 1, "remaining": 0}

        # GET is a bounded reconciliation trigger.  Concurrent readers claim
        # the single pending operation once, delete remotely once, and release
        # the original reservation only after that delete succeeds.
        FakeProvider.fail_delete = False
        FakeProvider.delete_calls = []
        await asyncio.gather(*(service.get_voice_clone(user_id=user_id) for _ in range(12)))
        assert FakeProvider.delete_calls == ["voice-orphan"]
        assert store.pending_voice_slot_count(user_id) == 0
        assert billing.get_billing_summary(user_id, now=future)["metrics"]["voice_slot"] == {
            "used": 0,
            "reserved": 0,
            "limit": 1,
            "remaining": 1,
        }

        # Once the provider response has been written to remote_created, its
        # still-valid claim lease prevents concurrent GET reconciliation from
        # taking over the local-save window.
        service.voice_store = store
        leased_user = f"{prefix}-leased-create"
        leased_request = f"{prefix}-leased-request"
        billing.reserve_usage(leased_user, leased_request, {"voice_slot": 1})
        leased_begin = store.begin_create_operation(leased_user, leased_request)
        leased_prefix = leased_begin["operation"]["provider_prefix"]
        leased_voice = f"fake-tts-{leased_prefix}-leased"
        store.mark_remote_create_success(
            int(leased_begin["operation"]["id"]), str(leased_begin["claim_token"]), leased_voice
        )
        FakeProvider.list_calls = []
        FakeProvider.delete_calls = []
        await asyncio.gather(*(service.get_voice_clone(user_id=leased_user) for _ in range(12)))
        assert FakeProvider.list_calls == [] and FakeProvider.delete_calls == []
        assert store.claim_pending_operations(leased_user, limit=1) == []
        store.save(
            user_id=leased_user,
            voice_id=leased_voice,
            object_key=f"voice-references/{prefix}-leased.wav",
            reference_filename="leased.wav",
            reference_size=100,
            reference_duration=10.0,
            target_model="fake-tts",
        )
        store.complete_create_operation(
            int(leased_begin["operation"]["id"]), str(leased_begin["claim_token"]), leased_voice
        )

        # A crash after the remote create response but before its DB update
        # leaves create_pending. Once its lease expires, list_voice finds the
        # sole matching ID and recovery compensates it exactly once.
        crash_user = f"{prefix}-create-crash"
        crash_request = f"{prefix}-create-crash-request"
        billing.reserve_usage(crash_user, crash_request, {"voice_slot": 1})
        crash_begin = store.begin_create_operation(crash_user, crash_request)
        crash_prefix = str(crash_begin["operation"]["provider_prefix"])
        crash_voice = f"fake-tts-{crash_prefix}-recovered"
        with store._connect() as connection:
            connection.execute(
                "UPDATE voice_clone_operations SET claim_expires_at = NOW() - INTERVAL '1 second' WHERE id = %s",
                (crash_begin["operation"]["id"],),
            )
        FakeProvider.list_calls = []
        FakeProvider.delete_calls = []
        FakeProvider.voices_by_prefix = {crash_prefix: [crash_voice]}
        await asyncio.gather(*(service.get_voice_clone(user_id=crash_user) for _ in range(12)))
        assert FakeProvider.list_calls == [crash_prefix]
        assert FakeProvider.delete_calls == [crash_voice]
        assert store.get_operation(int(crash_begin["operation"]["id"]))["status"] == "compensated"

        # A crash after remote delete response but before the status write
        # leaves delete_pending. list_voice not finding the exact ID means the
        # remote delete is already complete, so recovery only deactivates local
        # state and must not issue a second delete call.
        delete_user = f"{prefix}-delete"
        delete_seed = f"{prefix}-delete-create-request"
        delete_prefix = VoiceCloneStore.provider_prefix_for_request(delete_seed)
        delete_voice = f"fake-tts-{delete_prefix}-delete"
        store.save(
            user_id=delete_user,
            voice_id=delete_voice,
            object_key=f"voice-references/{prefix}-delete.wav",
            reference_filename="delete.wav",
            reference_size=100,
            reference_duration=10.0,
            target_model="fake-tts",
        )
        delete_operation = store.begin_delete_operation(delete_user, delete_voice)
        operation = delete_operation["operation"]
        with store._connect() as connection:
            connection.execute(
                "UPDATE voice_clone_operations SET claim_expires_at = NOW() - INTERVAL '1 second' WHERE id = %s",
                (operation["id"],),
            )
        service.voice_store = store
        FakeProvider.voices_by_prefix = {delete_prefix: []}
        FakeProvider.delete_calls = []
        await asyncio.gather(*(service.get_voice_clone(user_id=delete_user) for _ in range(12)))
        assert FakeProvider.delete_calls == []
        assert store.get_owned_active(delete_user, delete_voice) is None
        assert store.pending_operation_count(delete_user) == 0
    finally:
        FakeProvider.fail_delete = False
        service.voice_store = original_voice_store
        service.billing_store = original_billing_store
        service.BailianVoiceCloneProvider = original_provider
        service.OSSProvider = original_oss
        _assert_recovery_cleanup(store, billing, prefix)


def main() -> None:
    prefix = f"voice-slot-test-{uuid.uuid4().hex}"
    assert_store_keeps_three_active(prefix)
    asyncio.run(assert_endpoint_safety())
    asyncio.run(assert_durable_recovery(prefix))
    print("voice slot checks passed")


if __name__ == "__main__":
    main()
