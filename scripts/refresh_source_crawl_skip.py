#!/usr/bin/env python3
"""Rebuild uncrawlable-source list in DuckDB + config/sources_uncrawlable.txt."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

QUANT_ROOT = Path(__file__).resolve().parents[1]


def intel_src() -> Path:
    vendored = QUANT_ROOT / "leon_web_intel" / "src"
    if vendored.is_dir():
        return vendored
    raise SystemExit("leon_web_intel/src not found")


def main() -> int:
    p = argparse.ArgumentParser(
        description="Mark sources the current stack cannot crawl (not NotToday-only)."
    )
    p.add_argument(
        "--db",
        type=Path,
        default=QUANT_ROOT / "data" / "web_intel_leonquant.duckdb",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=QUANT_ROOT / "config" / "sources_uncrawlable.txt",
    )
    args = p.parse_args()

    src = intel_src()
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    from crawlability.source_skip import refresh_source_crawl_skip  # noqa: E402
    from settings import load_crawl_rules  # noqa: E402
    from storage.db import WebIntelDB  # noqa: E402

    root = QUANT_ROOT / "leon_web_intel"
    rules = load_crawl_rules(root / "config" / "crawl_rules.yaml")
    db_path = args.db.resolve()
    if not db_path.is_file():
        print(f"ERROR: database not found: {db_path}", file=sys.stderr)
        return 2

    db = WebIntelDB(db_path)
    try:
        stats = refresh_source_crawl_skip(db, rules=rules, export_txt_path=args.output.resolve())
    finally:
        db.close()

    print("===== SOURCE CRAWL SKIP =====")
    print(f"Profiles total:     {stats['profiles_total']}")
    print(f"Skip-listed:        {stats['skip_listed']}")
    print(f"Still crawlable:    {stats['still_crawlable']}")
    print(f"Wrote:              {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
