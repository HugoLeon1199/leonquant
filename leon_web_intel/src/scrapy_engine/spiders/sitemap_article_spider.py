from __future__ import annotations

import gzip
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import scrapy

from scrapy_engine.items import ArticleItem
from utils.today_filter import (
    is_datetime_in_range,
    is_url_likely_recent_calendar_days,
    parse_any_datetime,
    resolve_calendar_date,
    target_recent_calendar_days_range,
)


def _local(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _sitemap_discovery_priority(url: str) -> tuple[int, str]:
    """Lower tuple sorts first: prefer news/google sitemaps over decade archives."""
    lower = (url or "").lower()
    if any(k in lower for k in ("news-sitemap", "sitemap-news", "google-news", "sitemap_news", "latest-articles")):
        return (0, lower)
    if any(k in lower for k in ("/news-", "/news/", "articles/2026", "articles/2025", "news-2026", "news-2025")):
        return (1, lower)
    if any(k in lower for k in ("sitemap_index", "sitemap.xml", "sitemaps.xml")):
        return (2, lower)
    return (3, lower)


def _iter_locs(body: bytes) -> list[str]:
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return []
    out: list[str] = []
    for el in root.iter():
        if _local(el.tag or "").lower() == "loc" and el.text:
            u = el.text.strip()
            if u:
                out.append(u)
    return out


def _iter_sitemap_pairs(body: bytes) -> list[tuple[str, str | None]]:
    """``(loc, lastmod)`` pairs from urlset or sitemap index."""
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return []
    out: list[tuple[str, str | None]] = []
    root_name = _local(root.tag or "").lower()

    if root_name == "sitemapindex":
        for el in root:
            if _local(el.tag).lower() != "sitemap":
                continue
            loc = None
            lm = None
            for ch in el:
                ln = _local(ch.tag).lower()
                if ln == "loc" and ch.text:
                    loc = ch.text.strip()
                elif ln == "lastmod" and ch.text:
                    lm = ch.text.strip()
            if loc:
                out.append((loc, lm))
        return out

    for el in root.iter():
        if _local(el.tag).lower() != "url":
            continue
        loc = None
        lm = None
        for ch in el:
            ln = _local(ch.tag).lower()
            if ln == "loc" and ch.text:
                loc = ch.text.strip()
            elif ln == "lastmod" and ch.text:
                lm = ch.text.strip()
        if loc:
            out.append((loc, lm))

    if not out:
        return [(u, None) for u in _iter_locs(body)]
    return out


def _maybe_decompress(response: scrapy.http.Response) -> bytes:
    body = response.body
    url = (response.url or "").lower()
    if url.endswith(".gz") or response.headers.get("Content-Type", b"").decode("latin-1", errors="ignore").find("gzip") >= 0:
        try:
            return gzip.decompress(body)
        except Exception:  # noqa: BLE001
            return body
    return body


def _sitemap_root_is_index(body: bytes) -> bool:
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return False
    return _local(root.tag or "").lower() == "sitemapindex"


class SitemapArticleSpider(scrapy.Spider):
    """Production lane for ``sitemap_then_article_extract`` profiles."""

    name = "sitemap_article"

    @classmethod
    def from_crawler(cls, crawler: Any, *args: Any, **kwargs: Any) -> scrapy.Spider:
        kwargs2 = dict(kwargs)
        kwargs2.setdefault(
            "max_index_children",
            int(crawler.settings.getint("WEB_INTEL_SITEMAP_MAX_INDEX_CHILDREN", 5)),
        )
        kwargs2.setdefault(
            "max_xml_per_source",
            int(crawler.settings.getint("WEB_INTEL_SITEMAP_MAX_XML_PER_SOURCE", 20)),
        )
        kwargs2.setdefault(
            "recent_calendar_days",
            max(1, int(crawler.settings.getint("WEB_INTEL_RECENT_CALENDAR_DAYS", 2))),
        )
        return super().from_crawler(crawler, *args, **kwargs2)

    def __init__(
        self,
        sources: list[dict[str, Any]] | None = None,
        max_articles_per_source: int = 5,
        summary: Any | None = None,
        crawl_strategy: str = "sitemap_then_article_extract",
        max_sitemap_nested: int = 3,
        today_only: bool = False,
        target_date: str | None = None,
        timezone: str = "Asia/Ho_Chi_Minh",
        max_urls_per_source: int = 1000,
        max_index_children: int = 5,
        max_xml_per_source: int = 20,
        recent_calendar_days: int = 2,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.sources = sources or []
        self.max_articles_per_source = int(max_articles_per_source)
        self.summary = summary
        self.crawl_strategy = crawl_strategy
        self.max_sitemap_nested = int(max_sitemap_nested)
        self.today_only = bool(today_only)
        self.target_date_str = target_date
        self.timezone_str = str(timezone or "Asia/Ho_Chi_Minh")
        self.max_urls_per_source = int(max_urls_per_source)
        self.max_index_children = max(0, int(max_index_children))
        self.max_xml_per_source = int(max_xml_per_source)
        self.recent_calendar_days = max(1, int(recent_calendar_days))
        self._reserved: dict[str, int] = {}
        self._sitemap_xml_scheduled: dict[str, int] = {}

    def _take_sitemap_xml_budget(self, sid: str) -> bool:
        if self.max_xml_per_source <= 0:
            return True
        n = self._sitemap_xml_scheduled.get(sid, 0)
        if n >= self.max_xml_per_source:
            return False
        self._sitemap_xml_scheduled[sid] = n + 1
        return True

    def _sched(self, n: int = 1) -> None:
        if self.summary:
            with self.summary.lock:
                self.summary.requests_scheduled += n

    def _cap_for_source(self, sid: str) -> int:
        if self.today_only:
            return self.max_urls_per_source
        return self.max_articles_per_source

    def start_requests(self) -> Any:
        for row in self.sources:
            sid = row["source_id"]
            self._reserved.setdefault(sid, 0)
            active = row.get("_source_active", True)
            domain_host = urlparse(row.get("_homepage_url") or "").netloc.lower()
            sm_urls = sorted(row["_sitemap_urls"], key=_sitemap_discovery_priority)
            for sm_url in sm_urls:
                if not self._take_sitemap_xml_budget(sid):
                    break
                self._sched(1)
                yield scrapy.Request(
                    sm_url,
                    callback=self.parse_sitemap,
                    errback=self.errback,
                    meta={
                        "source_id": sid,
                        "source_active": active,
                        "nested_depth": 0,
                        "domain_host": domain_host,
                    },
                    dont_filter=False,
                )

    def _looks_like_sitemap_url(self, url: str) -> bool:
        lower = url.lower()
        return lower.endswith(".xml") or lower.endswith(".xml.gz") or "sitemap" in lower

    def parse_sitemap(self, response: scrapy.http.Response) -> Any:
        sid = response.meta["source_id"]
        active = response.meta.get("source_active", True)
        nested = int(response.meta.get("nested_depth", 0))
        domain_host = (response.meta.get("domain_host") or "").lower()

        raw = _maybe_decompress(response)
        pairs = _iter_sitemap_pairs(raw)
        remaining = self._cap_for_source(sid) - self._reserved.get(sid, 0)
        if remaining <= 0:
            return

        is_index = _sitemap_root_is_index(raw) and nested < self.max_sitemap_nested

        if is_index and not self.today_only:
            nested_meta: list[dict[str, Any]] = []
            for loc, lastmod in pairs:
                parsed = urlparse(loc)
                child_host = parsed.netloc.lower()
                if domain_host and child_host and child_host != domain_host:
                    continue
                if not self._looks_like_sitemap_url(loc):
                    continue
                nested_meta.append(
                    {
                        "loc": loc,
                        "depth": nested + 1,
                        "domain_host": domain_host or child_host,
                        "lastmod": lastmod,
                    }
                )

            def _nm_ts(nm: dict[str, Any]) -> float:
                lm = nm.get("lastmod")
                dt = parse_any_datetime(lm) if lm else None
                return dt.timestamp() if dt else float("-inf")

            nested_meta.sort(key=_nm_ts, reverse=True)
            cap_ch = self.max_index_children if self.max_index_children > 0 else len(nested_meta)
            for nm in nested_meta[:cap_ch]:
                if not self._take_sitemap_xml_budget(sid):
                    break
                self._sched(1)
                yield scrapy.Request(
                    nm["loc"],
                    callback=self.parse_sitemap,
                    errback=self.errback,
                    meta={
                        "source_id": sid,
                        "source_active": active,
                        "nested_depth": nm["depth"],
                        "domain_host": nm["domain_host"],
                    },
                    dont_filter=False,
                )
            return

        if self.today_only:
            target_d = resolve_calendar_date(self.target_date_str, self.timezone_str)
            start_utc, end_utc = target_recent_calendar_days_range(
                self.target_date_str, self.timezone_str, self.recent_calendar_days
            )
            nested_meta_t: list[dict[str, Any]] = []
            on_day: list[tuple[float, str, str | None]] = []
            other_day: list[tuple[float, str, str | None]] = []

            for loc, lastmod in pairs:
                parsed = urlparse(loc)
                child_host = parsed.netloc.lower()
                if domain_host and child_host and child_host != domain_host:
                    continue

                if self._looks_like_sitemap_url(loc) and nested < self.max_sitemap_nested:
                    nested_meta_t.append(
                        {
                            "loc": loc,
                            "depth": nested + 1,
                            "domain_host": domain_host or child_host,
                            "lastmod": lastmod,
                        }
                    )
                    continue

                if not loc.startswith("http"):
                    continue

                cand_raw = lastmod
                lm_dt = parse_any_datetime(lastmod) if lastmod else None
                sort_ts = lm_dt.timestamp() if lm_dt else float("-inf")
                if sort_ts == float("-inf") and is_url_likely_recent_calendar_days(loc, target_d, self.recent_calendar_days):
                    sort_ts = float("inf")
                row_t = (sort_ts, loc, cand_raw)
                if lm_dt and is_datetime_in_range(lm_dt, start_utc, end_utc):
                    on_day.append(row_t)
                elif is_url_likely_recent_calendar_days(loc, target_d, self.recent_calendar_days):
                    on_day.append(row_t)
                else:
                    other_day.append(row_t)

            def _nm_lastmod_ts(nm: dict[str, Any]) -> float:
                lm = nm.get("lastmod")
                dt = parse_any_datetime(lm) if lm else None
                return dt.timestamp() if dt else float("-inf")

            nested_meta_t.sort(
                key=lambda nm: (_sitemap_discovery_priority(str(nm.get("loc") or "")), -_nm_lastmod_ts(nm))
            )
            cap_ch2 = self.max_index_children if self.max_index_children > 0 else len(nested_meta_t)
            for nm in nested_meta_t[:cap_ch2]:
                if not self._take_sitemap_xml_budget(sid):
                    break
                self._sched(1)
                yield scrapy.Request(
                    nm["loc"],
                    callback=self.parse_sitemap,
                    errback=self.errback,
                    meta={
                        "source_id": sid,
                        "source_active": active,
                        "nested_depth": nm["depth"],
                        "domain_host": nm["domain_host"],
                    },
                    dont_filter=False,
                )

            on_day.sort(key=lambda r: r[0], reverse=True)
            leaf_rows = on_day
            cap_left = self._cap_for_source(sid) - self._reserved.get(sid, 0)
            for _, loc, cand_raw in leaf_rows[: max(0, cap_left)]:
                self._reserved[sid] = self._reserved.get(sid, 0) + 1
                self._sched(1)
                meta = {"source_id": sid, "source_active": active, "candidate_published_at": cand_raw}
                yield scrapy.Request(
                    loc,
                    callback=self.parse_article,
                    errback=self.errback,
                    meta=meta,
                    dont_filter=False,
                )
            return

        for loc, lastmod in pairs:
            if self._reserved.get(sid, 0) >= self._cap_for_source(sid):
                break
            parsed = urlparse(loc)
            child_host = parsed.netloc.lower()
            if domain_host and child_host and child_host != domain_host:
                continue

            if self._looks_like_sitemap_url(loc) and nested < self.max_sitemap_nested:
                if not self._take_sitemap_xml_budget(sid):
                    continue
                self._sched(1)
                yield scrapy.Request(
                    loc,
                    callback=self.parse_sitemap,
                    errback=self.errback,
                    meta={
                        "source_id": sid,
                        "source_active": active,
                        "nested_depth": nested + 1,
                        "domain_host": domain_host or child_host,
                    },
                    dont_filter=False,
                )
                continue

            if not loc.startswith("http"):
                continue

            cand_raw = lastmod
            lm_dt = parse_any_datetime(lastmod) if lastmod else None

            self._reserved[sid] = self._reserved.get(sid, 0) + 1
            self._sched(1)
            meta = {"source_id": sid, "source_active": active, "candidate_published_at": cand_raw}
            yield scrapy.Request(
                loc,
                callback=self.parse_article,
                errback=self.errback,
                meta=meta,
                dont_filter=False,
            )

    def parse_article(self, response: scrapy.http.Response) -> Any:
        sid = response.meta["source_id"]
        ctype = (response.headers.get(b"Content-Type") or b"").decode("latin-1", errors="ignore").lower()
        if "xml" in ctype or response.url.lower().endswith(".xml"):
            yield ArticleItem(
                source_id=sid,
                url=response.url,
                crawl_strategy_used=self.crawl_strategy,
                error_type="NonHtmlSkipped",
                error_message="xml content-type at article step",
                response_status=response.status,
                source_active=response.meta.get("source_active", True),
            )
            return

        td = None
        if self.today_only:
            td = str(resolve_calendar_date(self.target_date_str, self.timezone_str))

        yield ArticleItem(
            source_id=sid,
            url=response.url,
            crawl_strategy_used=self.crawl_strategy,
            html_body=response.body,
            response_status=response.status,
            source_active=response.meta.get("source_active", True),
            candidate_published_at=response.meta.get("candidate_published_at"),
            discovery_source="sitemap",
            target_date=td,
            is_today_candidate=bool(self.today_only),
            discovered_at=datetime.now(timezone.utc).isoformat(),
        )

    def errback(self, failure: Any) -> Any:
        req = failure.request
        resp = getattr(failure.value, "response", None)
        status = resp.status if resp is not None else None
        yield ArticleItem(
            source_id=req.meta.get("source_id", ""),
            url=req.url,
            crawl_strategy_used=self.crawl_strategy,
            error_type="FetchError",
            error_message=repr(failure.value),
            response_status=status,
            source_active=req.meta.get("source_active", True),
        )
