#!/usr/bin/env python3
"""Clear crawl/article tables; keep source_profiles for the next Scrapy-only run."""

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
    parser = argparse.ArgumentParser(description="Clear articles/crawl tables; keep source_profiles")
    parser.add_argument("--db", type=Path, default=QUANT_ROOT / "data" / "web_intel_leonquant.duckdb")
    args = parser.parse_args()

    intel = resolve_intel_root()
    sys.path.insert(0, str(intel / "src"))
    from storage.db import WebIntelDB  # noqa: E402

    db_path = args.db.resolve()
    if not db_path.is_file():
        print(f"No DuckDB at {db_path} — nothing to clear (first run will profile + crawl).")
        return 0

    db = WebIntelDB(db_path)
    try:
        stats = db.clear_crawl_article_data()
    finally:
        db.close()

    removed = {k: v for k, v in stats.items() if k != "source_profiles_kept"}
    print("Cleared crawl tables (rows removed):", ", ".join(f"{k}={v}" for k, v in sorted(removed.items())))
    print(f"Kept source_profiles: {stats.get('source_profiles_kept', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
