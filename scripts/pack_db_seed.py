#!/usr/bin/env python3
"""Build small data/web_intel_leonquant.duckdb.gz for git (profiles + optional recent articles)."""

from __future__ import annotations

import argparse
import gzip
import shutil
import sys
import tempfile
from pathlib import Path

QUANT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = QUANT_ROOT / "data" / "web_intel_leonquant.duckdb"
DEFAULT_GZ = QUANT_ROOT / "data" / "web_intel_leonquant.duckdb.gz"


def intel_root() -> Path:
    vendored = QUANT_ROOT / "leon_web_intel"
    if (vendored / "src" / "storage" / "db.py").is_file():
        return vendored
    return QUANT_ROOT.parent / "leon_web_intel"


def main() -> int:
    parser = argparse.ArgumentParser(description="Pack DuckDB seed for git (gzip only)")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output", type=Path, default=DEFAULT_GZ)
    parser.add_argument(
        "--mode",
        choices=("profiles-only", "trim"),
        default="profiles-only",
        help="profiles-only = smallest git seed (~profiles, no stale articles)",
    )
    parser.add_argument("--keep-calendar-days", type=int, default=3)
    parser.add_argument("--date", default="today")
    parser.add_argument("--timezone", default="Asia/Ho_Chi_Minh")
    args = parser.parse_args()

    src = args.db.resolve()
    if not src.is_file():
        print(f"ERROR: source DB not found: {src}", file=sys.stderr)
        return 2

    root = intel_root()
    sys.path.insert(0, str(root / "src"))
    from storage.db import WebIntelDB  # noqa: E402

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "seed.duckdb"
        shutil.copy2(src, work)
        db = WebIntelDB(work)
        try:
            if args.mode == "profiles-only":
                stats = db.clear_crawl_article_data()
                print(f"Cleared crawl tables: {stats}")
            else:
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
                stats = db.prune_stale_intel_data(
                    target_date_str=pin,
                    timezone_name=args.timezone,
                    recent_calendar_days=max(1, args.keep_calendar_days),
                )
                print(f"Pruned to {args.keep_calendar_days}d: {stats}")
        finally:
            db.close()

        out = args.output.resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(work, "rb") as fin, gzip.open(out, "wb", compresslevel=9) as fout:
            shutil.copyfileobj(fin, fout)

    raw_mb = work.stat().st_size / 1024 / 1024
    gz_mb = out.stat().st_size / 1024 / 1024
    print(f"Wrote {out} ({gz_mb:.1f} MB gzip, {raw_mb:.1f} MB raw, mode={args.mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
