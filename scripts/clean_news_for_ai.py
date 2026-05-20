#!/usr/bin/env python3
"""Clean news_for_ai.json (listings, dupes, short text) → news_for_ai_clean.json for Gemini."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from news_ai_filters import clean_articles_for_ai

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean news_for_ai JSON for Gemini digest")
    parser.add_argument("--input", type=Path, default=ROOT / "news_for_ai.json")
    parser.add_argument("--output", type=Path, default=ROOT / "news_for_ai_clean.json")
    parser.add_argument("--min-text-chars", type=int, default=250)
    parser.add_argument("--max-text-chars", type=int, default=0, help="0 = no cap")
    parser.add_argument("--keep-listings", action="store_true", help="Do not drop listing pages")
    parser.add_argument(
        "--no-dedupe",
        action="store_true",
        help="Keep rows even when URL and text both match an earlier row",
    )
    args = parser.parse_args()

    inp = args.input.resolve()
    if not inp.is_file():
        print(f"ERROR: not found: {inp}", flush=True)
        return 2

    data = json.loads(inp.read_text(encoding="utf-8"))
    articles = data.get("articles") or []
    cleaned, stats = clean_articles_for_ai(
        articles,
        min_text_chars=args.min_text_chars,
        max_text_chars=args.max_text_chars,
        drop_listings=not args.keep_listings,
        dedupe_same_url_and_text=not args.no_dedupe,
    )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "ai_summarization_clean",
        "source_file": str(inp),
        "count": len(cleaned),
        "window": data.get("window"),
        "schema": ["title", "url", "text"],
        "clean_stats": stats,
        "articles": cleaned,
    }

    out = args.output.resolve()
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    inp_mb = inp.stat().st_size / 1024 / 1024
    out_mb = out.stat().st_size / 1024 / 1024
    chars = sum(len(a.get("text") or "") for a in cleaned)
    print(f"Input:  {stats['input']} articles ({inp_mb:.2f} MB) -> {inp}")
    print(f"Output: {stats['output']} articles ({out_mb:.2f} MB) -> {out}")
    print(f"  drop listing (title/url): {stats['drop_listing_title_url']}")
    print(f"  drop listing (content):   {stats['drop_listing_content']}")
    print(f"  drop short text:          {stats['drop_short_text']}")
    print(f"  drop same url+text:       {stats['drop_dup_url_and_text']}")
    print(f"  total text chars:         {chars:,} (~{chars // 4:,} est. tokens)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
