#!/usr/bin/env python3
"""Export recent articles from DuckDB → compact JSON for AI (full text, no truncation)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

QUANT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = QUANT_ROOT / "scripts"


def resolve_intel_root() -> Path:
    env = os.environ.get("LEON_WEB_INTEL_ROOT")
    if env:
        return Path(env).resolve()
    vendored = QUANT_ROOT / "leon_web_intel"
    if (vendored / "src" / "storage" / "db.py").is_file():
        return vendored
    return QUANT_ROOT.parent / "leon_web_intel"


def row_to_ai_article(row: dict[str, Any]) -> dict[str, Any]:
    url = str(row.get("url") or "")
    title = str(row.get("title") or "").strip() or "Untitled"
    content = str(row.get("content") or "")
    return {
        "title": title,
        "url": url,
        "text": content,
    }


def resolve_export_calendar_date(date_arg: str, tz_name: str) -> str:
    s = date_arg.strip().lower()
    tz = ZoneInfo(tz_name)
    today = datetime.now(tz).date()
    if s == "today":
        return today.isoformat()
    if s == "yesterday":
        return (today - timedelta(days=1)).isoformat()
    return date_arg.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="DuckDB → news_for_ai.json (full text, recent days)")
    parser.add_argument("--db", type=Path, default=QUANT_ROOT / "data" / "web_intel_leonquant.duckdb")
    parser.add_argument(
        "--date",
        default="today",
        help="End day of window: today | yesterday | YYYY-MM-DD (timezone-aware)",
    )
    parser.add_argument("--timezone", default="Asia/Ho_Chi_Minh")
    parser.add_argument(
        "--recent-calendar-days",
        type=int,
        default=2,
        help="Local calendar days ending on --date (default 2 = two most recent days)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=QUANT_ROOT / "news_for_ai.json",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Apply listing/dedup filters (same as clean_news_for_ai.py)",
    )
    parser.add_argument("--min-text-chars", type=int, default=250)
    args = parser.parse_args()

    intel = resolve_intel_root()
    if not (intel / "src" / "storage" / "db.py").is_file():
        print(f"ERROR: LEON_WEB_INTEL_ROOT invalid: {intel}", file=sys.stderr)
        return 2

    db_path = args.db.resolve()
    if not db_path.is_file():
        print(f"ERROR: DuckDB not found: {db_path}", file=sys.stderr)
        return 2

    sys.path.insert(0, str(intel / "src"))
    from storage.db import WebIntelDB  # noqa: E402

    export_date = resolve_export_calendar_date(args.date, args.timezone)
    recent_days = max(1, int(args.recent_calendar_days))

    db = WebIntelDB(db_path)
    try:
        rows = db.fetch_today_articles(
            target_date_str=export_date,
            timezone_name=args.timezone,
            recent_calendar_days=recent_days,
        )
    finally:
        db.close()

    articles = [row_to_ai_article(r) for r in rows]
    clean_stats: dict[str, int] | None = None
    if args.clean:
        sys.path.insert(0, str(SCRIPTS))
        from news_ai_filters import clean_articles_for_ai  # noqa: E402

        articles, clean_stats = clean_articles_for_ai(
            articles, min_text_chars=args.min_text_chars
        )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "ai_summarization",
        "count": len(articles),
        "window": {
            "end_date": export_date,
            "timezone": args.timezone,
            "recent_calendar_days": recent_days,
        },
        "schema": ["title", "url", "text"],
        "articles": articles,
    }
    if clean_stats:
        payload["clean_stats"] = clean_stats

    out = args.output.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    with_text = sum(1 for a in articles if (a.get("text") or "").strip())
    avg_len = sum(len(a.get("text") or "") for a in articles) // len(articles) if articles else 0
    print(f"Wrote {len(articles)} articles -> {out}")
    print(f"  with text: {with_text} | avg text length: {avg_len} chars")
    print(f"  window: last {recent_days} day(s) ending {export_date} ({args.timezone})")
    if clean_stats:
        print(
            f"  cleaned: -{clean_stats['drop_listing_title_url']} listing(url), "
            f"-{clean_stats['drop_listing_content']} listing(body), "
            f"-{clean_stats['drop_dup_url_and_text']} same url+text"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
