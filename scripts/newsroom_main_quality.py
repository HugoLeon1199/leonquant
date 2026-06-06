#!/usr/bin/env python3
"""Tin48h main editorial quality — filters/dedupe for briefing output (not full archive)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

STORY_CLUSTER_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "fed_warsh",
        re.compile(
            r"kevin\s*warsh|warsh.*fed|fed.*warsh|chủ\s*tịch\s*fed|"
            r"fed\s*chair|chair.*fed|federal\s*reserve|cục\s*dự\s*trữ\s*liên\s*bang|\bfed\b.*lãi\s*suất",
            re.I,
        ),
    ),
    (
        "spacex_ipo",
        re.compile(
            r"spacex|starship|starlink.*ipo|ipo.*spacex|"
            r"hàng\s*không\s*vũ\s*trụ.*musk|musk.*spacex",
            re.I,
        ),
    ),
    (
        "us_iran",
        re.compile(
            r"iran|qeshm|tehran|hormuz|vùng\s*vịnh|trump.*iran|"
            r"đàm\s*phán.*iran|sức\s*ép.*iran",
            re.I,
        ),
    ),
)

_BAD_MAIN_TITLE_RE = re.compile(
    r"page\s+not\s+found|404\s+not\s+found|^nan$|^none$|^null$|untitled",
    re.I,
)
_BAD_MAIN_URL_PATH_RE = re.compile(
    r"/(?:category|categories|tag|tags|topic|topics|section|sections|archive|search|"
    r"coupon|promo|listing|listings)(?:/|$)|"
    r"/page-not-found|/404(?:/|$)|/not-found",
    re.I,
)
_SPAM_URL_RE = re.compile(
    r"coupon|/promo/|/deals/|/sale/|/reviews?/|utm_campaign=.*deal|/subscribe(?:/|$)",
    re.I,
)
_CATEGORY_ONLY_SEGMENTS = frozenset(
    {"news", "business", "world", "tech", "finance", "markets", "economy", "politics"}
)

MAIN_FRESHNESS_HOURS = 48.0


def story_cluster_key(*texts: str) -> str | None:
    blob = " ".join(str(t or "") for t in texts if str(t or "").strip()).lower()
    if not blob:
        return None
    for key, pat in STORY_CLUSTER_PATTERNS:
        if pat.search(blob):
            return key
    return None


def is_bad_main_editorial_title(title: str) -> bool:
    t = str(title or "").strip()
    if not t:
        return True
    if _BAD_MAIN_TITLE_RE.search(t):
        return True
    low = t.lower()
    if low in ("nan", "none", "null", "untitled", "page not found"):
        return True
    return False


def is_bad_main_editorial_url(url: str, *, title: str = "") -> bool:
    u = str(url or "").strip()
    if not u.startswith("http"):
        return True
    if is_bad_main_editorial_title(title):
        return True
    if _SPAM_URL_RE.search(u):
        return True
    try:
        p = urlparse(u)
    except ValueError:
        return True
    path = (p.path or "").lower()
    if _BAD_MAIN_URL_PATH_RE.search(path):
        return True
    segs = [s for s in path.split("/") if s]
    if len(segs) == 1 and segs[0] in _CATEGORY_ONLY_SEGMENTS:
        return True
    if len(segs) <= 1 and not re.search(r"\d{5,}|\.htm|/20\d{2}/", path):
        if path.rstrip("/") in {"/news", "/business", "/world", "/tech", "/finance"}:
            return True
    return False


def _parse_published_hours_ago(art: dict[str, Any] | None) -> float | None:
    if not isinstance(art, dict):
        return None
    raw = str(art.get("published_at") or art.get("publishedAt") or "").strip()
    if not raw or raw.lower() in ("nan", "none", "null"):
        return None
    try:
        if "T" in raw:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        elif len(raw) >= 10:
            dt = datetime.fromisoformat(raw[:10] + "T12:00:00+00:00")
        else:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt.astimezone(timezone.utc)
        return max(0.0, delta.total_seconds() / 3600.0)
    except (TypeError, ValueError, OverflowError):
        return None


def is_fresh_main_article(art: dict[str, Any] | None, *, window_hours: float = MAIN_FRESHNESS_HOURS) -> bool:
    hours = _parse_published_hours_ago(art)
    if hours is None:
        return True
    return hours <= window_hours


def row_editorial_rank(row: dict[str, Any]) -> int:
    for field in ("rank", "importance_rank", "importance"):
        raw = row.get(field)
        if raw is None or raw == "":
            continue
        try:
            return int(raw)
        except (TypeError, ValueError):
            continue
    return 999


def dedupe_rows_by_story_cluster(
    rows: list[dict[str, Any]],
    *,
    title_key: str = "title",
    extra_keys: tuple[str, ...] = ("summary", "one_sentence"),
) -> list[dict[str, Any]]:
    """Keep best-ranked row per story cluster; unclustered rows pass through."""
    ranked = sorted(rows, key=row_editorial_rank)
    seen_clusters: set[str] = set()
    kept: list[dict[str, Any]] = []
    for row in ranked:
        if not isinstance(row, dict):
            continue
        title = str(row.get(title_key) or "")
        extra = " ".join(str(row.get(k) or "") for k in extra_keys)
        ck = story_cluster_key(title, extra)
        if ck:
            if ck in seen_clusters:
                continue
            seen_clusters.add(ck)
        kept.append(row)
    kept.sort(key=row_editorial_rank)
    return kept


def filter_representative_sources(
    sources: list[dict[str, Any]],
    *,
    url_index: Any = None,
) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for src in sources:
        if not isinstance(src, dict):
            continue
        u = str(src.get("url") or "").strip()
        title = str(src.get("title") or "").strip()
        if not u or is_bad_main_editorial_url(u, title=title):
            continue
        art = None
        if url_index is not None and getattr(url_index, "active", False):
            art = url_index.by_url.get(u) or url_index.by_url.get(u.rstrip("/"))
            crawl_title = str((art or {}).get("title") or "").strip()
            if crawl_title and is_bad_main_editorial_title(crawl_title):
                continue
        out.append(
            {
                "title": title or str((art or {}).get("title") or u),
                "source": str(src.get("source") or (art or {}).get("source") or ""),
                "url": u,
                **({"excerpt": str(src.get("excerpt") or "").strip()} if src.get("excerpt") else {}),
            }
        )
        if len(out) >= 5:
            break
    return out


def _article_from_index(url_index: Any, url: str) -> dict[str, Any] | None:
    if url_index is None or not getattr(url_index, "active", False):
        return None
    u = str(url or "").strip().rstrip("/")
    if not u:
        return None
    art = url_index.by_url.get(u)
    if art:
        return art
    return url_index.by_url.get(u + "/")


def _freshness_sort_key(row: dict[str, Any], url_index: Any | None) -> tuple[int, float]:
    rank = row_editorial_rank(row)
    best_hours = 9999.0
    urls: list[str] = []
    for u in row.get("source_urls") or []:
        urls.append(str(u).strip())
    for src in row.get("representative_sources") or []:
        if isinstance(src, dict):
            urls.append(str(src.get("url") or "").strip())
    urls.append(str(row.get("url") or "").strip())
    for u in urls:
        if not u:
            continue
        hours = _parse_published_hours_ago(_article_from_index(url_index, u))
        if hours is not None:
            best_hours = min(best_hours, hours)
    return (rank, best_hours)


def enforce_newsroom_main_editorial_quality(
    summary: dict[str, Any],
    *,
    url_index: Any = None,
) -> dict[str, Any]:
    """Hygiene for main Tin48h editorial fields only — does not touch archive/article pools."""
    out = dict(summary)
    global_clusters: set[str] = set()

    def _track_cluster(row: dict[str, Any], *, title_key: str = "title") -> bool:
        title = str(row.get(title_key) or "")
        extra = " ".join(
            str(row.get(k) or "")
            for k in ("summary", "one_sentence", "why_it_matters", "why_notable")
        )
        ck = story_cluster_key(title, extra)
        if not ck:
            return True
        if ck in global_clusters:
            return False
        global_clusters.add(ck)
        return True

    front: list[dict[str, Any]] = []
    for row in out.get("front_page") or []:
        if not isinstance(row, dict):
            continue
        title = str(row.get("title") or "").strip()
        if is_bad_main_editorial_title(title):
            continue
        urls = [
            u
            for u in (row.get("source_urls") or [])
            if str(u).strip() and not is_bad_main_editorial_url(str(u), title=title)
        ]
        row = dict(row)
        row["source_urls"] = urls
        if not _track_cluster(row):
            continue
        front.append(row)
    front = dedupe_rows_by_story_cluster(front, extra_keys=("one_sentence", "why_it_matters"))
    front.sort(key=lambda r: _freshness_sort_key(r, url_index))
    out["front_page"] = front[:12]

    norm_sectors: list[dict[str, Any]] = []
    for sec in out.get("sector_deep_briefs") or []:
        if not isinstance(sec, dict):
            continue
        sec_copy = dict(sec)
        dossiers: list[dict[str, Any]] = []
        for d in sec.get("story_dossiers") or []:
            if not isinstance(d, dict):
                continue
            title = str(d.get("title") or "").strip()
            if is_bad_main_editorial_title(title):
                continue
            sd = dict(d)
            srcs = filter_representative_sources(
                [x for x in (sd.get("representative_sources") or []) if isinstance(x, dict)],
                url_index=url_index,
            )
            if not srcs:
                continue
            sd["representative_sources"] = srcs
            if not _track_cluster(sd):
                continue
            dossiers.append(sd)
        dossiers = dedupe_rows_by_story_cluster(dossiers)
        dossiers.sort(key=lambda r: _freshness_sort_key(r, url_index))
        sec_copy["story_dossiers"] = dossiers
        norm_sectors.append(sec_copy)
    out["sector_deep_briefs"] = norm_sectors

    notable: list[dict[str, Any]] = []
    for row in out.get("notable_articles") or []:
        if not isinstance(row, dict):
            continue
        title = str(row.get("title") or "").strip()
        u = str(row.get("url") or "").strip()
        if is_bad_main_editorial_title(title):
            continue
        if u and is_bad_main_editorial_url(u, title=title):
            continue
        if not _track_cluster(row):
            continue
        notable.append(dict(row))
    out["notable_articles"] = dedupe_rows_by_story_cluster(
        notable, extra_keys=("why_notable",)
    )[:12]

    return out
