"""Load SourceProfiler rows from DuckDB for Scrapy runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

import duckdb

StrategyKey = Literal["rss", "sitemap", "html", "all"]

ALLOWED_STRATEGIES = {
    "rss_then_article_extract",
    "sitemap_then_article_extract",
    "html_then_trafilatura",
    "playwright_fallback",
}

SKIP_STRATEGIES = {
    "api_first",
    "metadata_only",
    "manual_review",
}


def domains_from_allowlist_file(path: Path | None) -> frozenset[str] | None:
    """Parse Leon Quant tier files: non-comment lines as URLs or bare hostnames.

    Returns ``None`` when path is None (no filtering). Empty frozenset if file missing/empty.
    """
    if path is None:
        return None
    if not path.is_file():
        return frozenset()
    domains: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        url = s if "://" in s else f"https://{s}"
        try:
            host = urlparse(url).netloc.lower()
        except Exception:
            continue
        if host.startswith("www."):
            host = host[4:]
        if host:
            domains.add(host)
    return frozenset(domains)


def _row_matches_allowlist(row: dict[str, Any], norm: dict[str, Any], allowed: frozenset[str]) -> bool:
    dom = str(row.get("domain") or "").lower().strip().strip(".")
    if not dom:
        h = str(norm.get("_homepage_url") or "").strip()
        if h:
            u = h if "://" in h else f"https://{h}"
            try:
                dom = urlparse(u).netloc.lower()
            except Exception:
                dom = ""
            if dom.startswith("www."):
                dom = dom[4:]
    if not dom:
        return False
    if dom in allowed:
        return True
    for a in allowed:
        if dom == a or dom.endswith("." + a):
            return True
    return False


def _parse_json_list(val: Any) -> list[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(x) for x in val if x]
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return []
        try:
            data = json.loads(s)
            if isinstance(data, list):
                return [str(x) for x in data if x]
        except json.JSONDecodeError:
            return []
    return []


def _row_allowed_status(row: dict[str, Any]) -> bool:
    st = row.get("status") or ""
    return st in ("active", "active_candidate")


def _robots_allows_html(row: dict[str, Any]) -> bool:
    v = row.get("robots_can_fetch_homepage")
    if v is None:
        return True
    return bool(v)


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    rss_urls = _parse_json_list(row.get("rss_urls"))
    sitemap_urls = _parse_json_list(row.get("sitemap_urls"))
    homepage = row.get("homepage_url") or row.get("normalized_url") or ""
    out = dict(row)
    out["_rss_urls"] = rss_urls
    out["_sitemap_urls"] = sitemap_urls
    out["_homepage_url"] = str(homepage).strip()
    out["_source_active"] = True
    return out


def fetch_crawl_skip_source_ids(db_path: Path) -> frozenset[str]:
    """Source IDs on the persistent uncrawlable list (``source_crawl_skip``)."""
    if not db_path.is_file():
        return frozenset()
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        rows = conn.execute("SELECT source_id FROM source_crawl_skip").fetchall()
    except duckdb.CatalogException:
        return frozenset()
    finally:
        conn.close()
    return frozenset(str(r[0]) for r in rows if r and r[0])


def load_sources_for_scrapy(
    db_path: Path,
    strategy: StrategyKey,
    limit: int,
    allowed_domains: frozenset[str] | None = None,
    exclude_source_ids: frozenset[str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Return sources bucketed by Scrapy lane (rss / sitemap / html).

    Profiles must already have ``best_strategy`` from SourceProfiler.
    """
    if not db_path.is_file():
        return {"rss": [], "sitemap": [], "html": []}

    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        df = conn.execute(
            """
            SELECT * FROM source_profiles
            WHERE status IN ('active', 'active_candidate')
            ORDER BY source_id
            """
        ).fetchdf()
    finally:
        conn.close()

    rows = df.to_dict("records") if not df.empty else []
    rss_out: list[dict[str, Any]] = []
    sitemap_out: list[dict[str, Any]] = []
    html_out: list[dict[str, Any]] = []

    skip_ids = exclude_source_ids or frozenset()

    for row in rows:
        if not _row_allowed_status(row):
            continue
        sid = str(row.get("source_id") or "")
        if sid and sid in skip_ids:
            continue
        strat = row.get("best_strategy") or ""
        if strat in SKIP_STRATEGIES or strat not in ALLOWED_STRATEGIES:
            continue
        norm = _normalize_row(row)
        if allowed_domains is not None and not _row_matches_allowlist(row, norm, allowed_domains):
            continue
        if strat == "rss_then_article_extract" and norm["_rss_urls"]:
            rss_out.append(norm)
        elif strat == "sitemap_then_article_extract" and norm["_sitemap_urls"]:
            sitemap_out.append(norm)
        elif strat == "html_then_trafilatura":
            if not _robots_allows_html(row):
                continue
            if norm["_homepage_url"]:
                html_out.append(norm)
        elif strat == "playwright_fallback":
            if norm["_rss_urls"]:
                rss_out.append(norm)
            elif norm["_sitemap_urls"]:
                sitemap_out.append(norm)
            elif norm["_homepage_url"] and _robots_allows_html(row):
                html_out.append(norm)

    def clip(xs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if limit <= 0:
            return xs
        return xs[:limit]

    buckets = {
        "rss": clip(rss_out),
        "sitemap": clip(sitemap_out),
        "html": clip(html_out),
    }

    if strategy == "all":
        return buckets
    if strategy == "rss":
        return {"rss": buckets["rss"], "sitemap": [], "html": []}
    if strategy == "sitemap":
        return {"rss": [], "sitemap": buckets["sitemap"], "html": []}
    if strategy == "html":
        return {"rss": [], "sitemap": [], "html": buckets["html"]}
    raise ValueError(f"unknown strategy {strategy!r}")
