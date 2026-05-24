#!/usr/bin/env python3
"""Drop articles outside the 48h export window so DuckDB stays small (CI cache only)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

QUANT_ROOT = Path(__file__).resolve().parents[1]


def resolve_intel_root() -> Path:
    env = os.environ.get("LEON_WEB_INTEL_ROOT")
    if env:
        return Path(env).resolve()
    vendored = QUANT_ROOT / "leon_web_intel"
    if (vendored / "src" / "storage" / "db.py").is_file():
        return vendored
    return QUANT_ROOT.parent / "leon_web_intel"


def main() -> int:
    parser = argparse.ArgumentParser(description="Prune DuckDB to recent calendar window only")
    parser.add_argument("--db", type=Path, default=QUANT_ROOT / "data" / "web_intel_leonquant.duckdb")
    parser.add_argument("--date", default="today")
    parser.add_argument("--timezone", default="Asia/Ho_Chi_Minh")
    parser.add_argument("--recent-calendar-days", type=int, default=2)
    args = parser.parse_args()

    intel = resolve_intel_root()
    sys.path.insert(0, str(intel / "src"))
    from storage.db import WebIntelDB  # noqa: E402

    db_path = args.db.resolve()
    if not db_path.is_file():
        print(f"ERROR: DuckDB not found: {db_path}", file=sys.stderr)
        return 2

    db = WebIntelDB(db_path)
    try:
        stats = db.prune_stale_intel_data(
            target_date_str=args.date,
            timezone_name=args.timezone,
            recent_calendar_days=max(1, args.recent_calendar_days),
        )
    finally:
        db.close()

    mb = db_path.stat().st_size / 1024 / 1024
    print(
        f"Pruned articles {stats['articles_before']} -> {stats['articles_after']} "
        f"(removed {stats['articles_removed']}, kept {stats['keep_articles']})"
    )
    print(
        f"Trimmed crawl_errors -{stats['crawl_errors_removed']}, "
        f"discovered_urls -{stats['discovered_urls_removed']}"
    )
    print(f"DuckDB size after VACUUM: {mb:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
