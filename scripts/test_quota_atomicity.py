"""Real PostgreSQL regression checks for BillingStore's hard-quota invariants.

The script refuses a non-loopback database unless explicitly opted in.  All
records use one generated prefix and are deleted in ``finally`` so it is safe
to run repeatedly against the local development database.
"""

from __future__ import annotations

import os
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Barrier
from urllib.parse import urlparse

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.billing_store import (  # noqa: E402
    BillingStore,
    QuotaExceededError,
    RedemptionError,
    UsageRequestConflictError,
    hash_redemption_code,
)


def _database_url() -> str:
    load_dotenv(REPO_ROOT / ".env")
    url = os.getenv("QUOTA_TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("set QUOTA_TEST_DATABASE_URL (or local DATABASE_URL) before running this test")
    host = urlparse(url).hostname
    if host not in {"localhost", "127.0.0.1", "::1"} and os.getenv("ALLOW_NONLOCAL_QUOTA_TEST_DATABASE") != "1":
        raise RuntimeError("refusing non-local database; set ALLOW_NONLOCAL_QUOTA_TEST_DATABASE=1 only intentionally")
    return url


def _set_subscription(
    store: BillingStore,
    user_id: str,
    *,
    plan_code: str = "free",
    start: datetime | None = None,
    end: datetime | None = None,
    access_end: datetime | None = None,
) -> None:
    start = start or datetime.now(timezone.utc)
    end = end or start + timedelta(days=30)
    access_end = access_end or end
    with store._connect() as connection:  # test-only direct fixture setup
        connection.execute(
            """
            INSERT INTO user_subscriptions (user_id, plan_code, status, period_start, period_end, access_end)
            VALUES (%s, %s, 'active', %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE
            SET plan_code = EXCLUDED.plan_code, status = 'active', period_start = EXCLUDED.period_start,
                period_end = EXCLUDED.period_end, access_end = EXCLUDED.access_end, updated_at = NOW()
            """,
            (user_id, plan_code, start, end, access_end),
        )


def _event_count(store: BillingStore, user_id: str, request_id: str) -> int:
    with store._connect() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM usage_events WHERE user_id = %s AND request_id = %s",
            (user_id, request_id),
        ).fetchone()
    return int(row["count"])


def _event_status(store: BillingStore, user_id: str, request_id: str) -> str:
    with store._connect() as connection:
        row = connection.execute(
            "SELECT status FROM usage_events WHERE user_id = %s AND request_id = %s",
            (user_id, request_id),
        ).fetchone()
    if not row:
        raise AssertionError("expected usage event was not found")
    return str(row["status"])


def _event(store: BillingStore, user_id: str, request_id: str) -> dict[str, object]:
    with store._connect() as connection:
        row = connection.execute(
            """
            SELECT status, quantity::double precision AS quantity, raw_usage
            FROM usage_events WHERE user_id = %s AND request_id = %s
            """,
            (user_id, request_id),
        ).fetchone()
    if not row:
        raise AssertionError("expected usage event was not found")
    return dict(row)


def _cleanup(store: BillingStore, prefix: str) -> None:
    with store._connect() as connection:
        connection.execute("DELETE FROM usage_events WHERE user_id LIKE %s", (f"{prefix}%",))
        connection.execute("DELETE FROM subscription_grants WHERE user_id LIKE %s", (f"{prefix}%",))
        connection.execute(
            """
            DELETE FROM redemption_codes
            WHERE redeemed_by_user_id LIKE %s
               OR batch_id IN (SELECT id FROM redemption_batches WHERE created_by = %s)
            """,
            (f"{prefix}%", prefix),
        )
        connection.execute("DELETE FROM redemption_batches WHERE created_by = %s", (prefix,))
        connection.execute("DELETE FROM user_subscriptions WHERE user_id LIKE %s", (f"{prefix}%",))


