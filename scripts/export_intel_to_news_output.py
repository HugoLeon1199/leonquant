#!/usr/bin/env python3
"""Export Leon Web Intel DuckDB (today articles) → Leon Quant ``news_output.json`` (downstream unchanged)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

QUANT_ROOT = Path(__file__).resolve().parents[1]


def resolve_intel_root() -> Path:
    env = os.environ.get("LEON_WEB_INTEL_ROOT")
    if env:
        return Path(env).resolve()
    return QUANT_ROOT.parent / "leon_web_intel"


def host_from_url(url: str) -> str:
    try:
        netloc = urlparse(url).netloc.lower()
    except Exception:
        return ""
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Intel DuckDB → news_output.json")
    parser.add_argument("--db", type=Path, required=True, help="web_intel_leonquant.duckdb (absolute)")
    parser.add_argument("--date", default="today")
    parser.add_argument("--timezone", default="Asia/Ho_Chi_Minh")
    parser.add_argument("--output", type=Path, default=QUANT_ROOT / "news_output.json")
    parser.add_argument("--manifest", type=Path, default=QUANT_ROOT / "config" / "tiers_manifest.json")
    args = parser.parse_args()

    intel = resolve_intel_root()
    if not (intel / "src" / "storage" / "db.py").is_file():
        print(f"ERROR: LEON_WEB_INTEL_ROOT invalid (missing storage/db.py): {intel}", file=sys.stderr)
        return 2

    sys.path.insert(0, str(intel / "src"))
    from storage.db import WebIntelDB  # noqa: E402

    sys.path.insert(0, str(QUANT_ROOT))
    from crawl_financial_news import macro_relevance_score  # noqa: E402

    manifest: dict[str, str] = {}
    if args.manifest.is_file():
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))

    db_path = args.db.resolve()
    db = WebIntelDB(db_path)
    try:
        rows = db.fetch_today_articles(target_date_str=args.date, timezone_name=args.timezone)
    finally:
        db.close()

    articles: list[dict[str, Any]] = []
    for row in rows:
        url = str(row.get("url") or "")
        title = str(row.get("title") or "").strip() or "Untitled"
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

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(articles),
        "source_error_count": 0,
        "articles": articles,
        "errors": [],
        "pipeline": {"kind": "leon_web_intel_scrapy", "db": str(db_path)},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(articles)} articles → {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
