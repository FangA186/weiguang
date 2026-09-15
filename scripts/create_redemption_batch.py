#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.billing_store import BillingStore
from backend.config import Settings


def parse_expiry(value: str) -> datetime:
    if "T" not in value:
        return datetime.combine(
            datetime.fromisoformat(value).date(),
            time(23, 59, 59),
            tzinfo=ZoneInfo("Asia/Shanghai"),
        )
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError("timestamp must include a timezone")
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a one-time redemption batch. Raw codes are written only to stdout.",
    )
    parser.add_argument("--product", choices=("plus_30d", "pro_30d"), required=True)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--expires-at", type=parse_expiry, required=True, help="YYYY-MM-DD or ISO timestamp")
    parser.add_argument("--created-by", required=True, help="operator identifier for audit")
    args = parser.parse_args()

    settings = Settings.from_env()
    if not settings.database_url:
        parser.error("DATABASE_URL is required")
    batch, raw_codes = BillingStore(settings.database_url).create_redemption_batch(
        product_code=args.product,
        quantity=args.count,
        expires_at=args.expires_at,
        created_by=args.created_by,
    )
    print(
        f"created batch {batch['batch_code']} ({batch['quantity']} codes); "
        "stdout contains bearer codes and must be handled as sensitive data",
        file=sys.stderr,
    )
    for raw_code in raw_codes:
        print(raw_code)


if __name__ == "__main__":
    main()
