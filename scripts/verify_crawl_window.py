#!/usr/bin/env python3
"""Fail CI/local runs when DuckDB has no articles in the recent calendar export window."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

QUANT_ROOT = Path(__file__).resolve().parents[1]


def resolve_intel_root() -> Path:
    vendored = QUANT_ROOT / "leon_web_intel"
    if (vendored / "src" / "storage" / "db.py").is_file():
        return vendored
    return QUANT_ROOT.parent / "leon_web_intel"


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify DuckDB has articles in export window")
    parser.add_argument("--db", type=Path, default=QUANT_ROOT / "data" / "web_intel_leonquant.duckdb")
    parser.add_argument("--date", default="today")
    parser.add_argument("--timezone", default="Asia/Ho_Chi_Minh")
    parser.add_argument("--recent-calendar-days", type=int, default=2)
    parser.add_argument("--min-articles", type=int, default=1)
    args = parser.parse_args()

    intel = resolve_intel_root()
    sys.path.insert(0, str(intel / "src"))
    from storage.db import WebIntelDB  # noqa: E402
    from utils.today_filter import target_recent_calendar_days_range  # noqa: E402

    db_path = args.db.resolve()
    if not db_path.is_file():
        print(f"ERROR: DuckDB not found: {db_path}", file=sys.stderr)
        return 2

    db = WebIntelDB(db_path)
    try:
        rows = db.fetch_today_articles(
            target_date_str=args.date,
            timezone_name=args.timezone,
            recent_calendar_days=max(1, args.recent_calendar_days),
        )
        start, end = target_recent_calendar_days_range(
            args.date, args.timezone, max(1, args.recent_calendar_days)
        )
        max_ext = db.conn.execute("SELECT MAX(extracted_at) FROM articles").fetchone()[0]
    finally:
        db.close()

    n = len(rows)
    print(
        f"Window [{start.date()} .. {end.date()}) {args.timezone}: "
        f"{n} article(s) (min required: {args.min_articles})"
    )
    print(f"Latest extracted_at in DB: {max_ext}")
    if n < args.min_articles:
        print(
            "ERROR: export window is empty — crawl did not refresh DuckDB with recent articles.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
