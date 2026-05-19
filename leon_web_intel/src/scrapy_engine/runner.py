"""Run Scrapy crawlers after SourceProfiler (DuckDB-backed source selection)."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Literal

from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging

from scrapy_engine.db_source_loader import fetch_crawl_skip_source_ids, load_sources_for_scrapy
from scrapy_engine.settings import build_scrapy_settings
from scrapy_engine.spiders.html_article_spider import HtmlArticleSpider
from scrapy_engine.spiders.rss_article_spider import RssArticleSpider
from scrapy_engine.spiders.sitemap_article_spider import SitemapArticleSpider
from settings import load_crawl_rules


class ScrapyRunSummary:
    """Thread-safe counters shared with spiders + pipeline."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.sources_loaded = 0
        self.requests_scheduled = 0
        self.articles_inserted = 0
        self.errors_logged = 0
        self.duplicates_skipped = 0
        self.pipeline_items = 0

    def __copy__(self) -> ScrapyRunSummary:
        """Scrapy copies Settings via deepcopy; keep one shared summary + lock."""
        return self

    def __deepcopy__(self, memo: object) -> ScrapyRunSummary:
        return self


def run_scrapy_engine(
    *,
    root: Path,
    strategy: Literal["rss", "sitemap", "html", "all"],
    limit: int,
    max_articles_per_source: int,
    db_path: Path | None = None,
    run_id: str | None = None,
    close_spider_timeout: int = 600,
    today_only: bool = False,
    target_date: str = "today",
    timezone_name: str = "Asia/Ho_Chi_Minh",
    max_urls_per_source: int = 1000,
    allowed_domains: frozenset[str] | None = None,
    respect_crawl_skip: bool = True,
) -> ScrapyRunSummary:
    """Execute Scrapy lane(s). Uses CrawlerProcess for reliable teardown (esp. Windows)."""
    _ = run_id  # Stored at the orchestration layer for this phase.
    rules_path = root / "config" / "crawl_rules.yaml"
    rules = load_crawl_rules(rules_path)
    db = db_path or (root / "data" / "db" / "web_intel.duckdb")
    (root / "data" / "db").mkdir(parents=True, exist_ok=True)
    raw_root = root / "data" / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)

    skip_ids = (
        fetch_crawl_skip_source_ids(db)
        if respect_crawl_skip and rules.crawl_skip_list_enabled
        else frozenset()
    )
    buckets = load_sources_for_scrapy(
        db,
        strategy,
        limit,
        allowed_domains=allowed_domains,
        exclude_source_ids=skip_ids,
    )
    summary = ScrapyRunSummary()
    summary.sources_loaded = len(buckets["rss"]) + len(buckets["sitemap"]) + len(buckets["html"])

    if summary.sources_loaded == 0:
        return summary

    settings = build_scrapy_settings(
        rules,
        db_path=db,
        crawl_rules_path=rules_path,
        raw_root=raw_root,
        summary=summary,
        closespider_timeout=close_spider_timeout,
        today_only=today_only,
        target_date=target_date,
        timezone_name=timezone_name,
    )
    recent_calendar_days = max(1, int(settings.getint("WEB_INTEL_RECENT_CALENDAR_DAYS", 2)))

    configure_logging(settings={"LOG_LEVEL": settings.get("LOG_LEVEL")})
    process = CrawlerProcess(settings)

    if buckets["rss"]:
        process.crawl(
            RssArticleSpider,
            sources=buckets["rss"],
            max_articles_per_source=max_articles_per_source,
            summary=summary,
            today_only=today_only,
            target_date=target_date,
            timezone=timezone_name,
            max_urls_per_source=max_urls_per_source,
            recent_calendar_days=recent_calendar_days,
        )
    if buckets["sitemap"]:
        process.crawl(
            SitemapArticleSpider,
            sources=buckets["sitemap"],
            max_articles_per_source=max_articles_per_source,
            summary=summary,
            today_only=today_only,
            target_date=target_date,
            timezone=timezone_name,
            max_urls_per_source=max_urls_per_source,
            recent_calendar_days=recent_calendar_days,
        )
    if buckets["html"]:
        html_cap = max_urls_per_source if today_only else max_articles_per_source
        process.crawl(
            HtmlArticleSpider,
            sources=buckets["html"],
            max_articles_per_source=max_articles_per_source,
            summary=summary,
            today_only=today_only,
            target_date=target_date,
            timezone=timezone_name,
            max_urls_per_source=html_cap,
            max_depth=2,
            recent_calendar_days=recent_calendar_days,
        )

    process.start()
    return summary
