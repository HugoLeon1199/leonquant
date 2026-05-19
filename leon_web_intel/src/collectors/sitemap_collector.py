"""Collect lightweight sitemap samples."""

from __future__ import annotations

import json
import re
from typing import Any

from profiler.sitemap_detector import parse_sitemap_bytes
from storage.db import WebIntelDB, new_id, utc_now
from storage.raw_store import RawStore
from utils.hashing import sha256_text


_ARTICLE_HINT = re.compile(
    r"(/news/|/article/|/story/|/world/|/business/|/politics/|/\d{4}/|\.html$)",
    re.I,
)


def filter_article_like(urls: list[str], limit: int) -> list[str]:
    scored = []
    for u in urls:
        score = 0
        if _ARTICLE_HINT.search(u):
            score += 2
        if len(u.split("/")) >= 5:
            score += 1
        scored.append((score, u))
    scored.sort(key=lambda x: x[0], reverse=True)
    out: list[str] = []
    for _, u in scored:
        if u not in out:
            out.append(u)
        if len(out) >= limit:
            break
    return out


def discover_from_sitemap(
    *,
    source_id: str,
    sitemap_url: str,
    max_items: int,
    fetch_bytes,
    raw_store: RawStore,
    db: WebIntelDB,
    max_urls_probe: int,
) -> list[dict[str, Any]]:
    status, body = fetch_bytes(sitemap_url)
    if status >= 400 or not body:
        return []
    ext = "xml.gz" if sitemap_url.endswith(".gz") else "xml"
    raw_store.save_sitemap(source_id, body, ext=ext.split(".")[-1])

    ok, locs, is_index = parse_sitemap_bytes(body, sitemap_url)
    if not ok:
        return []

    candidate_urls = list(locs)
    if is_index:
        candidate_urls = []
        for child in locs[:3]:
            st2, body2 = fetch_bytes(child)
            if st2 >= 400 or not body2:
                continue
            ok2, inner, _ = parse_sitemap_bytes(body2, child)
            if ok2:
                candidate_urls.extend(inner)
            if len(candidate_urls) >= max_urls_probe:
                break

    picked = filter_article_like(candidate_urls, max_items)
    rows: list[dict[str, Any]] = []
    for link in picked:
        row = {
            "id": new_id(),
            "source_id": source_id,
            "url": link,
            "discovery_method": "sitemap",
            "title": None,
            "published_at": None,
            "raw_metadata": json.dumps({"sitemap_url": sitemap_url}),
            "discovered_at": utc_now(),
            "url_hash": sha256_text(link),
        }
        db.insert_discovered_url(row)
        rows.append(row)
    return rows
