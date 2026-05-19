from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

import scrapy
from scrapy.http.response.text import TextResponse

from scrapy_engine.items import ArticleItem
from utils.today_filter import is_url_likely_recent_calendar_days, resolve_calendar_date


def _article_like_url(url: str) -> bool:
    u = url.lower()
    needles = ("/news/", "/article/", "/story/", "/topics/", "/world/", "/politics/", "/business/", "/sport/", "/20")
    return any(n in u for n in needles)


class HtmlArticleSpider(scrapy.Spider):
    """Production lane for ``html_then_trafilatura`` profiles (bounded link crawl)."""

    name = "html_article"

    def __init__(
        self,
        sources: list[dict[str, Any]] | None = None,
        max_articles_per_source: int = 5,
        summary: Any | None = None,
        crawl_strategy: str = "html_then_trafilatura",
        max_depth: int = 2,
        max_links_per_page: int = 40,
        today_only: bool = False,
        target_date: str | None = None,
        timezone: str = "Asia/Ho_Chi_Minh",
        max_urls_per_source: int = 300,
        recent_calendar_days: int = 2,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.sources = sources or []
        self.max_articles_per_source = int(max_articles_per_source)
        self.summary = summary
        self.crawl_strategy = crawl_strategy
        self.max_depth = int(max_depth)
        self.max_links_per_page = int(max_links_per_page)
        self.today_only = bool(today_only)
        self.target_date_str = target_date
        self.timezone_str = str(timezone or "Asia/Ho_Chi_Minh")
        self.max_urls_per_source = int(max_urls_per_source)
        self.recent_calendar_days = max(1, int(recent_calendar_days))
        self._attempted: dict[str, int] = {}
        self._reserved: dict[str, int] = {}

    def _sched(self, n: int = 1) -> None:
        if self.summary:
            with self.summary.lock:
                self.summary.requests_scheduled += n

    def _cap(self, sid: str) -> int:
        return self.max_urls_per_source if self.today_only else self.max_articles_per_source

    def _host_key(self, netloc: str) -> str:
        host = netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host

    def _same_registrable_host(self, a: str, b: str) -> bool:
        ha = self._host_key(urlparse(a).netloc)
        hb = self._host_key(urlparse(b).netloc)
        return bool(ha and hb and ha == hb)

    def _target_date_obj(self):
        return resolve_calendar_date(self.target_date_str, self.timezone_str)

    def start_requests(self) -> Any:
        for row in self.sources:
            sid = row["source_id"]
            self._attempted.setdefault(sid, 0)
            self._reserved.setdefault(sid, 0)
            home = row["_homepage_url"]
            if not home:
                continue
            if self._reserved[sid] >= self._cap(sid):
                continue
            active = row.get("_source_active", True)
            self._reserved[sid] += 1
            self._sched(1)
            yield scrapy.Request(
                home,
                callback=self.parse_page,
                errback=self.errback,
                meta={"source_id": sid, "depth": 0, "source_active": active},
                dont_filter=False,
            )

    def parse_page(self, response: scrapy.http.Response) -> Any:
        sid = response.meta["source_id"]
        depth = int(response.meta["depth"])
        active = response.meta.get("source_active", True)
        target_d = self._target_date_obj() if self.today_only else None

        if self._attempted.get(sid, 0) >= self._cap(sid):
            return

        self._attempted[sid] = self._attempted.get(sid, 0) + 1
        td = str(target_d) if self.today_only else None
        yield ArticleItem(
            source_id=sid,
            url=response.url,
            crawl_strategy_used=self.crawl_strategy,
            html_body=response.body,
            response_status=response.status,
            source_active=active,
            discovery_source="html",
            target_date=td,
            is_today_candidate=bool(self.today_only),
            candidate_published_at=None,
            discovered_at=datetime.now(timezone.utc).isoformat(),
        )

        if self._attempted.get(sid, 0) >= self._cap(sid):
            return

        if depth >= self.max_depth:
            return

        if not isinstance(response, TextResponse):
            return

        links = response.css("a::attr(href)").getall()[: self.max_links_per_page]
        for href in links:
            if self._reserved.get(sid, 0) >= self._cap(sid):
                break
            if not href or href.startswith(("#", "mailto:", "javascript:", "tel:")):
                continue
            abs_u = urljoin(response.url, href)
            if not abs_u.startswith("http"):
                continue
            if not self._same_registrable_host(abs_u, response.url):
                continue

            if self.today_only and target_d is not None:
                follow = False
                if depth == 0:
                    follow = True
                elif is_url_likely_recent_calendar_days(abs_u, target_d, self.recent_calendar_days):
                    follow = True
                elif depth == 1 and _article_like_url(abs_u):
                    follow = True
                if not follow:
                    continue
            self._reserved[sid] += 1
            self._sched(1)
            yield scrapy.Request(
                abs_u,
                callback=self.parse_page,
                errback=self.errback,
                meta={"source_id": sid, "depth": depth + 1, "source_active": active},
                dont_filter=False,
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
