"""Collect lightweight RSS samples."""

from __future__ import annotations

import json
from typing import Any

import feedparser

from storage.db import WebIntelDB, new_id, utc_now
from storage.raw_store import RawStore
from utils.hashing import sha256_text


def iter_feed_article_urls(feed_body: str, limit: int) -> list[tuple[str, str | None, str | None]]:
    parsed = feedparser.parse(feed_body)
    out: list[tuple[str, str | None, str | None]] = []
    for entry in getattr(parsed, "entries", []) or []:
        link = (entry.get("link") or "").strip()
        title = (entry.get("title") or "").strip() or None
        pub = entry.get("published") or entry.get("updated")
        pub_s = str(pub) if pub else None
        if link:
            out.append((link, title, pub_s))
        if len(out) >= limit:
            break
    return out


def discover_from_rss(
    *,
    source_id: str,
    rss_url: str,
    max_items: int,
    fetch_text,
    raw_store: RawStore,
    db: WebIntelDB,
) -> list[dict[str, Any]]:
    status, body = fetch_text(rss_url)
    if status >= 400:
        return []
    raw_store.save_rss(source_id, body.encode("utf-8"))
    urls = iter_feed_article_urls(body, max_items)
    rows: list[dict[str, Any]] = []
    for link, title, pub in urls:
        row = {
            "id": new_id(),
            "source_id": source_id,
            "url": link,
            "discovery_method": "rss_feed",
            "title": title,
            "published_at": pub,
            "raw_metadata": json.dumps({"rss_url": rss_url}),
            "discovered_at": utc_now(),
            "url_hash": sha256_text(link),
        }
        db.insert_discovered_url(row)
        rows.append(row)
    return rows
