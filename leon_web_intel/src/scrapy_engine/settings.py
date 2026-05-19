"""Minimal Scrapy settings derived from ``config/crawl_rules.yaml``."""

from __future__ import annotations

import os
from pathlib import Path

from scrapy.settings import Settings

from settings import CrawlRules


def _recent_calendar_days_effective(rules: CrawlRules) -> int:
    raw = os.environ.get("WEB_INTEL_RECENT_CALENDAR_DAYS")
    if raw is not None and str(raw).strip() != "":
        return max(1, int(raw))
    return max(1, int(rules.recent_calendar_days))


def build_scrapy_settings_dict(
    rules: CrawlRules,
    *,
    db_path: Path,
    crawl_rules_path: Path,
    raw_root: Path,
    summary: object,
    closespider_timeout: int = 600,
    today_only: bool = False,
    target_date: str = "today",
    timezone_name: str = "Asia/Ho_Chi_Minh",
) -> dict:
    """Project-style overrides; merged into Scrapy ``Settings``."""
    return {
        "BOT_NAME": "leon_web_intel_scrapy",
        "ROBOTSTXT_OBEY": True,
        # Asyncio reactor avoids some Windows/select-related hangs with the default reactor.
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "USER_AGENT": rules.user_agent,
        "DOWNLOAD_TIMEOUT": int(rules.request_timeout_seconds),
        "RETRY_TIMES": max(0, min(8, int(rules.max_retries))),
        "DOWNLOAD_DELAY": float(rules.default_delay_seconds),
        "CONCURRENT_REQUESTS_PER_DOMAIN": max(1, int(rules.scrapy_concurrent_requests_per_domain)),
        "CONCURRENT_REQUESTS": max(8, int(rules.scrapy_concurrent_requests)),
        "LOG_LEVEL": "INFO",
        "COOKIES_ENABLED": False,
        "TELNETCONSOLE_ENABLED": False,
        # Wall-clock cap so the CLI cannot hang forever on stuck downloads (CloseSpider is in EXTENSIONS_BASE).
        "CLOSESPIDER_TIMEOUT": int(closespider_timeout),
        "ITEM_PIPELINES": {
            "scrapy_engine.pipelines.WebIntelArticlePipeline": 300,
        },
        "WEB_INTEL_DB_PATH": str(db_path.resolve()),
        "WEB_INTEL_CRAWL_RULES_PATH": str(crawl_rules_path.resolve()),
        "WEB_INTEL_RAW_ROOT": str(raw_root.resolve()),
        "WEB_INTEL_SUMMARY": summary,
        "WEB_INTEL_MIN_ARTICLE_LENGTH": rules.min_article_content_length,
        "WEB_INTEL_TODAY_ONLY": bool(today_only),
        "WEB_INTEL_TARGET_DATE": str(target_date),
        "WEB_INTEL_TIMEZONE": str(timezone_name),
        "WEB_INTEL_RECENT_CALENDAR_DAYS": _recent_calendar_days_effective(rules),
        "WEB_INTEL_SITEMAP_MAX_INDEX_CHILDREN": int(rules.sitemap_scrapy_max_index_children),
        "WEB_INTEL_SITEMAP_MAX_XML_PER_SOURCE": int(rules.sitemap_scrapy_max_xml_per_source),
    }


def build_scrapy_settings(
    rules: CrawlRules,
    *,
    db_path: Path,
    crawl_rules_path: Path,
    raw_root: Path,
    summary: object,
    closespider_timeout: int = 600,
    today_only: bool = False,
    target_date: str = "today",
    timezone_name: str = "Asia/Ho_Chi_Minh",
) -> Settings:
    s = Settings()
    s.setdict(
        build_scrapy_settings_dict(
            rules,
            db_path=db_path,
            crawl_rules_path=crawl_rules_path,
            raw_root=raw_root,
            summary=summary,
            closespider_timeout=closespider_timeout,
            today_only=today_only,
            target_date=target_date,
            timezone_name=timezone_name,
        ),
        priority="cmdline",
    )
    return s
