#!/usr/bin/env python3
"""Mock-only regression checks for paid endpoint quota boundaries.

No provider or database is contacted.  Run with ``.venv/bin/python
scripts/test_quota_endpoints.py``.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import sys
import threading
from dataclasses import replace
from pathlib import Path
from typing import Any

os.environ.update(
    DATABASE_URL="",
    QWEN_API_KEY="test-key",
    QWEN_BASE_URL="https://example.invalid/compatible-mode/v1",
    BAILIAN_TTS_URL="https://example.invalid/tts",
    BAILIAN_VOICE_CLONE_URL="https://example.invalid/voice-clone",
    BILLING_ENFORCEMENT_MODE="hard",
    APP_ENV="test",
)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import HTTPException, Response
from fastapi.testclient import TestClient

import backend.app as service
from backend.config import Settings


class QuotaExceededError(Exception):
    def __init__(self, metric: str) -> None:
        self.metric = metric

    def to_detail(self) -> dict[str, Any]:
        return {
            "code": "quota_exceeded",
            "metric": self.metric,
            "used": 1,
            "limit": 1,
            "remaining": 0,
            "reset_at": "2030-01-01T00:00:00+00:00",
        }


class FakeBillingStore:
    def __init__(self) -> None:
        self.fail_metric: str | None = None
        self.reserves: list[tuple[str, str, dict[str, float]]] = []
        self.confirms: list[tuple[str, str, str, float | None]] = []
        self.confirm_raw_usage: list[tuple[str, str, str, dict[str, Any] | None]] = []
        self.releases: list[tuple[str, str, tuple[str, ...] | None]] = []
        self.states: dict[tuple[str, str, str], str] = {}
        self.request_owners: dict[str, str] = {}
        self.lock = threading.Lock()

    def reserve_usage(
        self,
        user_id: str,
        request_id: str,
        metrics: dict[str, float],
        **_: Any,
    ) -> dict[str, Any]:
        with self.lock:
            self.reserves.append((user_id, request_id, dict(metrics)))
            if self.fail_metric in metrics:
                raise QuotaExceededError(str(self.fail_metric))
            owner = self.request_owners.get(request_id)
            if owner and owner != user_id:
                raise service.UsageRequestConflictError("request_id belongs to another user")
            self.request_owners[request_id] = user_id
            states = {self.states.get((user_id, request_id, metric)) for metric in metrics}
            if "reserved" in states:
                return {"request_id": request_id, "proceed": False, "state": "request_in_progress", "metrics": {}}
            if "completed" in states:
                return {"request_id": request_id, "proceed": False, "state": "request_already_completed", "metrics": {}}
            if "expired" in states:
                return {"request_id": request_id, "proceed": False, "state": "request_expired", "metrics": {}}
            for metric in metrics:
                self.states[(user_id, request_id, metric)] = "reserved"
        return {"request_id": request_id, "proceed": True, "state": "reserved", "metrics": {}}

    def confirm_usage(
        self,
        user_id: str,
        request_id: str,
        metric: str,
        actual_quantity: float | None = None,
        raw_usage: dict[str, Any] | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        with self.lock:
            self.confirms.append((user_id, request_id, metric, actual_quantity))
            self.confirm_raw_usage.append((user_id, request_id, metric, raw_usage))
            self.states[(user_id, request_id, metric)] = "completed"
        return {"request_id": request_id, "metrics": {}}

    def release_usage(self, user_id: str, request_id: str, metrics: list[str] | None = None) -> dict[str, Any]:
        with self.lock:
            self.releases.append((user_id, request_id, tuple(metrics) if metrics else None))
            selected = metrics or [metric for owner, seen_id, metric in self.states if owner == user_id and seen_id == request_id]
            for metric in selected:
                if self.states.get((user_id, request_id, metric)) == "reserved":
                    self.states[(user_id, request_id, metric)] = "released"
        return {"request_id": request_id, "metrics": {}}

    def get_monitoring_summary(self, **_: Any) -> dict[str, Any]:
        return {"alerts": [], "cost": {"estimated_cny": 0}}


class FakeAppDataStore:
    def user_id_for_session(self, token: str | None) -> str | None:
        return {"session-a": "user-a", "session-b": "user-b"}.get(token or "")


class FakeLLMProvider:
    calls = 0
    fail = False
    fail_after_delta = False
    wait_for_cancel = False

    def __init__(self, _: Any) -> None:
        pass

    async def complete_with_usage(self, *_: Any, **__: Any) -> dict[str, Any]:
        type(self).calls += 1
        if type(self).fail:
            raise RuntimeError("provider failed")
        return {
            "content": "可以。",
            "model": "fake-llm",
            "provider_request_id": "provider-llm",
            "usage": {"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3},
            "requested_max_completion_tokens": 512,
            "input_bytes": 128,
            "context_trimmed_messages": 2,
            "finish_reason": "stop",
        }

    async def stream_events(self, *_: Any, **__: Any):
        type(self).calls += 1
        if type(self).fail:
            raise RuntimeError("provider failed")
        yield {"type": "delta", "text": "可以。", "provider_request_id": "provider-llm"}
        if type(self).fail_after_delta:
            raise RuntimeError("provider failed after delta")
        if type(self).wait_for_cancel:
            await asyncio.Event().wait()
        yield {
            "type": "usage",
            "provider_request_id": "provider-llm",
            "usage": {"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3},
            "requested_max_completion_tokens": 512,
            "input_bytes": 128,
            "context_trimmed_messages": 2,
            "finish_reason": "stop",
        }


class FakeTTSProvider:
    calls = 0
    fail_after_pcm = False
    wait_after_pcm = False
    audio_duration_seconds = 0.01
    stream_pcm_bytes = 480
    stream_closed = False
    fail_synthesize = False
    last_options: dict[str, Any] = {}

    def __init__(self, _: Any) -> None:
        pass

    async def synthesize(self, *_: Any, **__: Any) -> dict[str, Any]:
        type(self).last_options = __
        type(self).calls += 1
        if type(self).fail_synthesize:
            raise RuntimeError("sensitive provider failure")
        return {
            "audio_url": "https://example.invalid/audio.wav",
            "model": "fake-tts",
            "provider_request_id": "provider-tts",
            "usage": {"characters": 3},
            "usage_characters": 3,
            "word_timestamps": [{"text": "好", "begin_time": 0, "end_time": 100}],
            "pcm_bytes": 4800,
            "audio_duration_seconds": type(self).audio_duration_seconds,
        }

    async def stream_synthesize(self, *_: Any, **__: Any):
        type(self).last_options = __
        type(self).calls += 1
        try:
            pcm = base64.b64encode(b"\x00" * type(self).stream_pcm_bytes).decode()
            yield {
                "audio_data": pcm,
                "pcm_bytes": type(self).stream_pcm_bytes,
                "provider_request_id": "provider-tts",
                "usage": {"characters": 3},
                "usage_characters": 3,
                "word_timestamps": [{"text": "好", "begin_time": 0, "end_time": 10}],
                "audio_duration_seconds": type(self).audio_duration_seconds,
            }
            if type(self).fail_after_pcm:
                raise RuntimeError("tts failed after pcm")
            if type(self).wait_after_pcm:
                await asyncio.Event().wait()
            yield {"audio_url": "https://example.invalid/audio.pcm"}
        finally:
            type(self).stream_closed = True


class FakeVoiceStore:
    def __init__(
        self,
        records: dict[str, dict[str, Any]] | None = None,
        *,
        fail_save: bool = False,
        fail_deactivate: bool = False,
    ) -> None:
        self.records = records or {}
        self.fail_save = fail_save
        self.fail_deactivate = fail_deactivate

    def get_by_voice_id(self, voice_id: str) -> dict[str, Any] | None:
        record = self.records.get(voice_id)
        return dict(record) if record else None

    def get_owned_active(self, user_id: str, voice_id: str) -> dict[str, Any] | None:
        record = self.records.get(voice_id)
        if not record or record.get("user_id") != user_id or record.get("active") is not True:
            return None
        return dict(record)

    def latest(self, user_id: str) -> dict[str, Any] | None:
        for record in self.records.values():
            if record.get("user_id") == user_id and record.get("active") is True:
                return dict(record)
        return None

    def rename_owned(self, user_id: str, voice_id: str, name: str) -> dict[str, Any] | None:
        record = self.get_owned_active(user_id, voice_id)
        if not record:
            return None
        self.records[voice_id]["reference_filename"] = name
        return {**record, "reference_filename": name}

    def save(self, **values: Any) -> dict[str, Any]:
        if self.fail_save:
            raise RuntimeError("local voice persistence failed")
        record = {**values, "active": True}
        self.records[str(values["voice_id"])] = record
        return dict(record)

    def deactivate_owned(self, user_id: str, voice_id: str) -> dict[str, Any] | None:
        if self.fail_deactivate:
            raise RuntimeError("local voice deactivation failed")
        record = self.records.get(voice_id)
        if not record or record.get("user_id") != user_id or record.get("active") is not True:
            return None
        record["active"] = False
        return dict(record)

    def list_active(self, user_id: str) -> list[dict[str, Any]]:
        return [dict(record) for record in self.records.values() if record.get("user_id") == user_id and record.get("active")]


class FakeVoiceCloneProvider:
    calls = 0
    delete_calls = 0
    delete_failures_remaining = 0
    delete_always_fail = False

    def __init__(self, _: Any) -> None:
        pass

    async def create_voice(self, **_: Any) -> dict[str, Any]:
        type(self).calls += 1
        return {"voice_id": "fake-clone", "target_model": "fake-tts", "request_id": "provider-clone"}

    async def delete_voice(self, **_: Any) -> dict[str, Any]:
        type(self).delete_calls += 1
        if type(self).delete_always_fail:
            raise RuntimeError("remote deletion failed")
        if type(self).delete_failures_remaining > 0:
            type(self).delete_failures_remaining -= 1
            raise RuntimeError("transient remote deletion failed")
        return {"request_id": "provider-delete"}


class FakeOSSProvider:
    def __init__(self, _: Any) -> None:
        pass

    def presign_object_download(self, _: str) -> str:
        return "https://example.invalid/reference.wav"


class FakeScreenshotExtractor:
    calls = 0

    def __init__(self, _: Any) -> None:
        pass

    async def extract_from_attachments(self, _: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
        type(self).calls += 1
        return [], []


def payload(request_id: str, content: str | list[dict[str, Any]] = "hello") -> dict[str, Any]:
    return {"request_id": request_id, "messages": [{"role": "user", "content": content}]}


def reserve_for(store: FakeBillingStore, request_id: str) -> dict[str, float]:
    for _, seen_id, metrics in reversed(store.reserves):
        if seen_id == request_id:
            return metrics
    raise AssertionError(f"missing reservation for {request_id}")


def has_confirmation(store: FakeBillingStore, request_id: str, metric: str = "ai_reply") -> bool:
    return any(seen_id == request_id and seen_metric == metric for _, seen_id, seen_metric, _ in store.confirms)


def has_release(store: FakeBillingStore, request_id: str, metric: str) -> bool:
    return any(seen_id == request_id and metrics and metric in metrics for _, seen_id, metrics in store.releases)


def raw_confirmation_for(store: FakeBillingStore, request_id: str, metric: str) -> dict[str, Any]:
    for _, seen_id, seen_metric, raw in reversed(store.confirm_raw_usage):
        if seen_id == request_id and seen_metric == metric:
            return raw or {}
    raise AssertionError(f"missing raw confirmation for {request_id}/{metric}")


async def assert_stream_cancel_confirms(store: FakeBillingStore) -> None:
    request_id = "stream-cancel"
    FakeLLMProvider.wait_for_cancel = True
    try:
        response = await service.chat_stream(service.ChatRequest(**payload(request_id)), user_id="user-a")
        iterator = response.body_iterator
        first = await anext(iterator)
        first_text = first.decode() if isinstance(first, bytes) else str(first)
        assert "text.delta" in first_text
        await iterator.aclose()
        await asyncio.sleep(0)
    finally:
        FakeLLMProvider.wait_for_cancel = False
    assert has_confirmation(store, request_id), "delta before disconnect must confirm the LLM reservation"
    assert not has_release(store, request_id, "ai_reply"), "delta before disconnect must not release usage"


async def assert_tts_cancel_confirms(store: FakeBillingStore) -> None:
    request_id = "tts-stream-cancel"
    FakeTTSProvider.wait_after_pcm = True
    FakeTTSProvider.stream_closed = False
    try:
        response = await service.chat_and_tts_stream(service.ChatRequest(**payload(request_id)), user_id="user-a")
        iterator = response.body_iterator
        while True:
            item = await anext(iterator)
            text = item.decode() if isinstance(item, bytes) else str(item)
            if "audio.delta" in text:
                break
        await iterator.aclose()
        await asyncio.sleep(0)
    finally:
        FakeTTSProvider.wait_after_pcm = False
    child_id = f"{request_id}.tts.0"
    assert has_confirmation(store, child_id, "ai_voice_seconds")
    assert not has_release(store, child_id, "ai_voice_seconds")
    assert FakeTTSProvider.stream_closed is True, "cancelling the browser stream must close Provider TTS"
    raw = raw_confirmation_for(store, child_id, "ai_voice_seconds")["quota_settlement"]
    assert raw["delivered_pcm_bytes"] == FakeTTSProvider.stream_pcm_bytes


async def assert_concurrent_replay_calls_provider_once(request_id: str) -> None:
    before = FakeLLMProvider.calls
    request = service.ChatRequest(**payload(request_id))
    results = await asyncio.gather(
        *(service.chat(request, user_id="user-a") for _ in range(100)),
        return_exceptions=True,
    )
    assert sum(isinstance(result, dict) for result in results) == 1
    assert all(
        isinstance(result, (dict, service._RequestReplayHTTPError)) for result in results
    ), "only the first request may enter the Provider path"
    assert FakeLLMProvider.calls == before + 1


def assert_production_cookie_secure_guard() -> None:
    original = {name: os.environ.get(name) for name in ("APP_ENV", "COOKIE_SECURE")}
    try:
        os.environ["APP_ENV"] = "production"
        os.environ["COOKIE_SECURE"] = "false"
        try:
            Settings.from_env()
        except ValueError as exc:
            assert str(exc) == "COOKIE_SECURE must be true when APP_ENV=production"
        else:
            raise AssertionError("production must reject COOKIE_SECURE=false")
        os.environ["COOKIE_SECURE"] = "true"
        assert Settings.from_env().cookie_secure is True
    finally:
        for name, value in original.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def main() -> None:
    assert_production_cookie_secure_guard()
    service.settings = replace(
        service.settings,
        database_url="test",
        billing_enforcement_mode="hard",
        billing_hard_user_ids=frozenset({"user-a"}),
        cookie_secure=False,
    )
    store = FakeBillingStore()
    service.billing_store = store
    service.app_data_store = FakeAppDataStore()
    service.voice_store = None
    service.QuotaExceededError = QuotaExceededError
    service.BailianLLMProvider = FakeLLMProvider
    service.BailianTTSProvider = FakeTTSProvider
    service.BailianVoiceCloneProvider = FakeVoiceCloneProvider
    service.ScreenshotExtractor = FakeScreenshotExtractor
    service.OSSProvider = FakeOSSProvider

    service.settings = replace(service.settings, cookie_secure=True)
    cookie_response = Response()
    service._set_session_cookie(cookie_response, "test-session")
    assert "Secure" in cookie_response.headers["set-cookie"]
    service.settings = replace(service.settings, cookie_secure=False)
    client = TestClient(service.app)
    client.cookies.set(service.SESSION_COOKIE, "session-a")

    before = FakeLLMProvider.calls
    assert client.post("/api/chat", json=payload("too-long", "字" * 2001)).status_code == 422
    too_many_images = [{"type": "image_url", "image_url": {"url": f"https://example.invalid/{i}.png"}} for i in range(5)]
    assert client.post("/api/chat", json=payload("too-many-images", too_many_images)).status_code == 422
    assert FakeLLMProvider.calls == before

    assert client.get("/api/admin/monitoring/summary").status_code == 200
    denied_monitor = TestClient(service.app)
    denied_monitor.cookies.set(service.SESSION_COOKIE, "session-b")
    assert denied_monitor.get("/api/admin/monitoring/summary").status_code == 403

    # Paid endpoints reject missing/forged client identity before Provider work.
    before = FakeLLMProvider.calls
    response = TestClient(service.app).post("/api/chat", json=payload("anonymous"))
    assert response.status_code == 401
    response = TestClient(service.app).post(
        "/api/chat", json=payload("forged"), headers={"X-Weiguang-User-ID": "user-b"}
    )
    assert response.status_code == 401 and FakeLLMProvider.calls == before

    # Hard quota denial happens before the LLM is constructed/called.
    store.fail_metric = "ai_reply"
    response = client.post("/api/chat", json=payload("hard-deny"))
    assert response.status_code == 402 and response.json()["code"] == "quota_exceeded"
    assert FakeLLMProvider.calls == before
    store.fail_metric = None

    # Provider failure returns the reservation to the pool.
    FakeLLMProvider.fail = True
    response = client.post("/api/chat", json=payload("provider-failure"))
    assert response.status_code == 502
    assert any(item[1] == "provider-failure" for item in store.releases)
    FakeLLMProvider.fail = False

    # Text-only and multimodal input reserve exactly their separate metrics.
    assert client.post("/api/chat", json=payload("plain")).status_code == 200
    assert reserve_for(store, "plain") == {"ai_reply": 1.0}
    plain_usage = raw_confirmation_for(store, "plain", "ai_reply")
    assert plain_usage["requested_max_completion_tokens"] == 512
    assert plain_usage["input_bytes"] == 128
    assert plain_usage["context_trimmed_messages"] == 2
    assert plain_usage["finish_reason"] == "stop"
    multimodal = [
        {"type": "text", "text": "describe"},
        {"type": "image_url", "image_url": {"url": "https://example.invalid/a.png"}},
        {"type": "image_url", "image_url": {"url": "https://example.invalid/b.png"}},
        {"type": "video_url", "video_url": {"url": "https://example.invalid/a.mp4"}},
    ]
    assert client.post("/api/chat", json=payload("multimodal", multimodal)).status_code == 200
    assert reserve_for(store, "multimodal") == {"ai_reply": 1.0, "image": 2.0, "video": 1.0}
    earlier_media = [
        {"role": "user", "content": [{"type": "image_url", "image_url": {"url": "https://example.invalid/old.png"}}]},
        {"role": "assistant", "content": [{"type": "video_url", "video_url": {"url": "https://example.invalid/old.mp4"}}]},
        {"role": "user", "content": "latest text only"},
    ]
    assert client.post("/api/chat", json={"request_id": "earlier-media", "messages": earlier_media}).status_code == 200
    assert reserve_for(store, "earlier-media") == {"ai_reply": 1.0, "image": 1.0, "video": 1.0}

    # An idempotent quota row is not enough: replays must never repeat the Provider call.
    before = FakeLLMProvider.calls
    assert client.post("/api/chat", json=payload("completed-replay")).status_code == 200
    response = client.post("/api/chat", json=payload("completed-replay"))
    assert response.status_code == 409 and response.json()["code"] == "request_already_completed"
    assert FakeLLMProvider.calls == before + 1
    before = FakeLLMProvider.calls
    assert client.post("/api/chat", json=payload("cross-user-request")).status_code == 200
    client_b = TestClient(service.app)
    client_b.cookies.set(service.SESSION_COOKIE, "session-b")
    response = client_b.post("/api/chat", json=payload("cross-user-request"))
    assert response.status_code == 409 and response.json()["code"] == "request_id_conflict"
    assert FakeLLMProvider.calls == before + 1
    asyncio.run(assert_concurrent_replay_calls_provider_once("same-request-id-hard"))
    service.settings = replace(service.settings, billing_enforcement_mode="shadow")
    asyncio.run(assert_concurrent_replay_calls_provider_once("same-request-id-shadow"))
    service.settings = replace(service.settings, billing_enforcement_mode="hard")
    store.request_owners["expired-replay"] = "user-a"
    store.states[("user-a", "expired-replay", "ai_reply")] = "expired"
    before = FakeLLMProvider.calls
    response = client.post("/api/chat", json=payload("expired-replay"))
    assert response.status_code == 409 and response.json()["code"] == "request_expired"
    assert FakeLLMProvider.calls == before

    # TTS endpoints must preserve replay 409 instead of turning it into 502.
    before = FakeTTSProvider.calls
    tts_body = {"request_id": "tts-replay", "text": "朗读"}
    assert client.post("/api/tts", json=tts_body).status_code == 200
    response = client.post("/api/tts", json=tts_body)
    assert response.status_code == 409 and response.json()["code"] == "request_already_completed"
    assert FakeTTSProvider.calls == before + 1
    message_tts_body = {"request_id": "message-tts-replay", "text": "朗读"}
    assert client.post("/api/messages/tts", json=message_tts_body).status_code == 200
    response = client.post("/api/messages/tts", json=message_tts_body)
    assert response.status_code == 409 and response.json()["code"] == "request_already_completed"
    FakeTTSProvider.fail_synthesize = True
    response = client.post("/api/messages/tts", json={"request_id": "message-tts-error", "text": "朗读"})
    assert response.status_code == 502
    assert response.json()["detail"] == "Bailian message TTS request failed"
    assert "sensitive provider failure" not in response.json()["detail"]
    FakeTTSProvider.fail_synthesize = False
    chat_tts_body = payload("chat-tts-replay")
    assert client.post("/api/chat-and-tts", json=chat_tts_body).status_code == 200
    response = client.post("/api/chat-and-tts", json=chat_tts_body)
    assert response.status_code == 409 and response.json()["code"] == "request_already_completed"

    # Voice depletion downgrades chat-and-tts streaming to text and never calls TTS.
    for endpoint in ("/api/tts", "/api/messages/tts", "/api/chat-and-tts", "/api/chat-and-tts/stream"):
        request_id = "options-" + endpoint.strip("/").replace("/", "-")
        is_chat = "/chat-and-tts" in endpoint
        body = payload(request_id) if is_chat else {"request_id": request_id, "text": "朗读"}
        options = {"sample_rate": 48000, "rate": 0.85, "instruction": "平静自然"}
        if not is_chat:
            body.update(options)
        response = client.post(endpoint, json=body, params=options if is_chat else None)
        assert response.status_code == 200, response.text
        assert all(FakeTTSProvider.last_options[key] == value for key, value in options.items())
        if endpoint.endswith("/stream"):
            child_id = request_id + ".tts.0"
            raw = raw_confirmation_for(store, child_id, "ai_voice_seconds")["quota_settlement"]
            assert raw["delivered_seconds"] == round(FakeTTSProvider.stream_pcm_bytes / 96000, 3)
        before = FakeTTSProvider.calls
        invalid = client.post(endpoint, json=body, params={"rate": "nan"} if is_chat else None) if is_chat else client.post(endpoint, json={**body, "rate": 0})
        assert invalid.status_code == 422
        assert FakeTTSProvider.calls == before
    assert service._tts_reservation_seconds("测试语速预算", 0.5) >= service._tts_reservation_seconds("测试语速预算", 1) * 1.99

    store.fail_metric = "ai_voice_seconds"
    FakeTTSProvider.calls = 0
    with client.stream("POST", "/api/chat-and-tts/stream", json=payload("voice-depleted")) as response:
        text = response.read().decode()
    assert response.status_code == 200 and "text.delta" in text and "audio.quota_exhausted" in text
    assert FakeTTSProvider.calls == 0
    store.fail_metric = None

    # Once an LLM delta reaches the browser, cancellation or upstream failure counts as a reply.
    asyncio.run(assert_stream_cancel_confirms(store))
    FakeLLMProvider.fail_after_delta = True
    with client.stream("POST", "/api/chat/stream", json=payload("stream-failure-after-delta")) as response:
        text = response.read().decode()
    assert response.status_code == 200 and "text.delta" in text and '"type":"error"' in text
    assert has_confirmation(store, "stream-failure-after-delta")
    assert not has_release(store, "stream-failure-after-delta", "ai_reply")
    FakeLLMProvider.fail_after_delta = False

    # PCM already sent is a billable TTS result even if its stream later fails or is cancelled.
    FakeTTSProvider.fail_after_pcm = True
    with client.stream("POST", "/api/chat-and-tts/stream", json=payload("tts-failure-after-pcm")) as response:
        text = response.read().decode()
    child_id = "tts-failure-after-pcm.tts.0"
    assert response.status_code == 200 and "audio.error" in text
    assert has_confirmation(store, child_id, "ai_voice_seconds")
    assert not has_release(store, child_id, "ai_voice_seconds")
    FakeTTSProvider.fail_after_pcm = False
    asyncio.run(assert_tts_cancel_confirms(store))

    # A completed non-streaming asset must retain its real, bounded overage.
    FakeTTSProvider.audio_duration_seconds = 2.0
    response = client.post("/api/tts", json={"request_id": "tts-nonstreaming-overage", "text": "短句"})
    assert response.status_code == 200
    child_id = "tts-nonstreaming-overage.tts"
    assert any(seen_id == child_id and metric == "ai_voice_seconds" and quantity == 2.0 for _, seen_id, metric, quantity in store.confirms)
    nonstream_raw = raw_confirmation_for(store, child_id, "ai_voice_seconds")["quota_settlement"]
    assert nonstream_raw["provider_actual_seconds"] == 2.0
    assert nonstream_raw["overage_seconds"] > 0

    # Streaming PCM is capped at its reservation; the observed Provider cost
    # remains in raw_usage and the upstream iterator is explicitly closed.
    FakeTTSProvider.stream_pcm_bytes = 96_000
    FakeTTSProvider.stream_closed = False
    with client.stream("POST", "/api/chat-and-tts/stream", json=payload("tts-over-reservation")) as response:
        text = response.read().decode()
    child_id = "tts-over-reservation.tts.0"
    audio_events = [json.loads(line[6:]) for line in text.splitlines() if line.startswith("data: ")]
    emitted_bytes = sum(
        len(base64.b64decode(event["audio"])) for event in audio_events if event.get("type") == "audio.delta"
    )
    assert emitted_bytes == 48_000
    assert "audio.url" not in text
    assert any(seen_id == child_id and metric == "ai_voice_seconds" and quantity == 1.0 for _, seen_id, metric, quantity in store.confirms)
    stream_raw = raw_confirmation_for(store, child_id, "ai_voice_seconds")["quota_settlement"]
    assert stream_raw["provider_actual_seconds"] == 2.0
    assert stream_raw["truncated_to_reservation"] is True
    assert FakeTTSProvider.stream_closed is True
    assert not has_release(store, child_id, "ai_voice_seconds")
    FakeTTSProvider.audio_duration_seconds = 0.01
    FakeTTSProvider.stream_pcm_bytes = 480

    # Production Origin checks run before cookie-authenticated Provider work.
    service.settings = replace(
        service.settings,
        app_env="production",
        cookie_secure=True,
        public_base_url="https://app.example.test",
        trusted_origins=frozenset({"https://app.example.test"}),
    )
    before = FakeLLMProvider.calls
    assert client.post("/api/chat", json=payload("origin-missing")).status_code == 403
    assert client.post("/api/chat", json=payload("origin-evil"), headers={"Origin": "https://evil.example"}).status_code == 403
    assert FakeLLMProvider.calls == before
    assert client.post("/api/chat", json=payload("origin-trusted"), headers={"Origin": "https://app.example.test"}).status_code == 200
    loopback_scope = {
        "type": "http", "method": "POST", "path": "/api/migrations/local-storage",
        "headers": [], "client": ("127.0.0.1", 12345), "server": ("testserver", 80), "scheme": "http",
    }
    try:
        service.migrate_local_storage(service.LegacyStorageMigrationRequest(profile={}), Response(), service.Request(loopback_scope))
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("production loopback migration must be rejected")
    service.settings = replace(
        service.settings,
        app_env="test",
        cookie_secure=False,
        public_base_url="http://localhost:5173",
        trusted_origins=frozenset({"http://localhost:5173"}),
    )

    # Explicit clone voices must be active and owned by the current user.
    service.voice_store = FakeVoiceStore(
        {
            "voice-own": {"user_id": "user-a", "voice_id": "voice-own", "active": True, "target_model": "fake-tts"},
            "voice-other": {"user_id": "user-b", "voice_id": "voice-other", "active": True, "target_model": "fake-tts"},
            "voice-inactive": {"user_id": "user-a", "voice_id": "voice-inactive", "active": False, "target_model": "fake-tts"},
        }
    )
    before = FakeTTSProvider.calls
    response = client.post("/api/tts", json={"request_id": "voice-other", "text": "朗读", "voice": "voice-other"})
    assert response.status_code == 403 and FakeTTSProvider.calls == before
    response = client.post("/api/tts", json={"request_id": "voice-inactive", "text": "朗读", "voice": "voice-inactive"})
    assert response.status_code == 403 and FakeTTSProvider.calls == before
    assert client.post("/api/tts", json={"request_id": "voice-own", "text": "朗读", "voice": "voice-own"}).status_code == 200
    service.voice_store.records["voice-own"].update(object_key="voice-references/test.wav", reference_filename="旧名称", reference_size=1, reference_duration=5, created_at="2030-01-01T00:00:00Z")
    renamed = client.patch("/api/voice-clones/voice-own", json={"name": "新名称"})
    assert renamed.status_code == 200 and renamed.json()["reference_filename"] == "新名称"
    assert client.patch("/api/voice-clones/voice-own", json={"name": ""}).status_code == 422
    assert client_b.patch("/api/voice-clones/voice-own", json={"name": "越权改名"}).status_code == 404

    # The provider may have created a clone before local persistence fails.
    # Only a confirmed remote delete releases the local slot reservation.
    service.voice_store = FakeVoiceStore(fail_save=True)
    FakeVoiceCloneProvider.delete_calls = 0
    FakeVoiceCloneProvider.delete_always_fail = False
    FakeVoiceCloneProvider.delete_failures_remaining = 2
    response = client.post(
        "/api/voice-clones",
        json={"request_id": "clone-compensation-success", "object_key": "voice-references/user-a/test.wav"},
    )
    assert response.status_code == 502 and response.json()["detail"] == "Voice clone record persistence failed"
    assert FakeVoiceCloneProvider.delete_calls == 3
    assert has_release(store, "clone-compensation-success", "voice_slot")

    FakeVoiceCloneProvider.delete_calls = 0
    FakeVoiceCloneProvider.delete_always_fail = True
    FakeVoiceCloneProvider.delete_failures_remaining = 0
    response = client.post(
        "/api/voice-clones",
        json={"request_id": "clone-compensation-failed", "object_key": "voice-references/user-a/test.wav"},
    )
    assert response.status_code == 502 and response.json()["detail"] == "Voice clone compensation failed"
    assert FakeVoiceCloneProvider.delete_calls == 3
    assert not has_release(store, "clone-compensation-failed", "voice_slot")
    assert store.states[("user-a", "clone-compensation-failed", "voice_slot")] == "reserved"
    FakeVoiceCloneProvider.delete_always_fail = False

    # A remote delete is not reported as success if local deactivation fails.
    service.voice_store = FakeVoiceStore(
        {
            "voice-delete-local-failure": {
                "user_id": "user-a",
                "voice_id": "voice-delete-local-failure",
                "object_key": "voice-references/test.wav",
                "active": True,
            }
        },
        fail_deactivate=True,
    )
    FakeVoiceCloneProvider.delete_calls = 0
    response = client.delete("/api/voice-clones/voice-delete-local-failure")
    assert response.status_code == 502 and response.json()["detail"] == "Voice clone deletion persistence failed"
    assert "deleted_voice_id" not in response.json()
    assert FakeVoiceCloneProvider.delete_calls == 1

    # Slot/import quota rejection prevents both expensive providers from starting.
    store.fail_metric = "voice_slot"
    FakeVoiceCloneProvider.calls = 0
    response = client.post("/api/voice-clones", json={"request_id": "clone-limit", "object_key": "voice-references/user-a/test.wav"})
    assert response.status_code == 402 and FakeVoiceCloneProvider.calls == 0
    store.fail_metric = "chat_import_batch"
    service.chat_import_store = object()
    FakeScreenshotExtractor.calls = 0
    response = client.post(
        "/api/chat-imports",
        json={"request_id": "import-limit", "attachments": [{"object_key": "chat-imports/test.png"}]},
    )
    assert response.status_code == 402 and FakeScreenshotExtractor.calls == 0
    store.fail_metric = None

    # One internal hard account fails closed even while ordinary users remain shadow.
    service.billing_store = None
    service.settings = replace(
        service.settings,
        billing_enforcement_mode="shadow",
        billing_hard_user_ids=frozenset({"user-a"}),
    )
    before = FakeLLMProvider.calls
    response = client.post("/api/chat", json=payload("selective-hard-billing-unavailable"))
    assert response.status_code == 503 and FakeLLMProvider.calls == before
    response = client_b.post("/api/chat", json=payload("ordinary-shadow-without-billing"))
    assert response.status_code == 200 and FakeLLMProvider.calls == before + 1

    print("quota endpoint mock checks passed")


if __name__ == "__main__":
    main()
