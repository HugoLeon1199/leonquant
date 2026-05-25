#!/usr/bin/env python3
"""Fail CI/local runs when DuckDB has no articles in the recent calendar export window."""

from __future__ import annotations

import argparse
import json
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
    parser.add_argument(
        "--check-export",
        type=Path,
        default=None,
        help="Optional news_output_today.json from crawl; print count and fail if both DB and export are low",
    )
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
        total_in_db = int(db.conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0])
    finally:
        db.close()

    n = len(rows)
    export_n: int | None = None
    if args.check_export is not None:
        export_path = args.check_export.resolve()
        if export_path.is_file():
            try:
                payload = json.loads(export_path.read_text(encoding="utf-8"))
                export_n = len(payload.get("articles") or [])
            except (OSError, json.JSONDecodeError, TypeError):
                export_n = 0
            print(f"Export {export_path.name}: {export_n} article(s)")
        else:
            print(f"Export file missing: {export_path}")

    print(
        f"Window [{start.date()} .. {end.date()}) {args.timezone}: "
        f"{n} article(s) (min required: {args.min_articles})"
    )
    print(f"Total rows in articles table: {total_in_db}")
    print(f"Latest extracted_at in DB: {max_ext}")
    ok_db = n >= args.min_articles
    ok_export = export_n is not None and export_n >= args.min_articles
    if ok_db or ok_export:
        if ok_export and not ok_db:
            print(f"PASS via export count ({export_n} >= {args.min_articles}); DB window had {n}")
        return 0
    print(
        "ERROR: export window is empty — crawl did not refresh DuckDB with recent articles.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
