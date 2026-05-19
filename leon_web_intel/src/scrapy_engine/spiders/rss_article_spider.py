from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, NamedTuple
from urllib.parse import urljoin, urlparse

import feedparser
import scrapy
from scrapy.http.response.text import TextResponse

from scrapy_engine.items import ArticleItem
from utils.today_filter import (
    is_datetime_in_range,
    is_url_likely_recent_calendar_days,
    parse_any_datetime,
    parse_datetime_from_feedparser_struct,
    resolve_calendar_date,
    target_recent_calendar_days_range,
)


class _TodayEntry(NamedTuple):
    sort_key: float
    link: str
    cand_raw: str | None


class RssArticleSpider(scrapy.Spider):
    """Production lane for ``rss_then_article_extract`` profiles."""

    name = "rss_article"

    def __init__(
        self,
        sources: list[dict[str, Any]] | None = None,
        max_articles_per_source: int = 5,
        summary: Any | None = None,
        crawl_strategy: str = "rss_then_article_extract",
        today_only: bool = False,
        target_date: str | None = None,
        timezone: str = "Asia/Ho_Chi_Minh",
        max_urls_per_source: int = 1000,
        recent_calendar_days: int = 2,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.sources = sources or []
        self.max_articles_per_source = int(max_articles_per_source)
        self.summary = summary
        self.crawl_strategy = crawl_strategy
        self.today_only = bool(today_only)
        self.target_date_str = target_date
        self.timezone_str = str(timezone or "Asia/Ho_Chi_Minh")
        self.max_urls_per_source = int(max_urls_per_source)
        self.recent_calendar_days = max(1, int(recent_calendar_days))
        self._reserved: dict[str, int] = {}
        self._source_by_id: dict[str, dict[str, Any]] = {
            str(r["source_id"]): r for r in self.sources if r.get("source_id")
        }

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
            for rss_url in row["_rss_urls"]:
                self._sched(1)
                yield scrapy.Request(
                    rss_url,
                    callback=self.parse_feed,
                    errback=self.errback,
                    meta={"source_id": sid, "source_active": active},
                    dont_filter=False,
                )

    def _feed_failure_item(
        self,
        *,
        sid: str,
        active: bool,
        url: str,
        error_type: str,
        error_message: str,
        status: int | None,
    ) -> ArticleItem:
        return ArticleItem(
            source_id=sid,
            url=url,
            crawl_strategy_used=self.crawl_strategy,
            error_type=error_type,
            error_message=error_message,
            response_status=status,
            source_active=active,
        )

    def parse_feed(self, response: scrapy.http.Response) -> Any:
        sid = response.meta["source_id"]
        active = response.meta.get("source_active", True)
        if response.status >= 400:
            yield self._feed_failure_item(
                sid=sid,
                active=active,
                url=response.url,
                error_type="HttpError",
                error_message=f"rss_feed status={response.status}",
                status=int(response.status),
            )
            return

        parsed = feedparser.parse(response.body)
        entries = getattr(parsed, "entries", []) or []
        if not entries:
            yield self._feed_failure_item(
                sid=sid,
                active=active,
                url=response.url,
                error_type="EmptyFeed",
                error_message="rss feed returned no entries",
                status=int(response.status),
            )
            return

        if self.today_only:
            target_d = resolve_calendar_date(self.target_date_str, self.timezone_str)
            start_utc, end_utc = target_recent_calendar_days_range(
                self.target_date_str, self.timezone_str, self.recent_calendar_days
            )
            on_day: list[_TodayEntry] = []
            other: list[_TodayEntry] = []
            for entry in entries:
                link = entry.get("link") or entry.get("id")
                if not link:
                    continue
                link = str(link).strip()
                if not link.startswith("http"):
                    continue

                pub_dt = parse_datetime_from_feedparser_struct(entry.get("published_parsed"))
                if pub_dt is None:
                    pub_dt = parse_any_datetime(entry.get("published"))
                upd_dt = parse_datetime_from_feedparser_struct(entry.get("updated_parsed"))
                if upd_dt is None:
                    upd_dt = parse_any_datetime(entry.get("updated"))
                cand_dt = pub_dt or upd_dt
                cand_raw = None
                if cand_dt:
                    cand_raw = cand_dt.astimezone(timezone.utc).isoformat()
                elif entry.get("published"):
                    cand_raw = str(entry.get("published"))
                elif entry.get("updated"):
                    cand_raw = str(entry.get("updated"))

                sk = cand_dt.timestamp() if cand_dt else float("-inf")
                row = _TodayEntry(sk, link, cand_raw)
                if cand_dt and is_datetime_in_range(cand_dt, start_utc, end_utc):
                    on_day.append(row)
                elif is_url_likely_recent_calendar_days(link, target_d, self.recent_calendar_days):
                    on_day.append(row)
                else:
                    other.append(row)

            on_day.sort(key=lambda e: e.sort_key, reverse=True)
            remaining = self.max_urls_per_source - self._reserved.get(sid, 0)
            if remaining <= 0:
                return
            for row in on_day[:remaining]:
                self._reserved[sid] = self._reserved.get(sid, 0) + 1
                self._sched(1)
                yield scrapy.Request(
                    row.link,
                    callback=self.parse_article,
                    errback=self.errback,
                    meta={
                        "source_id": sid,
                        "source_active": active,
                        "candidate_published_at": row.cand_raw,
                    },
                    dont_filter=False,
                )
            if not on_day:
                home = (self._source_by_id.get(sid) or {}).get("_homepage_url") or ""
                if home and self._reserved.get(sid, 0) < self.max_urls_per_source:
                    self._sched(1)
                    yield scrapy.Request(
                        str(home).strip(),
                        callback=self.parse_homepage_fallback,
                        errback=self.errback,
                        meta={"source_id": sid, "source_active": active},
                        dont_filter=False,
                    )
            return

        remaining = self._cap_for_source(sid) - self._reserved.get(sid, 0)
        for entry in entries:
            if remaining <= 0:
                break
            link = entry.get("link") or entry.get("id")
            if not link:
                continue
            link = str(link).strip()
            if not link.startswith("http"):
                continue
            self._reserved[sid] = self._reserved.get(sid, 0) + 1
            remaining -= 1
            self._sched(1)
            pub_dt = parse_datetime_from_feedparser_struct(entry.get("published_parsed")) or parse_any_datetime(
                entry.get("published")
            )
            cand_raw = pub_dt.astimezone(timezone.utc).isoformat() if pub_dt else (
                str(entry.get("published")) if entry.get("published") else None
            )
            yield scrapy.Request(
                link,
                callback=self.parse_article,
                errback=self.errback,
                meta={
                    "source_id": sid,
                    "source_active": active,
                    "candidate_published_at": cand_raw,
                },
                dont_filter=False,
            )

    def _same_host(self, url: str, base: str) -> bool:
        a = urlparse(url).netloc.lower().removeprefix("www.")
        b = urlparse(base).netloc.lower().removeprefix("www.")
        return bool(a and b and a == b)

    def _homepage_article_link(self, href: str, base_url: str, target_d) -> str | None:
        if not href or href.startswith(("#", "mailto:", "javascript:", "tel:")):
            return None
        abs_u = urljoin(base_url, href)
        if not abs_u.startswith("http") or not self._same_host(abs_u, base_url):
            return None
        low = abs_u.lower()
        if any(x in low for x in ("/rss", "/feed", "/tag/", "/author/", "/page/", "/search")):
            return None
        if target_d is not None and is_url_likely_recent_calendar_days(abs_u, target_d, self.recent_calendar_days):
            return abs_u
        if low.endswith(".html") or ".html?" in low:
            return abs_u
        if any(x in low for x in ("/news/", "/kinh-te", "/kinh-doanh", "/kinh-te-", "/article/")):
            return abs_u
        return None

    def parse_homepage_fallback(self, response: scrapy.http.Response) -> Any:
        """RSS feeds are often stale; discover fresh links from the category/homepage."""
        sid = response.meta["source_id"]
        active = response.meta.get("source_active", True)
        if not isinstance(response, TextResponse):
            return
        target_d = resolve_calendar_date(self.target_date_str, self.timezone_str) if self.today_only else None
        seen: set[str] = set()
        remaining = self.max_urls_per_source - self._reserved.get(sid, 0)
        for href in response.css("a::attr(href)").getall()[:120]:
            if remaining <= 0:
                break
            link = self._homepage_article_link(href, response.url, target_d)
            if not link or link in seen:
                continue
            seen.add(link)
            self._reserved[sid] = self._reserved.get(sid, 0) + 1
            remaining -= 1
            self._sched(1)
            yield scrapy.Request(
                link,
                callback=self.parse_article,
                errback=self.errback,
                meta={
                    "source_id": sid,
                    "source_active": active,
                    "candidate_published_at": None,
                    "homepage_fallback": True,
                },
                dont_filter=False,
            )

    def parse_article(self, response: scrapy.http.Response) -> Any:
        sid = response.meta["source_id"]
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
            discovery_source="rss_homepage" if response.meta.get("homepage_fallback") else "rss",
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
