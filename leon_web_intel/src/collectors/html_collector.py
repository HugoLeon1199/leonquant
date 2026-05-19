"""Collect internal links from HTML landing pages."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from storage.db import WebIntelDB, new_id, utc_now
from utils.hashing import sha256_text


def discover_internal_links(
    *,
    source_id: str,
    homepage_url: str,
    html: str,
    max_items: int,
    db: WebIntelDB,
) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    base = urlparse(homepage_url)
    links: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        abs_u = urljoin(homepage_url, href)
        p = urlparse(abs_u)
        if p.netloc.lower() != base.netloc.lower():
            continue
        if abs_u not in links:
            links.append(abs_u)
        if len(links) >= max_items * 8:
            break

    picked = links[:max_items]
    rows: list[dict[str, Any]] = []
    for link in picked:
        row = {
            "id": new_id(),
            "source_id": source_id,
            "url": link,
            "discovery_method": "html_internal_links",
            "title": None,
            "published_at": None,
            "raw_metadata": json.dumps({"homepage": homepage_url}),
            "discovered_at": utc_now(),
            "url_hash": sha256_text(link),
        }
        db.insert_discovered_url(row)
        rows.append(row)
    return rows
