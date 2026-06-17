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
_GENERIC_EDITORIAL_PHRASES = (
    "cần theo dõi",
    "đáng chú ý",
    "điểm nóng",
    "bức tranh",
    "diễn biến phức tạp",
    "tác động lớn",
    "tiếp tục theo dõi",
)


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


def _norm_editorial_text(text: Any) -> str:
    raw = str(text or "").strip().lower()
    raw = re.sub(r"https?://\S+", " ", raw)
    raw = re.sub(r"[\W_]+", " ", raw, flags=re.UNICODE)
    return re.sub(r"\s+", " ", raw).strip()


def _looks_duplicateish(a: Any, b: Any) -> bool:
    na = _norm_editorial_text(a)
    nb = _norm_editorial_text(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    short, long = (na, nb) if len(na) <= len(nb) else (nb, na)
    if len(short) >= 24 and short in long:
        return True
    wa = set(na.split())
    wb = set(nb.split())
    if not wa or not wb:
        return False
    overlap = len(wa & wb) / max(1, min(len(wa), len(wb)))
    return overlap >= 0.82


def _is_generic_editorial_text(text: Any) -> bool:
    norm = _norm_editorial_text(text)
    if not norm:
        return True
    if len(norm) < 18:
        return True
    return any(phrase in norm for phrase in _GENERIC_EDITORIAL_PHRASES)


def _unique_nonempty_texts(*values: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        norm = _norm_editorial_text(text)
        if not text or not norm or norm in seen:
            continue
        seen.add(norm)
        out.append(text)
    return out


def _distinct_text(value: Any, *already_used: Any) -> str:
    """Return value's text only if it's non-empty and distinct from already_used.

    Unlike copying a sibling field as a fallback, this leaves the field blank
    when there's no genuinely different text, so build_website_content.py's
    render_style logic can fall back to a thinner layout instead of showing
    the same sentence three times.
    """
    text = str(value or "").strip()
    norm = _norm_editorial_text(text)
    if not text or not norm:
        return ""
    for other in already_used:
        other_norm = _norm_editorial_text(str(other or "").strip())
        if other_norm and other_norm == norm:
            return ""
    return text


def _front_page_row_is_publishable(row: dict[str, Any]) -> bool:
    title = str(row.get("title") or "").strip()
    why = str(row.get("why_it_matters") or "").strip()
    if not title or not why:
        return False
    one = str(row.get("one_sentence") or "").strip()
    watch = str(row.get("watch_next") or "").strip()
    if not one and not watch:
        return False
    if _is_generic_editorial_text(why):
        return False
    return True


def _dossier_is_publishable(row: dict[str, Any]) -> bool:
    title = str(row.get("title") or "").strip()
    why = str(row.get("why_it_matters") or "").strip()
    if not title or not why:
        return False
    devs = [str(x).strip() for x in (row.get("main_developments") or []) if str(x).strip()]
    if not devs:
        return False
    watch_lines = [str(x).strip() for x in (row.get("watch_next") or []) if str(x).strip()]
    if watch_lines and any(_looks_duplicateish(why, line) for line in watch_lines):
        return False
    return True


def _watchlist_row(theme: str, what: str, why: str) -> dict[str, str] | None:
    theme = str(theme or "").strip()
    what = str(what or "").strip()
    why = str(why or "").strip()
    if not theme or not what or not why:
        return None
    return {"theme": theme[:120], "what_to_watch": what[:220], "why": why[:280]}


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
    publishable_front: list[dict[str, Any]] = []
    for row in front:
        if not _front_page_row_is_publishable(row):
            continue
        row_copy = dict(row)
        row_copy["source_urls"] = [str(u).strip() for u in (row_copy.get("source_urls") or []) if str(u).strip()][:3]
        row_copy["one_sentence"] = str(row_copy.get("one_sentence") or "").strip()
        row_copy["why_it_matters"] = _distinct_text(
            row_copy.get("why_it_matters"), row_copy.get("one_sentence")
        )
        row_copy["watch_next"] = _distinct_text(
            row_copy.get("watch_next"),
            row_copy.get("why_it_matters"),
            row_copy.get("one_sentence"),
        )
        publishable_front.append(row_copy)
    for idx, row in enumerate(publishable_front[:12], start=1):
        row["rank"] = idx
    out["front_page"] = publishable_front[:12]

    norm_sectors: list[dict[str, Any]] = []
    existing_watchlist = [
        row for row in (out.get("watchlist_24_72h") or []) if isinstance(row, dict)
    ]
    carry_watchlist: list[dict[str, str]] = []
    for sec in out.get("sector_deep_briefs") or []:
        if not isinstance(sec, dict):
            continue
        sec_copy = dict(sec)
        sec_name = str(sec_copy.get("name") or sec_copy.get("code") or "Lĩnh vực").strip()
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
            sd["representative_sources"] = srcs
            if not _track_cluster(sd):
                continue
            if not _dossier_is_publishable(sd):
                watch_text = ", ".join(
                    str(x).strip() for x in (sd.get("watch_next") or []) if str(x).strip()
                )
                why = str(sd.get("why_it_matters") or "").strip() or watch_text
                moved = _watchlist_row(sec_name, watch_text or title, why or watch_text)
                if moved:
                    carry_watchlist.append(moved)
                continue
            dossiers.append(sd)
        dossiers = dedupe_rows_by_story_cluster(dossiers)
        dossiers.sort(key=lambda r: _freshness_sort_key(r, url_index))
        for idx, dossier in enumerate(dossiers[:12], start=1):
            dossier["rank"] = idx
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

    watchlist: list[dict[str, str]] = []
    for row in existing_watchlist:
        item = _watchlist_row(
            row.get("theme"),
            row.get("what_to_watch"),
            row.get("why"),
        )
        if item:
            watchlist.append(item)
    watchlist.extend(carry_watchlist)
    deduped_watch: list[dict[str, str]] = []
    seen_watch: set[str] = set()
    for row in watchlist:
        key = _norm_editorial_text(" ".join((row.get("theme", ""), row.get("what_to_watch", ""))))
        if not key or key in seen_watch:
            continue
        seen_watch.add(key)
        deduped_watch.append(row)
    out["watchlist_24_72h"] = deduped_watch[:10]

    eb = out.get("executive_briefing") if isinstance(out.get("executive_briefing"), dict) else {}
    eb_sources = filter_representative_sources(
        [x for x in (eb.get("representative_sources") or []) if isinstance(x, dict)],
        url_index=url_index,
    )
    if not eb_sources:
        fallback_sources: list[dict[str, Any]] = []
        for row in out.get("front_page") or []:
            title = str(row.get("title") or "").strip()
            for u in row.get("source_urls") or []:
                fallback_sources.append({"url": u, "title": title})
        for sec in out.get("sector_deep_briefs") or []:
            for d in sec.get("story_dossiers") or []:
                fallback_sources.extend(d.get("representative_sources") or [])
        eb_sources = filter_representative_sources(fallback_sources, url_index=url_index)
    if isinstance(eb, dict):
        eb_copy = dict(eb)
        eb_copy["representative_sources"] = eb_sources[:5]
        out["executive_briefing"] = eb_copy

    return out
