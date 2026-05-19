#!/usr/bin/env python3
"""Write crawl_baseline_snapshot.md from DuckDB (errors, articles, export window)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import duckdb

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "scripts" / "crawl_baseline_snapshot.md"
DEFAULT_DB = ROOT / "data" / "web_intel_leonquant.duckdb"
TZ = "Asia/Ho_Chi_Minh"


def main() -> int:
    db_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DB
    if not db_path.is_file():
        print(f"No DB: {db_path}", file=sys.stderr)
        return 2

    anchor = datetime.now(ZoneInfo(TZ)).date().isoformat()
    today_json = ROOT / "news_output_today.json"
    today_count = 0
    if today_json.is_file():
        try:
            today_count = int(json.loads(today_json.read_text(encoding="utf-8")).get("count", 0))
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    c = duckdb.connect(str(db_path), read_only=True)
    err_total = c.execute("SELECT COUNT(*) FROM crawl_errors").fetchone()[0]
    err_rows = c.execute(
        "SELECT error_type, COUNT(*) n FROM crawl_errors GROUP BY 1 ORDER BY n DESC LIMIT 12"
    ).fetchall()
    arts, sources = c.execute("SELECT COUNT(*), COUNT(DISTINCT source_id) FROM articles").fetchone()
    prof = c.execute("SELECT COUNT(*) FROM source_profiles").fetchone()[0]
    skip = c.execute("SELECT COUNT(*) FROM source_crawl_skip").fetchone()[0]
    c.close()

    lines = [
        "# Crawl baseline snapshot",
        "",
        f"- generated_at_utc: {datetime.now(timezone.utc).isoformat()}",
        f"- db: `{db_path}`",
        f"- calendar_anchor ({TZ}): **{anchor}**",
        f"- recent_calendar_days: 2 (from crawl_rules.yaml)",
        "",
        "## Articles",
        f"- articles_total: **{arts}**",
        f"- distinct_source_id: **{sources}**",
        f"- news_output_today.json count: **{today_count}**",
        "",
        "## crawl_errors",
        f"- total: **{err_total}**",
        "",
        "| error_type | n |",
        "| --- | ---: |",
    ]
    for et, n in err_rows:
        lines.append(f"| {et} | {n} |")
    lines.extend(
        [
            "",
            "## Profiles / skip",
            f"- source_profiles: {prof}",
            f"- source_crawl_skip: {skip}",
            "",
            "## Commands",
            "```bash",
            "python scripts/crawl_error_snapshot.py",
            "python scripts/investigate_zero_article_sources.py",
            "python scripts/source_coverage_report.py",
            "```",
        ]
    )
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
