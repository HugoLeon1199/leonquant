#!/usr/bin/env python3
"""Print crawl_errors aggregates for before/after crawl comparison."""
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

QUANT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db", type=Path, default=QUANT_ROOT / "data" / "web_intel_leonquant.duckdb")
    args = p.parse_args()
    db = args.db.resolve()
    if not db.is_file():
        print(f"No DB: {db}")
        return 2
    c = duckdb.connect(str(db), read_only=True)
    total = c.execute("SELECT COUNT(*) FROM crawl_errors").fetchone()[0]
    print(f"crawl_errors total: {total}")
    rows = c.execute(
        """
        SELECT error_type, COUNT(*) n FROM crawl_errors
        GROUP BY 1 ORDER BY n DESC
        """
    ).fetchall()
    for et, n in rows[:15]:
        print(f"  {n:5d}  {et}")
    for label, sql in (
        ("EmptyFeed", "SELECT COUNT(*) FROM crawl_errors WHERE error_type = 'EmptyFeed'"),
        ("NotToday", "SELECT COUNT(*) FROM crawl_errors WHERE error_type = 'NotToday'"),
        ("HttpError", "SELECT COUNT(*) FROM crawl_errors WHERE error_type = 'HttpError'"),
    ):
        n = c.execute(sql).fetchone()[0]
        print(f"{label}: {n}")
    arts = c.execute("SELECT COUNT(*), COUNT(DISTINCT source_id) FROM articles").fetchone()
    print(f"articles: {arts[0]} ({arts[1]} sources)")
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
