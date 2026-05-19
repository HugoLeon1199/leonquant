"""Primary article body extraction using trafilatura."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import httpx
import trafilatura
from loguru import logger

from settings import CrawlRules
from storage.raw_store import RawStore
from utils.hashing import sha256_text


@dataclass
class ArticleResult:
    url: str
    title: str | None
    published_at: str | None
    content: str | None
    content_length: int
    content_hash: str
    language: str | None
    raw_path: str
    extract_ok: bool
    paywall_detected: bool
    login_detected: bool
    captcha_detected: bool


def compute_quality_score(
    *,
    title: str | None,
    content_length: int,
    published_at: str | None,
    source_active: bool,
    content_hash: str,
    url: str,
    strategy: str,
    raw_path: str,
    extract_ok: bool,
    paywall_triplet: tuple[bool, bool, bool],
    existing_hashes: set[str],
) -> float:
    score = 0.0
    if title and title.strip():
        score += 2
    if content_length >= 500:
        score += 2
    elif content_length >= 300:
        score += 1
    if published_at:
        score += 1
    if source_active:
        score += 1
    pw, li, cp = paywall_triplet
    if content_hash and content_hash not in existing_hashes:
        score += 1
    try:
        parsed = httpx.URL(url)
        if parsed.scheme and parsed.host:
            score += 1
    except Exception:
        pass
    if strategy != "manual_review":
        score += 1
    if raw_path and Path(raw_path).exists():
        score += 1

    if pw or li or cp:
        score -= 2
    if content_length < 300:
        score -= 2
    if not extract_ok:
        score -= 3

    return max(0.0, min(10.0, score))


def extract_article(
    url: str,
    source_id: str,
    strategy: str,
    *,
    rules: CrawlRules,
    raw_store: RawStore,
    client: httpx.Client,
    paywall_keywords: list[str] | None = None,
) -> ArticleResult:
    paywall_keywords = paywall_keywords or rules.paywall_keywords
    try:
        resp = client.get(url, timeout=rules.request_timeout_seconds, follow_redirects=True)
        status = resp.status_code
        html = resp.text if resp.content else ""
        if status >= 400:
            return ArticleResult(
                url=url,
                title=None,
                published_at=None,
                content=None,
                content_length=0,
                content_hash="",
                language=None,
                raw_path="",
                extract_ok=False,
                paywall_detected=False,
                login_detected=False,
                captcha_detected=False,
            )
    except Exception as exc:  # noqa: BLE001
        logger.debug("fetch article failed {}: {}", url, exc)
        return ArticleResult(
            url=url,
            title=None,
            published_at=None,
            content=None,
            content_length=0,
            content_hash="",
            language=None,
            raw_path="",
            extract_ok=False,
            paywall_detected=False,
            login_detected=False,
            captcha_detected=False,
        )

    lower = html.lower()
    paywall_detected = any(k.lower() in lower for k in rules.paywall_keywords)
    login_detected = any(k.lower() in lower for k in rules.login_keywords)
    captcha_detected = any(k.lower() in lower for k in rules.captcha_keywords)

    if paywall_detected or login_detected or captcha_detected:
        return ArticleResult(
            url=url,
            title=None,
            published_at=None,
            content=None,
            content_length=0,
            content_hash="",
            language=None,
            raw_path="",
            extract_ok=False,
            paywall_detected=paywall_detected,
            login_detected=login_detected,
            captcha_detected=captcha_detected,
        )

    raw_path = raw_store.save_html(source_id, html.encode("utf-8"))

    meta = trafilatura.extract_metadata(html)
    content = trafilatura.extract(html)
    title = meta.title if meta and meta.title else None
    pub = meta.date if meta and meta.date else None
    language = meta.language if meta and meta.language else None

    content = content or ""
    content_length = len(content.strip())
    content_hash = sha256_text(content) if content else ""

    return ArticleResult(
        url=url,
        title=title,
        published_at=str(pub) if pub else None,
        content=content if content else None,
        content_length=content_length,
        content_hash=content_hash,
        language=language,
        raw_path=raw_path,
        extract_ok=bool(content and content_length >= rules.min_article_content_length),
        paywall_detected=paywall_detected,
        login_detected=login_detected,
        captcha_detected=captcha_detected,
    )
