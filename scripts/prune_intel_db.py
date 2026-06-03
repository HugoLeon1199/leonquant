#!/usr/bin/env python3
"""Drop articles outside the recent export window so DuckDB stays small (CI cache only)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

QUANT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = QUANT_ROOT / "scripts"
DEFAULT_WINDOW_STATE = QUANT_ROOT / "data" / "digest_export_window.json"


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
    parser.add_argument(
        "--recent-calendar-days",
        type=int,
        default=0,
        help="Fallback when no window state (0 = read state file or 3)",
    )
    parser.add_argument(
        "--window-state",
        type=Path,
        default=DEFAULT_WINDOW_STATE,
        help="Use same window as export (never prune tighter than digest used)",
    )
    args = parser.parse_args()

    sys.path.insert(0, str(SCRIPTS))
    from digest_window import load_window_state, prune_calendar_days_from_state  # noqa: E402

    prune_days = args.recent_calendar_days
    pin_date = args.date
    tz = args.timezone
    state = load_window_state(args.window_state)
    if state:
        prune_days = prune_calendar_days_from_state(state)
        pin_date = str(state.get("end_date") or pin_date)
        tz = str(state.get("timezone") or tz)
        print(f"Prune from window state: {prune_days} calendar day(s), date={pin_date}")
    elif prune_days <= 0:
        prune_days = 3

    intel = resolve_intel_root()
    sys.path.insert(0, str(intel / "src"))
    from storage.db import WebIntelDB  # noqa: E402

    db_path = args.db.resolve()
    if not db_path.is_file():
        print(f"ERROR: DuckDB not found: {db_path}", file=sys.stderr)
        return 2

    if str(pin_date).strip().lower() == "today":
        import subprocess

        pin_date = subprocess.check_output(
            [
                sys.executable,
                str(SCRIPTS / "pin_crawl_calendar_date.py"),
                "--date",
                "today",
                "--timezone",
                tz,
            ],
            text=True,
        ).strip()

    db = WebIntelDB(db_path)
    try:
        stats = db.prune_stale_intel_data(
            target_date_str=pin_date,
            timezone_name=tz,
            recent_calendar_days=max(1, prune_days),
        )
    finally:
        db.close()

    mb = db_path.stat().st_size / 1024 / 1024
    print(
        f"Pruned articles {stats['articles_before']} -> {stats['articles_after']} "
        f"(removed {stats['articles_removed']}, kept {stats['keep_articles']})"
    )
    if stats["keep_articles"] == 0 and stats["articles_before"] > 0:
        print("WARN: prune kept 0 articles in calendar window — table left intact (safety)")
    print(
        f"Trimmed crawl_errors -{stats['crawl_errors_removed']}, "
        f"discovered_urls -{stats['discovered_urls_removed']}"
    )
    print(f"DuckDB size after VACUUM: {mb:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
