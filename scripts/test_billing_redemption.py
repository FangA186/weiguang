#!/usr/bin/env python3
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.billing_store import (
    RedemptionError,
    calculate_redemption_period,
    generate_redemption_code,
    hash_redemption_code,
    normalize_redemption_code,
)
from backend.config import _ldxp_product_url


def main() -> None:
    assert _ldxp_product_url("https://pay.ldxp.cn/item/example") == "https://pay.ldxp.cn/item/example"
    assert _ldxp_product_url("http://pay.ldxp.cn/item/example") == ""
    assert _ldxp_product_url("https://ldxp.cn.example.com/item/example") == ""

    codes = {generate_redemption_code() for _ in range(512)}
    assert len(codes) == 512
    for code in codes:
        normalized = normalize_redemption_code(code)
        assert normalized.startswith("WG") and len(normalized) == 34
        assert hash_redemption_code(code) == hash_redemption_code(normalized.lower())

    now = datetime.now(timezone.utc)
    start, grant_start, end = calculate_redemption_period(
        current_plan="free",
        current_status="active",
        current_start=now - timedelta(days=1),
        current_end=now + timedelta(days=29),
        redeemed_plan="plus",
        now=now,
    )
    assert start == grant_start == now
    assert end == now + timedelta(days=30)

    paid_start = now - timedelta(days=10)
    paid_end = now + timedelta(days=20)
    start, grant_start, end = calculate_redemption_period(
        current_plan="plus",
        current_status="active",
        current_start=paid_start,
        current_end=paid_end,
        redeemed_plan="plus",
        now=now,
    )
    assert start == paid_start and grant_start == paid_end and end == paid_end + timedelta(days=30)

    try:
        calculate_redemption_period(
            current_plan="plus",
            current_status="active",
            current_start=paid_start,
            current_end=paid_end,
            redeemed_plan="pro",
            now=now,
        )
    except RedemptionError:
        pass
    else:
        raise AssertionError("active cross-plan redemption must be rejected")

    print("billing redemption checks passed")


if __name__ == "__main__":
    main()