def _prefix_counts(store: BillingStore, prefix: str) -> dict[str, int]:
    with store._connect() as connection:
        row = connection.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM usage_events WHERE user_id LIKE %s) AS events,
                (SELECT COUNT(*) FROM user_subscriptions WHERE user_id LIKE %s) AS subscriptions,
                (SELECT COUNT(*) FROM subscription_grants WHERE user_id LIKE %s) AS grants,
                (SELECT COUNT(*) FROM redemption_batches WHERE created_by = %s) AS batches,
                (
                    SELECT COUNT(*)
                    FROM redemption_codes AS codes
                    WHERE codes.redeemed_by_user_id LIKE %s
                       OR codes.batch_id IN (
                           SELECT id FROM redemption_batches WHERE created_by = %s
                       )
                ) AS codes
            """,
            (f"{prefix}%", f"{prefix}%", f"{prefix}%", prefix, f"{prefix}%", prefix),
        ).fetchone()
    return {key: int(row[key]) for key in ("events", "subscriptions", "grants", "batches", "codes")}


def _assert_concurrent_limit(store: BillingStore, prefix: str) -> None:
    user_id = f"{prefix}-concurrent"
    _set_subscription(store, user_id)
    barrier = Barrier(100)

    def reserve(index: int) -> str:
        barrier.wait(timeout=30)
        try:
            result = store.reserve_usage(user_id, f"{prefix}-concurrent-{index}", {"ai_reply": 1})
            assert result["proceed"] is True
            return "reserved"
        except QuotaExceededError:
            return "quota_exceeded"

    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(reserve, index) for index in range(100)]
        outcomes = [future.result(timeout=60) for future in as_completed(futures)]
    assert outcomes.count("reserved") == 50, outcomes
    assert outcomes.count("quota_exceeded") == 50, outcomes
    summary = store.get_billing_summary(user_id)
    assert summary["metrics"]["ai_reply"] == {"used": 0, "reserved": 50, "limit": 50, "remaining": 0}


def _assert_retry_idempotency(store: BillingStore, prefix: str) -> None:
    user_id = f"{prefix}-retry"
    request_id = f"{prefix}-same-request"
    _set_subscription(store, user_id)
    barrier = Barrier(100)

    def reserve_once() -> dict[str, object]:
        barrier.wait(timeout=30)
        return store.reserve_usage(user_id, request_id, {"ai_reply": 1})

    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(reserve_once) for _ in range(100)]
        results = [future.result(timeout=60) for future in as_completed(futures)]
    assert sum(bool(result["proceed"]) for result in results) == 1
    assert sum(result["state"] == "request_in_progress" for result in results) == 99
    assert _event_count(store, user_id, request_id) == 1


def _assert_release_and_ttl(store: BillingStore, prefix: str) -> None:
    user_id = f"{prefix}-release"
    _set_subscription(store, user_id)
    request_id = f"{prefix}-release-request"
    first = store.reserve_usage(user_id, request_id, {"ai_reply": 1})
    assert first["proceed"] is True
    released = store.release_usage(user_id, request_id, ["ai_reply"])
    assert released["metrics"]["ai_reply"]["status"] == "released"
    assert store.get_billing_summary(user_id)["metrics"]["ai_reply"]["reserved"] == 0
    retry = store.reserve_usage(user_id, request_id, {"ai_reply": 1})
    assert retry["proceed"] is True and retry["state"] == "reserved"

    ttl_request_id = f"{prefix}-ttl-request"
    at = datetime.now(timezone.utc)
    store.reserve_usage(user_id, ttl_request_id, {"image": 1}, ttl=timedelta(seconds=1), now=at)
    store.get_billing_summary(user_id, now=at + timedelta(seconds=2))
    assert _event_status(store, user_id, ttl_request_id) == "expired"
    retry = store.reserve_usage(user_id, ttl_request_id, {"image": 1}, now=at + timedelta(seconds=2))
    assert retry["proceed"] is False and retry["state"] == "request_expired"


def _assert_late_confirmation_keeps_cost(store: BillingStore, prefix: str) -> None:
    """A late Provider result wins over its own TTL, while other orphans expire."""
    user_id = f"{prefix}-late-confirm"
    target_id = f"{prefix}-late-target"
    other_id = f"{prefix}-late-other"
    at = datetime.now(timezone.utc)
    _set_subscription(store, user_id, start=at, end=at + timedelta(days=30))
    store.reserve_usage(user_id, target_id, {"ai_voice_seconds": 1}, ttl=timedelta(seconds=1), now=at)
    store.reserve_usage(user_id, other_id, {"image": 1}, ttl=timedelta(seconds=1), now=at)
    confirmed = store.confirm_usage(
        user_id,
        target_id,
        "ai_voice_seconds",
        actual_quantity=2,
        raw_usage={"provider_actual": 2},
        now=at + timedelta(seconds=2),
    )
    assert confirmed["metrics"]["ai_voice_seconds"]["status"] == "completed"
    target = _event(store, user_id, target_id)
    assert target == {"status": "completed", "quantity": 2.0, "raw_usage": {"provider_actual": 2}}
    assert _event_status(store, user_id, other_id) == "expired"


def _assert_expired_retry_late_confirm_race(store: BillingStore, prefix: str) -> None:
    """No same-id retry is re-authorized while a late Provider completion races it."""
    user_id = f"{prefix}-expiry-race"
    request_id = f"{prefix}-expiry-race-request"
    at = datetime.now(timezone.utc)
    _set_subscription(store, user_id, start=at, end=at + timedelta(days=30))
    store.reserve_usage(user_id, request_id, {"ai_reply": 1}, ttl=timedelta(seconds=1), now=at)
    late = at + timedelta(seconds=2)
    retries = 20
    barrier = Barrier(retries + 1)

    def retry() -> tuple[str, dict[str, object]]:
        barrier.wait(timeout=30)
        return "retry", store.reserve_usage(user_id, request_id, {"ai_reply": 1}, now=late)

    def confirm() -> tuple[str, dict[str, object]]:
        barrier.wait(timeout=30)
        return "confirm", store.confirm_usage(
            user_id, request_id, "ai_reply", actual_quantity=2,
            raw_usage={"provider_actual": 2}, now=late,
        )

    with ThreadPoolExecutor(max_workers=retries + 1) as executor:
        futures = [executor.submit(retry) for _ in range(retries)]
        futures.append(executor.submit(confirm))
        results = [future.result(timeout=60) for future in as_completed(futures)]
    retry_results = [result for kind, result in results if kind == "retry"]
    assert len(retry_results) == retries
    assert all(result["proceed"] is False for result in retry_results), retry_results
    event = _event(store, user_id, request_id)
    assert event == {"status": "completed", "quantity": 2.0, "raw_usage": {"provider_actual": 2}}


def _assert_period_switch(store: BillingStore, prefix: str) -> None:
    user_id = f"{prefix}-renewal"
    batch, codes = store.create_redemption_batch(
        product_code="plus_30d",
        quantity=2,
        expires_at=datetime.now(timezone.utc) + timedelta(days=3),
        created_by=prefix,
    )
    assert batch["quantity"] == 2
    first_grant = store.redeem_code(user_id=user_id, code=codes[0])
    before_renew = store.get_billing_summary(user_id)
    old_end = before_renew["period_end"]
    store.reserve_usage(user_id, f"{prefix}-old-cycle", {"ai_reply": 1})
    store.confirm_usage(user_id, f"{prefix}-old-cycle", "ai_reply", actual_quantity=1)

    second_grant = store.redeem_code(user_id=user_id, code=codes[1])
    after_renew = store.get_billing_summary(user_id)
    assert after_renew["period_end"] == old_end
    assert after_renew["access_ends_at"] == second_grant["period_end"].isoformat()
    assert after_renew["metrics"]["ai_reply"]["used"] == 1

    switched = store.get_billing_summary(user_id, now=second_grant["period_start"] + timedelta(seconds=1))
    assert switched["plan_code"] == "plus"
    assert switched["period_start"] == second_grant["period_start"].isoformat()
    assert switched["metrics"]["ai_reply"]["used"] == 0
    assert first_grant["period_end"] == second_grant["period_start"]


def _assert_free_trial_once(store: BillingStore, prefix: str) -> None:
    """A free trial expires once, blocks shadow traffic, and never returns after paid access."""
    user_id = f"{prefix}-one-time-trial"
    started = datetime.now(timezone.utc)
    initial = store.get_billing_summary(user_id, now=started)
    assert initial["plan_code"] == "free" and initial["status"] == "active"
    assert initial["metrics"]["ai_reply"]["limit"] == 50
    assert datetime.fromisoformat(initial["period_end"]) - started == timedelta(days=7)

    expired_at = started + timedelta(days=8)
    expired = store.get_billing_summary(user_id, now=expired_at)
    assert expired["status"] == "expired"
    assert all(metric["limit"] == 0 and metric["remaining"] == 0 for metric in expired["metrics"].values())
    repeated = store.get_billing_summary(user_id, now=expired_at + timedelta(days=8))
    assert repeated["period_start"] == initial["period_start"]
    assert repeated["period_end"] == initial["period_end"]
    assert repeated["free_trial_started_at"] == initial["free_trial_started_at"]

    shadow = BillingStore(store.database_url, enforcement_mode="shadow")
    try:
        shadow.reserve_usage(user_id, f"{prefix}-expired-shadow", {"ai_reply": 1}, now=expired_at)
    except QuotaExceededError as exc:
        assert exc.limit == 0 and exc.remaining == 0
    else:
        raise AssertionError("an expired one-time trial must block Provider calls even in shadow mode")

    _, codes = store.create_redemption_batch(
        product_code="plus_30d",
        quantity=1,
        expires_at=datetime.now(timezone.utc) + timedelta(days=3),
        created_by=prefix,
    )
    grant = store.redeem_code(user_id=user_id, code=codes[0])
    paid = store.get_billing_summary(user_id)
    assert paid["status"] == "active" and paid["plan_code"] == "plus"
    after_paid = store.get_billing_summary(user_id, now=grant["period_end"] + timedelta(seconds=1))
    assert after_paid["status"] == "expired"
    assert after_paid["metrics"]["ai_reply"]["limit"] == 0


def _assert_monitoring_summary(store: BillingStore, prefix: str) -> None:
    user_id = f"{prefix}-monitoring"
    _set_subscription(store, user_id)
    before = store.get_monitoring_summary(hours=24, daily_budget_cny=1)
    store.record_usage_event(
        user_id=user_id,
        request_id=f"{prefix}-monitor-llm",
        metric="ai_reply",
        provider="bailian",
        model="qwen3.5-flash",
        raw_usage={
            "usage": {"prompt_tokens": 1_000_000, "completion_tokens": 100_000},
            "requested_max_completion_tokens": 512,
            "input_bytes": 48_000,
            "context_trimmed_messages": 2,
            "finish_reason": "length",
        },
    )
    store.record_usage_event(
        user_id=user_id,
        request_id=f"{prefix}-monitor-tts",
        metric="ai_voice_seconds",
        quantity=5,
        provider="bailian",
        model="qwen-audio-3.0-tts-flash",
        raw_usage={"usage_characters": 10_000},
    )
    store.record_usage_event(
        user_id=user_id,
        request_id=f"{prefix}-monitor-missing",
        metric="ai_voice_seconds",
        quantity=1,
        provider="bailian",
        model="qwen-audio-3.0-tts-flash",
    )
    summary = store.get_monitoring_summary(hours=24, daily_budget_cny=1)
    assert round(summary["cost"]["estimated_cny"] - before["cost"]["estimated_cny"], 6) == 1.4
    assert summary["cost"]["partial"] is True
    assert summary["provider_usage"]["llm_prompt_tokens"] - before["provider_usage"]["llm_prompt_tokens"] == 1_000_000
    assert summary["provider_usage"]["llm_limited_requests"] >= 1
    assert summary["provider_usage"]["context_trimmed_messages"] >= 2
    assert summary["provider_usage"]["llm_prompt_tokens_p95"] > 0
    assert summary["provider_usage"]["llm_completion_tokens_p95"] > 0
    assert summary["provider_usage"]["llm_length_finish_rate_percent"] > 0
    costs = store.get_admin_costs_summary(hours=24)
    assert costs["totals"]["llm_limited_requests"] >= 1
    assert costs["totals"]["context_trimmed_messages"] >= 2
    assert any(plan["requests"] > 0 for plan in costs["plans"])
    codes = {alert["code"] for alert in summary["alerts"]}
    assert {"cost_budget_exceeded", "cost_telemetry_missing"} <= codes


def _assert_cross_user_isolation(store: BillingStore, prefix: str) -> None:
    user_a = f"{prefix}-user-a"
    user_b = f"{prefix}-user-b"
    request_id = f"{prefix}-cross-user"
    _set_subscription(store, user_a)
    _set_subscription(store, user_b)
    store.reserve_usage(user_a, request_id, {"ai_reply": 1})
    try:
        store.reserve_usage(user_b, request_id, {"image": 1})
    except UsageRequestConflictError:
        pass
    else:
        raise AssertionError("a request id cannot be reused by another user")
    summary_b = store.get_billing_summary(user_b)
    assert summary_b["metrics"]["ai_reply"]["used"] == 0
    assert summary_b["metrics"]["image"]["reserved"] == 0


def _assert_limit_sequence(store: BillingStore, prefix: str) -> None:
    """Exercise limit-1, limit, and limit+1 without relying on concurrency."""
    user_id = f"{prefix}-limit-sequence"
    _set_subscription(store, user_id)
    store.reserve_usage(user_id, f"{prefix}-limit-1", {"ai_reply": 49})
    store.confirm_usage(user_id, f"{prefix}-limit-1", "ai_reply", actual_quantity=49)
    assert store.get_billing_summary(user_id)["metrics"]["ai_reply"] == {
        "used": 49,
        "reserved": 0,
        "limit": 50,
        "remaining": 1,
    }
    store.reserve_usage(user_id, f"{prefix}-limit", {"ai_reply": 1})
    store.confirm_usage(user_id, f"{prefix}-limit", "ai_reply", actual_quantity=1)
    assert store.get_billing_summary(user_id)["metrics"]["ai_reply"] == {
        "used": 50,
        "reserved": 0,
        "limit": 50,
        "remaining": 0,
    }
    try:
        store.reserve_usage(user_id, f"{prefix}-limit-plus-1", {"ai_reply": 1})
    except QuotaExceededError as exc:
        assert exc.to_detail()["remaining"] == 0
    else:
        raise AssertionError("limit+1 must be rejected before the provider call")
    assert _event_count(store, user_id, f"{prefix}-limit-plus-1") == 0


def _assert_confirm_records_actual_overage(store: BillingStore, prefix: str) -> None:
    """Provider completion must remain auditable even if its estimate was low."""
    user_id = f"{prefix}-actual-overage"
    _set_subscription(store, user_id)
    store.reserve_usage(user_id, f"{prefix}-overage-base", {"ai_reply": 49})
    store.confirm_usage(user_id, f"{prefix}-overage-base", "ai_reply", actual_quantity=49)
    store.reserve_usage(user_id, f"{prefix}-overage-actual", {"ai_reply": 1})
    confirmed = store.confirm_usage(
        user_id,
        f"{prefix}-overage-actual",
        "ai_reply",
        actual_quantity=2,
        raw_usage={"provider_actual": 2},
    )
    assert confirmed["metrics"]["ai_reply"]["status"] == "completed"
    assert confirmed["metrics"]["ai_reply"]["quantity"] == 2
    assert store.get_billing_summary(user_id)["metrics"]["ai_reply"] == {
        "used": 51,
        "reserved": 0,
        "limit": 50,
        "remaining": 0,
    }


def _assert_boundary_switch_concurrency(store: BillingStore, prefix: str) -> None:
    """One queued grant is selected once even when 100 requests hit its boundary."""
    user_id = f"{prefix}-boundary"
    _, codes = store.create_redemption_batch(
        product_code="plus_30d",
        quantity=2,
        expires_at=datetime.now(timezone.utc) + timedelta(days=3),
        created_by=prefix,
    )
    store.redeem_code(user_id=user_id, code=codes[0])
    queued = store.redeem_code(user_id=user_id, code=codes[1])
    boundary = queued["period_start"] + timedelta(microseconds=1)
    barrier = Barrier(100)

    def switch_once() -> tuple[str, str]:
        barrier.wait(timeout=30)
        cycle = store.ensure_current_cycle(user_id, now=boundary)
        return cycle["period_start"].isoformat(), cycle["period_end"].isoformat()

    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(switch_once) for _ in range(100)]
        cycles = [future.result(timeout=60) for future in as_completed(futures)]
    assert set(cycles) == {(queued["period_start"].isoformat(), queued["period_end"].isoformat())}
    with store._connect() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM subscription_grants WHERE user_id = %s", (user_id,)
        ).fetchone()
    assert int(row["count"]) == 2


def _assert_redemption_code_concurrency(store: BillingStore, prefix: str) -> None:
    """The same code cannot authorize both of two users under 100 concurrent attempts."""
    _, codes = store.create_redemption_batch(
        product_code="plus_30d",
        quantity=1,
        expires_at=datetime.now(timezone.utc) + timedelta(days=3),
        created_by=prefix,
    )
    code = codes[0]
    users = (f"{prefix}-card-user-a", f"{prefix}-card-user-b")
    barrier = Barrier(100)

    def redeem(index: int) -> tuple[str, str]:
        user_id = users[index % 2]
        barrier.wait(timeout=30)
        try:
            store.redeem_code(user_id=user_id, code=code)
            return "redeemed", user_id
        except RedemptionError as exc:
            assert str(exc) == "兑换码无效或不可用"
            return "invalid", user_id

    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(redeem, index) for index in range(100)]
        outcomes = [future.result(timeout=60) for future in as_completed(futures)]
    winners = [user_id for status, user_id in outcomes if status == "redeemed"]
    assert len(winners) == 1, outcomes
    assert sum(status == "invalid" for status, _ in outcomes) == 99
    losing_user = users[1] if winners[0] == users[0] else users[0]
    with store._connect() as connection:
        grants = connection.execute(
            "SELECT user_id, COUNT(*) AS count FROM subscription_grants WHERE user_id = ANY(%s) GROUP BY user_id",
            (list(users),),
        ).fetchall()
        redemption = connection.execute(
            "SELECT status, redeemed_by_user_id FROM redemption_codes WHERE code_hash = %s",
            (hash_redemption_code(code),),
        ).fetchone()
    grant_counts = {row["user_id"]: int(row["count"]) for row in grants}
    assert grant_counts == {winners[0]: 1}
    assert redemption["status"] == "redeemed" and redemption["redeemed_by_user_id"] == winners[0]
    assert losing_user not in grant_counts


def _assert_selective_hard_mode(store: BillingStore, prefix: str) -> None:
    """One internal account is hard while ordinary users remain shadow."""
    hard_user = f"{prefix}-selective-hard"
    shadow_user = f"{prefix}-selective-shadow"
    selective = BillingStore(
        store.database_url,
        enforcement_mode="shadow",
        hard_user_ids={hard_user},
    )
    for user_id in (hard_user, shadow_user):
        _set_subscription(selective, user_id)
        selective.record_usage_event(
            user_id=user_id,
            request_id=f"{user_id}-used",
            metric="ai_reply",
            quantity=50,
        )
    assert selective.get_billing_summary(hard_user)["enforcement_mode"] == "hard"
    assert selective.get_billing_summary(shadow_user)["enforcement_mode"] == "shadow"
    try:
        selective.reserve_usage(hard_user, f"{hard_user}-blocked", {"ai_reply": 1})
    except QuotaExceededError:
        pass
    else:
        raise AssertionError("selective hard user must be blocked at the limit")
    assert selective.reserve_usage(
        shadow_user,
        f"{shadow_user}-allowed",
        {"ai_reply": 1},
    )["proceed"] is True


def main() -> None:
    prefix = f"quota-test-{uuid.uuid4().hex}"
    store = BillingStore(_database_url(), enforcement_mode="hard")
    try:
        _assert_concurrent_limit(store, prefix)
        _assert_retry_idempotency(store, prefix)
        _assert_release_and_ttl(store, prefix)
        _assert_late_confirmation_keeps_cost(store, prefix)
        _assert_expired_retry_late_confirm_race(store, prefix)
        _assert_limit_sequence(store, prefix)
        _assert_confirm_records_actual_overage(store, prefix)
        _assert_period_switch(store, prefix)
        _assert_free_trial_once(store, prefix)
        _assert_monitoring_summary(store, prefix)
        _assert_boundary_switch_concurrency(store, prefix)
        _assert_cross_user_isolation(store, prefix)
        _assert_redemption_code_concurrency(store, prefix)
        _assert_selective_hard_mode(store, prefix)
    finally:
        _cleanup(store, prefix)
        cleanup_counts = _prefix_counts(store, prefix)
        assert cleanup_counts == {
            "events": 0,
            "subscriptions": 0,
            "grants": 0,
            "batches": 0,
            "codes": 0,
        }, cleanup_counts
    print("quota atomicity checks passed")


if __name__ == "__main__":
    main()
