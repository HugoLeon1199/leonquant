"""Shared filters to clean news JSON before Gemini digest."""

from __future__ import annotations

import hashlib
import re
from typing import Any
from urllib.parse import parse_qs, urlparse

# Re-export listing heuristic aligned with export_intel_to_news_output.py
LISTING_TITLE_PHRASES = (
    "trang 1",
    "trang 2",
    "trang 3",
    " - trang 1",
    " | trang 1",
    "trang chủ",
    "homepage",
    "danh sách",
    "danh sach",
)

LISTING_TITLE_EXACT = frozenset(
    s.lower()
    for s in (
        "forex news",
        "east asia",
        "spotlight",
        "markets",
        "business",
        "economy",
        "technology",
        "công nghệ",
    )
)

VN_DATE_IN_TEXT = re.compile(
    r"\b\d{1,2}/\d{1,2}/\d{4}\b|\b\d{1,2}-\d{1,2}-\d{4}\b"
)


def normalize_url(url: str) -> str:
    try:
        p = urlparse(url.strip())
        host = (p.netloc or "").lower()
        if host.startswith("www."):
            host = host[4:]
        path = p.path or "/"
        if path != "/" and path.endswith("/"):
            path = path[:-1]
        return f"{p.scheme or 'https'}://{host}{path}"
    except Exception:
        return url.strip().lower()


def is_probable_listing_page(url: str, title: str) -> bool:
    u = (url or "").lower()
    t = (title or "").strip().lower()
    if t in LISTING_TITLE_EXACT:
        return True
    path = urlparse(url).path.lower().strip("/")
    if path in ("", "index.html", "index.htm"):
        return True
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
            for v in qs.get(key) or []:
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
    for phrase in LISTING_TITLE_PHRASES:
        if phrase in t:
            return True
    # Short category path: /cong-nghe/ or single segment without article id
    if path and "/" not in path.strip("/"):
        seg = path.strip("/")
        if len(seg) < 40 and seg.count("-") < 4 and not re.search(r"\d{6,}", seg):
            if not re.search(r"/\d{4}/\d{2}/\d{2}", u) and not re.search(r"\d{4}-\d{2}-\d{2}", u):
                return True
    return False


def is_probable_listing_content(text: str, *, min_date_hits: int = 8) -> bool:
    """Category pages often embed many teaser lines with VN dates."""
    if not text:
        return False
    hits = len(VN_DATE_IN_TEXT.findall(text))
    if hits >= min_date_hits:
        return True
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if len(lines) >= 25 and hits >= 4:
        return True
    return False


def text_hash(text: str) -> str:
    normalized = re.sub(r"\s+", " ", (text or "").strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def clean_articles_for_ai(
    articles: list[dict[str, Any]],
    *,
    min_text_chars: int = 250,
    max_text_chars: int = 0,
    drop_listings: bool = True,
    dedupe_same_url_and_text: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    stats: dict[str, int] = {
        "input": len(articles),
        "drop_listing_title_url": 0,
        "drop_listing_content": 0,
        "drop_short_text": 0,
        "drop_dup_url_and_text": 0,
        "output": 0,
    }
    seen_url_text: set[tuple[str, str]] = set()
    out: list[dict[str, Any]] = []

    for raw in articles:
        title = str(raw.get("title") or "").strip() or "Untitled"
        url = str(raw.get("url") or "").strip()
        text = str(raw.get("text") or "").strip()

        if drop_listings and is_probable_listing_page(url, title):
            stats["drop_listing_title_url"] += 1
            continue
        if drop_listings and is_probable_listing_content(text):
            stats["drop_listing_content"] += 1
            continue
        if len(text) < min_text_chars:
            stats["drop_short_text"] += 1
            continue

        nurl = normalize_url(url) if url else ""
        th = text_hash(text)
        if dedupe_same_url_and_text and nurl and text:
            key = (nurl, th)
            if key in seen_url_text:
                stats["drop_dup_url_and_text"] += 1
                continue
            seen_url_text.add(key)

        if max_text_chars > 0 and len(text) > max_text_chars:
            text = text[:max_text_chars]

        row: dict[str, Any] = {"title": title, "url": url, "text": text}
        for key in ("published_at", "source", "category", "region"):
            val = raw.get(key)
            if val is not None and str(val).strip():
                row[key] = str(val).strip() if key != "published_at" else val
        out.append(row)

    stats["output"] = len(out)
    return out, stats
