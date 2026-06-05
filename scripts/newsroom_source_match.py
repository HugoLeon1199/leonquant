#!/usr/bin/env python3
"""Strict story ↔ article source matching for newsroom brief (no wrong URL fallback)."""

from __future__ import annotations

import re
import sys
from difflib import SequenceMatcher
from typing import Any
from urllib.parse import urlparse

# Import DigestUrlIndex from parent package when run as script
def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "").strip().lower())


def _title_tokens(text: str) -> set[str]:
    return set(re.findall(r"[\wàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]{4,}", _norm(text), re.I))


def story_profile(headline: str, *, context: str = "") -> dict[str, Any]:
    """Topic guards derived from public headline (+ optional one_sentence)."""
    blob = _norm(f"{headline} {context}")
    profile: dict[str, Any] = {
        "headline": headline,
        "required_title_any": [],
        "forbidden_title": [],
        "min_score": 0.40,
    }

    tphcm_specific = bool(
        re.search(r"tp\.?\s*hcm|tp hcm|thành phố hồ chí minh|hồ chí minh.*bđs|28\s*dự", blob)
    )
    cantho_specific = bool(re.search(r"cần thơ|can thơ", blob))
    crypto_ai = bool(
        re.search(
            r"crypto|bitcoin|btc|coin|cổ phiếu ai|ai stock|nhóm ai|microsoft|nvidia|alphabet|"
            r"dòng vốn.*crypto|crypto.*cổ",
            blob,
        )
    )
    iran_energy = bool(re.search(r"iran|qeshm|tehran|hormuz|dầu|vùng vịnh", blob))
    e10 = bool(re.search(r"e10|xăng e10", blob))

    if crypto_ai:
        profile["required_title_any"] = [
            "bitcoin",
            "btc",
            "crypto",
            "coin",
            "nvidia",
            "microsoft",
            "alphabet",
            "google",
            "etf",
            "chứng khoán",
            "công nghệ",
            "ai ",
            "máy tính",
        ]
        profile["forbidden_title"] = [
            "đất đai",
            "tái tạo sinh kế",
            "sinh kế",
            "can thơ",
            "cần thơ",
            "hạ tầng đất",
            "nông sản",
        ]
        profile["min_score"] = 0.38

    if tphcm_specific and not re.search(r"địa phương|nhiều (tỉnh|địa)|toàn quốc", blob):
        profile["required_title_any"] = profile.get("required_title_any") or [
            "tp.hcm",
            "tp hcm",
            "hồ chí minh",
            "tphcm",
            "28 dự",
            "28 dự án",
        ]
        profile["forbidden_title"] = list(
            dict.fromkeys(
                (profile.get("forbidden_title") or [])
                + ["cần thơ", "can thơ", "cần-thơ"]
            )
        )
        profile["min_score"] = max(profile["min_score"], 0.42)

    if cantho_specific:
        profile["required_title_any"] = ["cần thơ", "can thơ", "cần-thơ"]
        profile["forbidden_title"] = (profile.get("forbidden_title") or []) + [
            "tp.hcm",
            "hồ chí minh",
            "28 dự",
        ]
        profile["min_score"] = max(profile["min_score"], 0.42)

    if re.search(r"bất động sản|bđs|dự án", blob) and not tphcm_specific and not cantho_specific:
        profile["required_title_any"] = profile.get("required_title_any") or [
            "bất động sản",
            "bđs",
            "dự án",
            "pháp lý",
        ]
        profile["min_score"] = max(profile["min_score"], 0.36)

    if iran_energy:
        profile["required_title_any"] = profile.get("required_title_any") or [
            "iran",
            "tehran",
            "qeshm",
            "dầu",
            "hormuz",
            "mỹ",
            "trump",
        ]
        profile["forbidden_title"] = (profile.get("forbidden_title") or []) + [
            "e10",
            "xăng",
            "cần thơ",
        ]

    if e10:
        profile["required_title_any"] = profile.get("required_title_any") or [
            "e10",
            "xăng",
            "nhiên liệu",
        ]

    return profile


def _forbidden_hit(title_low: str, forbidden: list[str]) -> bool:
    return any(p in title_low for p in forbidden if p)


