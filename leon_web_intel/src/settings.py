"""Load YAML configuration into typed models."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class JsDetectionConfig(BaseModel):
    min_text_length: int = 500
    script_count_threshold: int = 15
    js_keywords: list[str] = Field(default_factory=list)


class CrawlRules(BaseModel):
    user_agent: str = "LeonWebIntelBot/0.1 (+local research project)"
    # SEC fair access + OpenAlex/Crossref polite pool + NCBI etiquette — use env WEB_INTEL_CONTACT_EMAIL if unset.
    contact_email: str | None = None
    contact_display_name: str = "LeonWebIntel"
    ncbi_tool_name: str = "leon_web_intel"
    request_timeout_seconds: float = 20.0
    max_retries: int = 2
    default_delay_seconds: float = 1.5
    concurrency: int = 20
    scrapy_concurrent_requests: int = 32
    scrapy_concurrent_requests_per_domain: int = 3
    profile_cache_days: int = 7
    http_cache_enabled: bool = True

    max_rss_candidates: int = 20
    # Hard cap on RSS URL probe GETs during profiling (prevents multi-hour stalls).
    profiler_max_rss_http_attempts: int = 40
    max_sitemap_candidates: int = 10
    max_sitemaps_to_parse_in_profiler: int = 5
    max_urls_from_sitemap_in_profiler: int = 200
    # Scrapy sitemap lane: limit discovery cost (each .xml fetch counts). 0 = unlimited.
    sitemap_scrapy_max_index_children: int = 5
    sitemap_scrapy_max_xml_per_source: int = 20

    min_extract_text_length: int = 300
    min_article_content_length: int = 300
    sample_max_articles_per_source: int = 5

    rss_candidate_paths: list[str] = Field(default_factory=list)
    sitemap_candidate_paths: list[str] = Field(default_factory=list)

    js_detection: JsDetectionConfig = Field(default_factory=JsDetectionConfig)
    paywall_keywords: list[str] = Field(default_factory=list)
    login_keywords: list[str] = Field(default_factory=list)
    captcha_keywords: list[str] = Field(default_factory=list)
    prefer_metadata_only_domains: list[str] = Field(default_factory=list)

    # Max-collection: keep trafilatura output even if HTML shell matches paywall/login keywords (not captcha).
    keep_extract_despite_access_signal_if_meets_min_length: bool = False
    # Today-mode: accept articles without a parsed date when URL/day heuristics are inconclusive (broader intake).
    today_allow_undated_uncertain_urls: bool = False
    # Today-mode: local calendar window length ending at target date (e.g. 2 = yesterday + today).
    recent_calendar_days: int = 2

    # Sources with >= N block-type crawl_errors and 0 DB articles (and not NotToday-only) go on source_crawl_skip.
    uncrawlable_min_block_errors: int = 5
    crawl_skip_list_enabled: bool = True
    # Never crawl (no news feed, site placeholder, etc.) — always on skip list.
    manual_skip_domains: list[str] = Field(default_factory=list)


def load_crawl_rules(path: Path) -> CrawlRules:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    local_path = path.with_name("crawl_rules.local.yaml")
    if local_path.is_file():
        local = yaml.safe_load(local_path.read_text(encoding="utf-8")) or {}
        if isinstance(local, dict):
            data = {**data, **local}
    return CrawlRules.model_validate(data)
