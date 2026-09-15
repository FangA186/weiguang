#!/usr/bin/env python3
"""Print the production monitoring summary; exit 2 when alerts are active."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.billing_store import BillingStore
from backend.config import Settings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=int, default=24)
    args = parser.parse_args()
    settings = Settings.from_env()
    summary = BillingStore(
        settings.database_url,
        enforcement_mode=settings.billing_enforcement_mode,
        hard_user_ids=settings.billing_hard_user_ids,
    ).get_monitoring_summary(
        hours=args.hours,
        daily_budget_cny=settings.monitor_daily_budget_cny,
        failure_rate_percent=settings.monitor_failure_rate_percent,
        llm_input_cny_per_million=settings.qwen_llm_input_cny_per_million,
        llm_output_cny_per_million=settings.qwen_llm_output_cny_per_million,
        tts_cny_per_10k_characters=settings.qwen_tts_cny_per_10k_characters,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 2 if summary["alerts"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
