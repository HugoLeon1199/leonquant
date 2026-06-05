#!/usr/bin/env python3
"""Giữ publishedAt trên link khi Pages rebuild content.json (DuckDB seed có thể thiếu URL mới)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _published_map(data: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    idx = data.get("articleLinkIndex")
    if isinstance(idx, list):
        for row in idx:
            if not isinstance(row, dict):
                continue
            u = str(row.get("url") or "").strip()
            ts = str(row.get("publishedAt") or row.get("published_at") or "").strip()
            if u and ts:
                out[u] = ts
    for key in ("allArticles",):
        rows = data.get(key)
        if isinstance(rows, list):
            for row in rows:
                if not isinstance(row, dict):
                    continue
                u = str(row.get("url") or "").strip()
                ts = str(row.get("publishedAt") or row.get("published_at") or "").strip()
                if u and ts:
                    out.setdefault(u, ts)
    return out


def _apply_links(links: list[Any], pub: dict[str, str]) -> int:
    n = 0
    for lk in links:
        if not isinstance(lk, dict):
            continue
        u = str(lk.get("url") or "").strip()
        if not u or str(lk.get("publishedAt") or lk.get("published_at") or "").strip():
            continue
        ts = pub.get(u)
        if ts:
            lk["publishedAt"] = ts
            n += 1
    return n


def merge_published_at(prior: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    pub = _published_map(prior)
    if not pub:
        return target
    out = dict(target)
    merged = 0
    idx = out.get("articleLinkIndex")
    if isinstance(idx, list):
        for row in idx:
            if not isinstance(row, dict):
                continue
            u = str(row.get("url") or "").strip()
            if u and not str(row.get("publishedAt") or "").strip() and u in pub:
                row["publishedAt"] = pub[u]
                merged += 1
    for sec in out.get("sectorDeepBriefs") or []:
        if not isinstance(sec, dict):
            continue
        for d in sec.get("storyDossiers") or []:
            if isinstance(d, dict) and isinstance(d.get("links"), list):
                merged += _apply_links(d["links"], pub)
        for sb in sec.get("subsectorBriefs") or []:
            if isinstance(sb, dict) and isinstance(sb.get("links"), list):
                merged += _apply_links(sb["links"], pub)
    for row in out.get("frontPage") or []:
        if isinstance(row, dict) and isinstance(row.get("links"), list):
            merged += _apply_links(row["links"], pub)
    for row in out.get("digestNotableArticles") or []:
        if isinstance(row, dict):
            u = str(row.get("url") or "").strip()
            if u and not str(row.get("publishedAt") or "").strip() and u in pub:
                row["publishedAt"] = pub[u]
                merged += 1
    print(f"merge_link_published_at: restored {merged} link timestamp(s) from prior content.json")
    return out


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: merge_link_published_at.py <prior-content.json> <target-content.json>", file=sys.stderr)
        return 2
    prior_path = Path(sys.argv[1])
    target_path = Path(sys.argv[2])
    prior = json.loads(prior_path.read_text(encoding="utf-8"))
    target = json.loads(target_path.read_text(encoding="utf-8"))
    merged = merge_published_at(prior, target)
    target_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
