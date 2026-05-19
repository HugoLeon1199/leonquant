"""Shared HTML checks + trafilatura extraction for Scrapy spiders/pipelines."""

from __future__ import annotations

import re

import trafilatura
from pydantic import BaseModel

from utils.hashing import sha256_text

# Gate phrases: block immediately if present in raw HTML (case-insensitive).
_STRONG_LOGIN_PHRASES = (
    "sign in to continue",
    "log in to continue",
    "login to continue",
)

_STRONG_PAYWALL_PHRASES = (
    "subscribe to continue",
    "subscribe to read",
    "register to read",
    "registration required",
    "subscribers only",
    "premium subscribers only",
    "premium subscribers",
    "paywall",
)

# Technical / bot walls — always block regardless of extracted length.
_CAPTCHA_HARD_MARKERS = (
    "verify you are human",
    "checking your browser",
    "just a moment...",
    "just a moment …",
    "cf-ray",
    "__cf_bm",
    "hcaptcha",
    "g-recaptcha",
    "/recaptcha/api.js",
    "recaptcha/api",
    "turnstile",
    "attention required",
    "enable javascript and cookies",
)


class ExtractOutcome(BaseModel):
    title: str | None = None
    published_at: str | None = None
    content: str | None = None
    content_length: int = 0
    content_hash: str = ""
    language: str | None = None


def _debloat_scripts_styles(html: str) -> str:
    t = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    t = re.sub(r"<noscript[^>]*>.*?</noscript>", " ", t, flags=re.DOTALL | re.IGNORECASE)
    t = re.sub(r"<style[^>]*>.*?</style>", " ", t, flags=re.DOTALL | re.IGNORECASE)
    return t


def visible_text_lower(html: str) -> str:
    """Lightweight main-visible-ish text for soft keyword counting (not perfect DOM)."""
    t = _debloat_scripts_styles(html)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\s+", " ", t).strip().lower()
    return t


def _keyword_hit_count(text_lower: str, keyword: str) -> int:
    kl = keyword.lower().strip()
    if not kl:
        return 0
    if " " in kl:
        n = 0
        start = 0
        while True:
            i = text_lower.find(kl, start)
            if i < 0:
                break
            n += 1
            start = i + len(kl)
        return n
    return len(re.findall(rf"\b{re.escape(kl)}\b", text_lower))


def _strict_bot_wall(html_lower: str) -> bool:
    """True only for bot/challenge pages — not generic 'captcha' in site chrome."""
    for m in _CAPTCHA_HARD_MARKERS:
        if m in html_lower:
            return True
    if "cloudflare" in html_lower and ("ray id" in html_lower or "cf-ray" in html_lower):
        return True
    return False


def _hard_denial_wall(html_lower: str) -> bool:
    return "access denied" in html_lower or "403 forbidden" in html_lower


def _strong_gate_wall(html_lower: str) -> tuple[bool, bool]:
    """Returns (paywall_signal, login_signal)."""
    login_hit = any(p in html_lower for p in _STRONG_LOGIN_PHRASES)
    pay_hit = any(p in html_lower for p in _STRONG_PAYWALL_PHRASES)
    return pay_hit, login_hit


def _all_strong_phrases_flat() -> frozenset[str]:
    return frozenset(_STRONG_LOGIN_PHRASES + _STRONG_PAYWALL_PHRASES)


def _soft_keyword_pressure(
    body_lower: str,
    visible_lower: str,
    paywall_keywords: list[str],
    login_keywords: list[str],
) -> tuple[int, bool]:
    """
    Soft hits: repeated chrome-like tokens on visible text, or any hit inside extracted body.
    Skips YAML entries that duplicate strong phrases (already handled).
    """
    strong_flat = _all_strong_phrases_flat()
    visible_total = 0
    body_hit = False
    for kw in list(paywall_keywords) + list(login_keywords):
        kl = kw.strip().lower()
        if not kl or kl in strong_flat:
            continue
        visible_total += _keyword_hit_count(visible_lower, kl)
        if _keyword_hit_count(body_lower, kl) > 0:
            body_hit = True
    return visible_total, body_hit


def access_control_triplet(
    html_text: str,
    paywall_keywords: list[str],
    login_keywords: list[str],
    captcha_keywords: list[str],
    *,
    extracted_plain: str,
    content_length: int,
    min_article_content_length: int,
    soft_repeat_threshold: int = 5,
) -> tuple[bool, bool, bool]:
    """
    Paywall/login/captcha gates for Scrapy pipeline.

    When trafilatura already produced a full article body, ignore YAML keyword lists
    (login/captcha/paywall in page chrome). RSS + extract success is the real signal.
    """
    _ = captcha_keywords  # YAML list not used — too many false positives on VN news sites.
    hl = html_text.lower()
    body_lower = (extracted_plain or "").lower()
    visible_lower = visible_text_lower(html_text)

    if content_length >= min_article_content_length:
        if _hard_denial_wall(hl):
            return True, False, False
        return False, False, False

    if _strict_bot_wall(hl):
        return False, False, True

    if _hard_denial_wall(hl):
        return True, False, False

    return False, False, False


def extract_with_trafilatura(html: str) -> ExtractOutcome:
    meta = trafilatura.extract_metadata(html)
    content = trafilatura.extract(html) or ""
    stripped = content.strip()
    title = meta.title if meta and meta.title else None
    pub = meta.date if meta and meta.date else None
    language = meta.language if meta and meta.language else None
    content_hash = sha256_text(stripped) if stripped else ""
    return ExtractOutcome(
        title=title,
        published_at=str(pub) if pub else None,
        content=stripped if stripped else None,
        content_length=len(stripped),
        content_hash=content_hash,
        language=language,
    )
