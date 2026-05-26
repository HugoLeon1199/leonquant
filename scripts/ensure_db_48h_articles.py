#!/usr/bin/env python3
"""Re-seed DuckDB from bundled .gz when the 48h export window has too few articles (CI cache drift)."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

QUANT_ROOT = Path(__file__).resolve().parents[1]


def intel_root() -> Path:
    vendored = QUANT_ROOT / "leon_web_intel"
    if (vendored / "src" / "storage" / "db.py").is_file():
        return vendored
    return QUANT_ROOT.parent / "leon_web_intel"


def count_window_articles(db_path: Path, *, date: str, timezone: str, days: int) -> int:
    root = intel_root()
    sys.path.insert(0, str(root / "src"))
    from storage.db import WebIntelDB  # noqa: E402

    db = WebIntelDB(db_path)
    try:
        rows = db.fetch_today_articles(
            target_date_str=date,
            timezone_name=timezone,
            recent_calendar_days=days,
        )
    finally:
        db.close()
    return len(rows)


def reseed_from_gz(db_path: Path, gz_path: Path) -> None:
    if not gz_path.is_file():
        print(f"ERROR: seed not found: {gz_path}", file=sys.stderr)
        raise SystemExit(2)
    import gzip

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.is_file():
        db_path.unlink()
    with gzip.open(gz_path, "rb") as fin, open(db_path, "wb") as fout:
        shutil.copyfileobj(fin, fout)
    print(f"Re-seeded {db_path} from {gz_path} ({db_path.stat().st_size // 1024 // 1024} MB)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=QUANT_ROOT / "data" / "web_intel_leonquant.duckdb")
    parser.add_argument("--gz", type=Path, default=QUANT_ROOT / "data" / "web_intel_leonquant.duckdb.gz")
    parser.add_argument("--date", default="today")
    parser.add_argument("--timezone", default="Asia/Ho_Chi_Minh")
    parser.add_argument("--recent-calendar-days", type=int, default=2)
    parser.add_argument("--min", type=int, default=5, dest="min_articles")
    args = parser.parse_args()

    import subprocess

    pin = subprocess.check_output(
        [
            sys.executable,
            str(QUANT_ROOT / "scripts" / "pin_crawl_calendar_date.py"),
            "--date",
            args.date,
            "--timezone",
            args.timezone,
        ],
        text=True,
    ).strip()

    db = args.db.resolve()
    if not db.is_file():
        reseed_from_gz(db, args.gz.resolve())
    n = count_window_articles(db, date=pin, timezone=args.timezone, days=args.recent_calendar_days)
    print(f"articles_in_48h_window={n} (min={args.min_articles}, date={pin})")
    if n < args.min_articles:
        reseed_from_gz(db, args.gz.resolve())
        n = count_window_articles(db, date=pin, timezone=args.timezone, days=args.recent_calendar_days)
        print(f"after_reseed articles_in_48h_window={n}")
    if n < args.min_articles:
        print("ERROR: still below minimum after re-seed", file=sys.stderr)
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
