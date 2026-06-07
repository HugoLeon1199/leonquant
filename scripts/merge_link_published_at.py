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


def _timestamp_has_clock(ts: str) -> bool:
    s = str(ts or "").strip()
    if not s:
        return False
    if "T" in s:
        return True
    return len(s) > 10 and s[10:11] in (" ", "T")


def _parse_ts(ts: str) -> float | None:
    s = str(ts or "").strip()
    if not s:
        return None
    try:
        from datetime import datetime

        if "T" in s:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        elif len(s) >= 19 and s[10:11] == " ":
            dt = datetime.fromisoformat(s[:19].replace(" ", "T"))
        elif len(s) >= 10:
            dt = datetime.fromisoformat(s[:10] + "T00:00:00")
        else:
            return None
        if dt.tzinfo is not None:
            dt = dt.astimezone(datetime.now().astimezone().tzinfo).replace(tzinfo=None)
        return dt.timestamp()
    except Exception:
        return None


def _pick_better_timestamp(current: str, candidate: str, *, min_ts: float | None = None) -> str:
    cur = str(current or "").strip()
    cand = str(candidate or "").strip()
    if not cand:
        return cur
    cand_parsed = _parse_ts(cand)
    if min_ts is not None and cand_parsed is not None and cand_parsed < min_ts:
        return cur
    if not cur:
        return cand
    cur_clock = _timestamp_has_clock(cur)
    cand_clock = _timestamp_has_clock(cand)
    if cand_clock and not cur_clock:
        return cand
    if cur_clock and not cand_clock:
        return cur
    cur_ts = _parse_ts(cur)
    cand_ts = _parse_ts(cand)
    if cur_ts is not None and cand_ts is not None and cand_ts > cur_ts:
        return cand
    return cur


def _apply_links(links: list[Any], pub: dict[str, str], *, min_ts: float | None = None) -> int:
    n = 0
    for lk in links:
        if not isinstance(lk, dict):
            continue
        u = str(lk.get("url") or "").strip()
        if not u:
            continue
        ts_prior = pub.get(u)
        if not ts_prior:
            continue
        cur = str(lk.get("publishedAt") or lk.get("published_at") or "").strip()
        best = _pick_better_timestamp(cur, ts_prior, min_ts=min_ts)
        if best and best != cur:
            lk["publishedAt"] = best
            n += 1
    return n


def merge_published_at(prior: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    pub = _published_map(prior)
    if not pub:
        return target
    from datetime import datetime, timedelta

    min_ts = (datetime.utcnow() - timedelta(hours=72)).timestamp()
    out = dict(target)
    merged = 0
    idx = out.get("articleLinkIndex")
    if isinstance(idx, list):
        for row in idx:
            if not isinstance(row, dict):
                continue
            u = str(row.get("url") or "").strip()
            if not u or u not in pub:
                continue
            cur = str(row.get("publishedAt") or "").strip()
            best = _pick_better_timestamp(cur, pub[u], min_ts=min_ts)
            if best and best != cur:
                row["publishedAt"] = best
                merged += 1
    for sec in out.get("sectorDeepBriefs") or []:
        if not isinstance(sec, dict):
            continue
        for d in sec.get("storyDossiers") or []:
            if isinstance(d, dict) and isinstance(d.get("links"), list):
                merged += _apply_links(d["links"], pub, min_ts=min_ts)
        for sb in sec.get("subsectorBriefs") or []:
            if isinstance(sb, dict) and isinstance(sb.get("links"), list):
                merged += _apply_links(sb["links"], pub, min_ts=min_ts)
    for row in out.get("frontPage") or []:
        if isinstance(row, dict) and isinstance(row.get("links"), list):
            merged += _apply_links(row["links"], pub, min_ts=min_ts)
    for row in out.get("digestNotableArticles") or []:
        if isinstance(row, dict):
            u = str(row.get("url") or "").strip()
            if not u or u not in pub:
                continue
            cur = str(row.get("publishedAt") or "").strip()
            best = _pick_better_timestamp(cur, pub[u], min_ts=min_ts)
            if best and best != cur:
                row["publishedAt"] = best
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
