#!/usr/bin/env python3
"""Export Leon Web Intel DuckDB → Leon Quant news JSON (all articles + today subset)."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

QUANT_ROOT = Path(__file__).resolve().parents[1]


def resolve_intel_root() -> Path:
    env = os.environ.get("LEON_WEB_INTEL_ROOT")
    if env:
        return Path(env).resolve()
    vendored = QUANT_ROOT / "leon_web_intel"
    if (vendored / "src" / "storage" / "db.py").is_file():
        return vendored
    return QUANT_ROOT.parent / "leon_web_intel"


def host_from_url(url: str) -> str:
    try:
        netloc = urlparse(url).netloc.lower()
    except Exception:
        return ""
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


def resolve_export_calendar_date(date_arg: str, tz_name: str) -> str:
    s = date_arg.strip()
    if s.lower() == "today":
        return datetime.now(ZoneInfo(tz_name)).date().isoformat()
    return s


def is_probable_listing_page(url: str, title: str) -> bool:
    """Heuristic: category / pagination pages (not single articles)."""
    u = (url or "").lower()
    t = (title or "").lower()
    path = urlparse(url).path.lower().strip("/")
    if path in ("", "index.html", "index.htm"):
        return True
    # VN / legacy: short category .htm (video.htm, hang-hoa.htm) without article slug
    if path.endswith((".htm", ".html")):
        segments = [s for s in path.split("/") if s]
        last = segments[-1] if segments else ""
        stem = last.rsplit(".", 1)[0]
        if len(segments) <= 2 and len(stem) < 28 and not re.search(r"\d{6,}", last):
            if stem.count("-") < 4 and not re.search(r"\d{4}[-/]\d{2}", path):
                return True
    q = urlparse(url).query.lower()
    try:
        qs = parse_qs(urlparse(url).query.lower())
        for key in ("page", "p", "trang", "paged", "pagenum"):
            vals = qs.get(key) or []
            for v in vals:
                try:
                    if int(v) >= 2:
                        return True
                except ValueError:
                    continue
    except Exception:
        pass
    for needle in ("paged=", "pagenum="):
        if needle in q:
            return True
    path_needles = (
        "/tag/",
        "/tags/",
        "/topic/",
        "/category/",
        "/categories/",
        "trang-1",
        "trang-2",
        "-trang-1",
        "/page/",
    )
    if any(n in u for n in path_needles):
        return True
    for phrase in ("trang 1", "trang 2", "trang 3", " - trang 1", " | trang 1"):
        if phrase in t:
            return True
    return False


def infer_region(tier_id: str) -> str:
    t = tier_id.lower()
    if "vietnam" in t or t.startswith("vietnam"):
        return "vietnam"
    return "global"


def published_iso(val: Any) -> str | None:
    if val is None:
        return None
    if hasattr(val, "isoformat"):
        try:
            dt = val.to_pydatetime() if hasattr(val, "to_pydatetime") else val  # type: ignore[assignment]
            if getattr(dt, "tzinfo", None) is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except Exception:
            pass
    s = str(val).strip()
    return s or None


def rows_to_articles(
    rows: list[dict[str, Any]],
    manifest: dict[str, str],
    *,
    filter_listings: bool = True,
) -> list[dict[str, Any]]:
    sys.path.insert(0, str(QUANT_ROOT))
    from macro_relevance import macro_relevance_score  # noqa: E402

    articles: list[dict[str, Any]] = []
    for row in rows:
        url = str(row.get("url") or "")
        title = str(row.get("title") or "").strip() or "Untitled"
        if filter_listings and is_probable_listing_page(url, title):
            continue
        content = str(row.get("content") or "")
        summary = (content[:1500] + "…") if len(content) > 1500 else content
        host = host_from_url(url)
        tier_id = manifest.get(host, "intel_crawl")
        art = {
            "title": title,
            "url": url,
            "summary": summary,
            "published_at": published_iso(row.get("published_at")),
            "source": host or str(row.get("source_id") or "intel"),
            "category": tier_id,
            "region": infer_region(tier_id),
            "tier": tier_id,
        }
        art["macro_score"] = macro_relevance_score(art)
        articles.append(art)
    return articles


def build_payload(
    articles: list[dict[str, Any]],
    *,
    db_path: Path,
    export_kind: str,
    target_date: str | None = None,
    timezone_name: str | None = None,
    recent_calendar_days: int | None = None,
) -> dict[str, Any]:
    pipe: dict[str, Any] = {"kind": "leon_web_intel_scrapy", "db": str(db_path), "export": export_kind}
    if target_date is not None:
        pipe["date"] = target_date
    if timezone_name is not None:
        pipe["timezone"] = timezone_name
    if recent_calendar_days is not None:
        pipe["recent_calendar_days"] = int(recent_calendar_days)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(articles),
        "source_error_count": 0,
        "articles": articles,
        "errors": [],
        "pipeline": pipe,
    }


def write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Intel DuckDB → news JSON export(s)")
    parser.add_argument("--db", type=Path, required=True, help="web_intel_leonquant.duckdb (absolute)")
    parser.add_argument("--date", default="today", help="Calendar day for today export")
    parser.add_argument("--timezone", default="Asia/Ho_Chi_Minh")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Legacy: single today file (same as --output-today)",
    )
    parser.add_argument(
        "--output-today",
        type=Path,
        default=QUANT_ROOT / "news_output_today.json",
    )
    parser.add_argument(
        "--output-all",
        type=Path,
        default=QUANT_ROOT / "news_output_all.json",
    )
    parser.add_argument("--manifest", type=Path, default=QUANT_ROOT / "config" / "tiers_manifest.json")
    parser.add_argument(
        "--today-only",
        action="store_true",
        help="Only write today file (skip --output-all)",
    )
    parser.add_argument(
        "--no-filter-listings",
        action="store_true",
        help="Include likely category/pagination pages in JSON exports",
    )
    parser.add_argument(
        "--recent-calendar-days",
        type=int,
        default=None,
        help="Export window: last N local calendar days ending on --date (default: crawl_rules.yaml)",
    )
    args = parser.parse_args()

    intel = resolve_intel_root()
    if not (intel / "src" / "storage" / "db.py").is_file():
        print(f"ERROR: LEON_WEB_INTEL_ROOT invalid (missing storage/db.py): {intel}", file=sys.stderr)
        return 2

    sys.path.insert(0, str(intel / "src"))
    from settings import load_crawl_rules  # noqa: E402
    from storage.db import WebIntelDB  # noqa: E402

    rules = load_crawl_rules(intel / "config" / "crawl_rules.yaml")
    recent_days = rules.recent_calendar_days if args.recent_calendar_days is None else args.recent_calendar_days
    recent_days = max(1, int(recent_days))
    manifest: dict[str, str] = {}
    if args.manifest.is_file():
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))

    db_path = args.db.resolve()
    today_path = (args.output or args.output_today).resolve()
    all_path = args.output_all.resolve()
    export_date = resolve_export_calendar_date(args.date, args.timezone)
    if args.date.strip().lower() == "today":
        print(f"Export calendar date (pinned): {export_date} ({args.timezone}); recent_calendar_days={recent_days}")

    db = WebIntelDB(db_path)
    try:
        today_rows = db.fetch_today_articles(
            target_date_str=export_date, timezone_name=args.timezone, recent_calendar_days=recent_days
        )
        all_rows = [] if args.today_only else db.fetch_all_articles()
    finally:
        db.close()

    fl = not args.no_filter_listings
    today_articles = rows_to_articles(today_rows, manifest, filter_listings=fl)
    today_payload = build_payload(
        today_articles,
        db_path=db_path,
        export_kind="today",
        target_date=export_date,
        timezone_name=args.timezone,
        recent_calendar_days=recent_days,
    )
    write_payload(today_path, today_payload)
    print(f"Wrote {len(today_articles)} articles -> {today_path}")

    if not args.today_only:
        all_articles = rows_to_articles(all_rows, manifest, filter_listings=fl)
        all_payload = build_payload(all_articles, db_path=db_path, export_kind="all")
        write_payload(all_path, all_payload)
        print(f"Wrote {len(all_articles)} articles -> {all_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
