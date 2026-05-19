"""RSS / Atom discovery and lightweight validation."""

from __future__ import annotations

from collections.abc import Callable
from urllib.parse import urljoin, urlparse

import feedparser
from bs4 import BeautifulSoup
from loguru import logger

from profiler.normalize import NormalizedSource
from settings import CrawlRules


def validate_feed_body(body: str, url: str) -> bool:
    parsed = feedparser.parse(body)
    if getattr(parsed, "bozo", False) and not parsed.entries:
        return False
    entries = getattr(parsed, "entries", []) or []
    if len(entries) == 0:
        return False
    ok_any = False
    for e in entries[:50]:
        link = (e.get("link") or "").strip()
        title = (e.get("title") or "").strip()
        if link or title:
            ok_any = True
            break
    return ok_any


def parse_rss_candidate(body: str, url: str) -> bool:
    """Thin alias for tests."""
    return validate_feed_body(body, url)


def discover_rss_urls(
    norm: NormalizedSource,
    homepage_html: str,
    homepage_url: str,
    rules: CrawlRules,
    fetch_text: Callable[[str], tuple[int, str]],
) -> tuple[list[str], int]:
    candidates: list[str] = []
    seen: set[str] = set()

    def add(u: str) -> None:
        if u not in seen:
            seen.add(u)
            candidates.append(u)

    # Method 2: link tags from homepage
    soup = BeautifulSoup(homepage_html, "lxml")
    for link in soup.find_all("link"):
        rel = (link.get("rel") or [])
        if isinstance(rel, str):
            rel = [rel]
        rel_l = [str(r).lower() for r in rel]
        typ = (link.get("type") or "").lower()
        if "alternate" in rel_l and ("rss" in typ or "atom" in typ or "xml" in typ):
            href = link.get("href")
            if href:
                add(urljoin(homepage_url, href))

    parsed_home = urlparse(homepage_url)
    origin = f"{parsed_home.scheme}://{parsed_home.netloc}"

    for path in rules.rss_candidate_paths:
        if len(candidates) >= rules.max_rss_candidates:
            break
        add(urljoin(origin, path))

    valid: list[str] = []
    tried = 0
    probe_cap = max(1, rules.profiler_max_rss_http_attempts)
    for cand in candidates:
        if tried >= probe_cap:
            break
        tried += 1
        try:
            status, body = fetch_text(cand)
            if status >= 400:
                continue
            if validate_feed_body(body, cand):
                valid.append(cand)
                break
        except Exception as exc:  # noqa: BLE001
            logger.debug("rss candidate failed {}: {}", cand, exc)

    return valid, len(valid)
