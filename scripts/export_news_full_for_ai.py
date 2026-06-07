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


def _published_at_iso(val: Any) -> str:
    if val is None:
        return ""
    if hasattr(val, "isoformat"):
        try:
            dt = val.to_pydatetime() if hasattr(val, "to_pydatetime") else val  # type: ignore[assignment]
            if getattr(dt, "tzinfo", None) is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except Exception:
            pass
    return str(val).strip()


def _host_from_url(url: str) -> str:
    try:
        from urllib.parse import urlparse

        host = (urlparse(url).hostname or "").lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def row_to_ai_article(row: dict[str, Any]) -> dict[str, Any]:
    url = str(row.get("url") or "")
    title = str(row.get("title") or "").strip() or "Untitled"
    content = str(row.get("content") or "")
    published = _published_at_iso(row.get("published_at"))
    source = str(row.get("source_id") or row.get("source") or "").strip() or _host_from_url(url)
    out: dict[str, Any] = {
        "title": title,
        "url": url,
        "text": content,
    }
    if published:
        out["published_at"] = published
    if source:
        out["source"] = source
    return out


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
    parser.add_argument(
        "--window-state",
        type=Path,
        default=None,
        help="JSON from prepare_digest_db.py (overrides --recent-calendar-days / enables rolling export)",
    )
    parser.add_argument(
        "--rolling-hours",
        type=int,
        default=0,
        help="Export by extracted_at rolling window (overrides calendar when > 0)",
    )
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
    rolling_hours = max(0, int(args.rolling_hours))
    export_mode = "calendar"

    if args.window_state is not None:
        sys.path.insert(0, str(SCRIPTS))
        from digest_window import load_window_state  # noqa: E402

        state = load_window_state(args.window_state)
        if state:
            export_date = str(state.get("end_date") or export_date)
            args.timezone = str(state.get("timezone") or args.timezone)
            export_mode = str(state.get("mode") or "calendar")
            if export_mode == "rolling":
                rolling_hours = int(state.get("rolling_hours") or 48)
            else:
                recent_days = max(1, int(state.get("recent_calendar_days") or recent_days))
            print(
                f"Using window state: mode={export_mode} calendar_days={recent_days} "
                f"rolling_hours={rolling_hours or 'n/a'} expected={state.get('article_count')}"
            )

    db = WebIntelDB(db_path)
    try:
        if rolling_hours > 0:
            df = db.conn.execute(
                f"""
                SELECT * FROM articles
                WHERE extracted_at >= CURRENT_TIMESTAMP - INTERVAL {rolling_hours} HOUR
                  AND COALESCE(content_length, 0) >= 200
                ORDER BY extracted_at DESC
                """
            ).fetchdf()
            rows = df.to_dict("records")
        else:
            rows = db.fetch_today_articles(
                target_date_str=export_date,
                timezone_name=args.timezone,
                recent_calendar_days=recent_days,
            )
    finally:
        db.close()

    articles = [row_to_ai_article(r) for r in rows]

    sys.path.insert(0, str(SCRIPTS))
    from digest_window import filter_digest_fresh_articles  # noqa: E402

    before_fresh = len(articles)
    articles = filter_digest_fresh_articles(
        articles,
        end_date_str=export_date,
        timezone_name=args.timezone,
        max_calendar_days=min(recent_days, 2),
        rolling_hours=rolling_hours if rolling_hours > 0 else 48,
    )
    if before_fresh != len(articles):
        print(
            f"  Tin48h freshness filter: {before_fresh} -> {len(articles)} articles "
            f"(max 2 calendar days ending {export_date})"
        )
    recent_days = min(recent_days, 2)

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
            "mode": export_mode,
            "rolling_hours": rolling_hours if rolling_hours > 0 else None,
        },
        "schema": ["title", "url", "text", "published_at", "source"],
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
    print(f"  window: mode={export_mode}", end="")
    if rolling_hours > 0:
        print(f" rolling {rolling_hours}h", end="")
    else:
        print(f" last {recent_days} day(s) ending {export_date} ({args.timezone})", end="")
    print()
    if clean_stats:
        print(
            f"  cleaned: -{clean_stats['drop_listing_title_url']} listing(url), "
            f"-{clean_stats['drop_listing_content']} listing(body), "
            f"-{clean_stats['drop_dup_url_and_text']} same url+text"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
