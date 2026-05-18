#!/usr/bin/env python3
"""Validate config/news_sources_tiered.json shape (no network)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT = ROOT / "config" / "news_sources_tiered.json"


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    data = json.loads(path.read_text(encoding="utf-8"))
    tiers = data.get("tiers")
    if not isinstance(tiers, list) or not tiers:
        print("ERROR: missing non-empty 'tiers' list", file=sys.stderr)
        return 2
    n = 0
    seen_urls: set[str] = set()
    for i, tier in enumerate(tiers):
        if not isinstance(tier, dict):
            print(f"ERROR: tiers[{i}] must be object", file=sys.stderr)
            return 2
        if not tier.get("id") or not tier.get("title"):
            print(f"ERROR: tiers[{i}] needs id and title", file=sys.stderr)
            return 2
        sources = tier.get("sources")
        if not isinstance(sources, list):
            print(f"ERROR: tier {tier.get('id')!r} sources must be list", file=sys.stderr)
            return 2
        for j, src in enumerate(sources):
            if not isinstance(src, dict):
                print(f"ERROR: tier {tier['id']} sources[{j}] not object", file=sys.stderr)
                return 2
            for k in ("name", "url", "category", "region"):
                if k not in src or not str(src.get(k, "")).strip():
                    print(f"ERROR: tier {tier['id']} source[{j}] missing {k}", file=sys.stderr)
                    return 2
            u = str(src["url"]).strip()
            if u in seen_urls:
                print(f"WARN: duplicate feed url: {u}")
            seen_urls.add(u)
            n += 1
    print(f"OK: {len(tiers)} tiers, {n} RSS sources — {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