def score_article_for_story(art: dict[str, Any], headline: str, *, context: str = "") -> float:
    title = str(art.get("title") or "")
    if not title.strip():
        return 0.0
    hl = _norm(headline)
    title_low = _norm(title)
    if not hl:
        return 0.0
    prof = story_profile(headline, context=context)
    if _forbidden_hit(title_low, prof.get("forbidden_title") or []):
        return 0.0
    req_any = prof.get("required_title_any") or []
    if req_any and not any(k in title_low for k in req_any):
        return 0.0
    title_sc = SequenceMatcher(None, hl, title_low).ratio()
    hl_t = _title_tokens(hl)
    art_t = _title_tokens(title)
    overlap = len(hl_t & art_t) / max(1, len(hl_t)) if hl_t else 0.0
    text = str(art.get("content_for_ai") or art.get("text") or "")[:400].lower()
    blob_bonus = 0.08 if any(t in text for t in hl_t if len(t) >= 5) else 0.0
    topic_bonus = 0.0
    if req_any and any(k in title_low for k in req_any if k.strip()):
        topic_bonus = 0.44
    ctx_low = _norm(context)
    if prof.get("required_title_any") and ctx_low:
        ctx_hits = sum(1 for k in req_any if k in ctx_low or k in title_low)
        if ctx_hits >= 2:
            topic_bonus = max(topic_bonus, 0.46)
    return min(1.0, max(title_sc, overlap * 0.85, topic_bonus) + blob_bonus)


def article_matches_story(
    art: dict[str, Any],
    headline: str,
    *,
    context: str = "",
    min_score: float | None = None,
) -> bool:
    prof = story_profile(headline, context=context)
    floor = min_score if min_score is not None else prof.get("min_score", 0.40)
    return score_article_for_story(art, headline, context=context) >= floor


def filter_urls_for_story(
    urls: list[str],
    headline: str,
    index: Any,
    *,
    context: str = "",
    sector_code: str = "",
) -> list[str]:
    """Keep only whitelist URLs whose crawled article matches the story."""
    if index is None or not getattr(index, "active", False):
        return [u for u in urls if str(u).strip().startswith("http")][:3]

    from summarize_news_gemini import _canonical_digest_url, _resolve_digest_url_by_path

    prof = story_profile(headline, context=context)
    min_sc = prof.get("min_score", 0.40)
    out: list[str] = []
    seen: set[str] = set()
    hl = str(headline or "").strip()

    for raw in urls:
        raw_c = _canonical_digest_url(str(raw))
        if not raw_c:
            continue
        u = raw_c if raw_c in index.allowed else ""
        if not u:
            u = _resolve_digest_url_by_path(raw_c, hl, index) or ""
        if not u or u in seen:
            continue
        art = index.by_url.get(u)
        if not art or not article_matches_story(art, hl, context=context, min_score=min_sc):
            continue
        seen.add(u)
        out.append(u)
        if len(out) >= 3:
            break
    return out


def sanitize_representative_sources(
    sources: Any,
    *,
    headline: str,
    index: Any,
    sector_code: str = "",
    context: str = "",
) -> list[dict[str, str]]:
    rows = sources if isinstance(sources, list) else []
    excerpt_by_url: dict[str, str] = {}
    raw_urls: list[str] = []
    for row in rows:
        if isinstance(row, dict) and str(row.get("url") or "").strip():
            u = str(row.get("url") or "").strip()
            raw_urls.append(u)
            ex = str(row.get("excerpt") or "").strip()
            if ex:
                excerpt_by_url[u] = ex
    valid = filter_urls_for_story(
        raw_urls, headline, index, context=context, sector_code=sector_code
    )
    out: list[dict[str, str]] = []
    for u in valid:
        art = index.by_url.get(u) if index and index.active else None
        title = str((art or {}).get("title") or "").strip()
        src = str((art or {}).get("source") or "").strip()
        item: dict[str, str] = {"title": title or u, "source": src, "url": u}
        if excerpt_by_url.get(u):
            item["excerpt"] = excerpt_by_url[u]
        out.append(item)
        if len(out) >= 5:
            break
    return out


def sanitize_front_page_sources(
    source_urls: list[str],
    *,
    headline: str,
    index: Any,
    context: str = "",
) -> list[str]:
    return filter_urls_for_story(
        [str(u).strip() for u in source_urls if str(u).strip()],
        headline,
        index,
        context=context,
    )
