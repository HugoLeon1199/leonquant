"""End-to-end profiling orchestration + strategy decision tree."""

from __future__ import annotations

import json
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse

from loguru import logger
from pydantic import BaseModel, Field
from tqdm.auto import tqdm

from profiler.html_probe import HTMLProbeResult, run_html_probe
from profiler.js_detector import detect_js_heavy
from profiler.normalize import NormalizedSource, dedupe_sources, normalize_url
from profiler.paywall_detector import detect_paywall_signals
from profiler.robots_checker import check_robots
from profiler.rss_detector import discover_rss_urls, validate_feed_body
from profiler.sitemap_detector import discover_sitemap_urls
from settings import CrawlRules
from storage.db import WebIntelDB, new_id, utc_now
from utils.cache import CachedHttpClient


class SourceProfile(BaseModel):
    source_id: str = ""
    input_url: str = ""
    normalized_url: str = ""
    domain: str = ""
    scheme: str = "https"
    homepage_url: str = ""
    robots_url: str = ""
    robots_ok: bool = True
    robots_sitemaps: list[str] = Field(default_factory=list)
    robots_disallow_detected: bool = False
    robots_can_fetch_homepage: bool = True
    has_known_api: bool = False
    known_api_adapter: str | None = None
    known_api_endpoint_hint: str | None = None
    has_rss: bool = False
    rss_urls: list[str] = Field(default_factory=list)
    rss_valid_count: int = 0
    has_sitemap: bool = False
    sitemap_urls: list[str] = Field(default_factory=list)
    sitemap_url_count: int = 0
    html_status_code: int = 0
    html_title: str = ""
    html_text_length: int = 0
    html_link_count: int = 0
    html_extract_ok: bool = False
    sample_extracted_text_length: int = 0
    js_required: bool = False
    paywall_detected: bool = False
    captcha_detected: bool = False
    login_detected: bool = False
    best_strategy: str = "manual_review"
    tos_risk: str = "unknown"
    status: str = "review"
    error_message: str | None = None
    profiled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def decide_best_strategy(profile: SourceProfile, rules: CrawlRules) -> SourceProfile:
    """Prefer RSS → sitemap → HTML → Playwright fallback (Leon Quant: no API-first path)."""
    if profile.has_rss and profile.rss_valid_count > 0:
        profile.best_strategy = "rss_then_article_extract"
        profile.tos_risk = "medium"
        profile.status = "active"
        apply_commercial_governance(profile, rules)
        return profile

    if profile.has_sitemap and profile.sitemap_url_count > 0:
        profile.best_strategy = "sitemap_then_article_extract"
        profile.tos_risk = "medium"
        profile.status = "active"
        apply_commercial_governance(profile, rules)
        return profile

    if profile.html_status_code < 400 and profile.html_extract_ok:
        profile.best_strategy = "html_then_trafilatura"
        profile.tos_risk = "medium"
        profile.status = "active_candidate"
        apply_commercial_governance(profile, rules)
        return profile

    if profile.js_required:
        profile.best_strategy = "playwright_fallback"
        profile.tos_risk = "medium"
        profile.status = "active_candidate"
        apply_commercial_governance(profile, rules)
        return profile

    if profile.paywall_detected or profile.login_detected or profile.captcha_detected:
        profile.best_strategy = "metadata_only"
        profile.tos_risk = "high"
        profile.status = "review"
        return profile

    profile.best_strategy = "manual_review"
    profile.tos_risk = "unknown"
    profile.status = "review"
    return profile


def apply_robots_homepage_governance(profile: SourceProfile) -> str | None:
    """
    If robots.txt disallows our User-Agent from the homepage, never keep HTML/Playwright
    crawl strategies; downgrade and return a message for crawl_errors / error_message.
    """
    if profile.robots_can_fetch_homepage:
        return None
    blocked = {"html_then_trafilatura", "playwright_fallback"}
    if profile.best_strategy not in blocked:
        return None
    prev = profile.best_strategy
    has_meta = bool(
        (profile.html_title or "").strip()
        or profile.sample_extracted_text_length > 0
        or profile.html_text_length > 0
    )
    profile.best_strategy = "metadata_only" if has_meta else "manual_review"
    profile.status = "review"
    profile.tos_risk = "high"
    msg = (
        f"robots.txt disallows User-Agent from fetching homepage ({profile.homepage_url}); "
        f"removed strategy {prev} → {profile.best_strategy}"
    )
    profile.error_message = (profile.error_message + " | " if profile.error_message else "") + msg
    return msg


def apply_commercial_governance(profile: SourceProfile, rules: CrawlRules) -> None:
    domain = profile.domain.lower()
    risky = [d.lower() for d in rules.prefer_metadata_only_domains]
    if domain not in risky:
        return
    if profile.best_strategy in ("html_then_trafilatura", "playwright_fallback"):
        profile.best_strategy = "metadata_only"
        profile.tos_risk = "high"
        profile.status = "review"


def profile_to_db_row(profile: SourceProfile) -> dict[str, Any]:
    return {
        "source_id": profile.source_id,
        "input_url": profile.input_url,
        "normalized_url": profile.normalized_url,
        "domain": profile.domain,
        "scheme": profile.scheme,
        "homepage_url": profile.homepage_url,
        "robots_url": profile.robots_url,
        "robots_ok": profile.robots_ok,
        "robots_sitemaps": json.dumps(profile.robots_sitemaps),
        "robots_disallow_detected": profile.robots_disallow_detected,
        "robots_can_fetch_homepage": profile.robots_can_fetch_homepage,
        "has_known_api": profile.has_known_api,
        "known_api_adapter": profile.known_api_adapter,
        "known_api_endpoint_hint": profile.known_api_endpoint_hint,
        "has_rss": profile.has_rss,
        "rss_urls": json.dumps(profile.rss_urls),
        "rss_valid_count": profile.rss_valid_count,
        "has_sitemap": profile.has_sitemap,
        "sitemap_urls": json.dumps(profile.sitemap_urls),
        "sitemap_url_count": profile.sitemap_url_count,
        "html_status_code": profile.html_status_code,
        "html_title": profile.html_title,
        "html_text_length": profile.html_text_length,
        "html_link_count": profile.html_link_count,
        "html_extract_ok": profile.html_extract_ok,
        "sample_extracted_text_length": profile.sample_extracted_text_length,
        "js_required": profile.js_required,
        "paywall_detected": profile.paywall_detected,
        "captcha_detected": profile.captcha_detected,
        "login_detected": profile.login_detected,
        "best_strategy": profile.best_strategy,
        "tos_risk": profile.tos_risk,
        "status": profile.status,
        "error_message": profile.error_message,
        "profiled_at": profile.profiled_at,
    }


class SourceProfiler:
    def __init__(
        self,
        *,
        rules: CrawlRules,
        http: CachedHttpClient,
        db: WebIntelDB,
        raw_store,
    ) -> None:
        self.rules = rules
        self.http = http
        self.db = db
        self.raw_store = raw_store

    def _fetch_text(self, url: str) -> tuple[int, str]:
        return self.http.get_text(url)

    def _fetch_bytes(self, url: str) -> tuple[int, bytes]:
        entry = self.http.get(url)
        return entry.status_code, entry.body

    def profile_source(self, input_url: str) -> SourceProfile:
        profile = SourceProfile(input_url=input_url, profiled_at=datetime.now(timezone.utc))
        try:
            norm = normalize_url(input_url)
            profile.source_id = norm.source_id
            profile.input_url = norm.input_url
            profile.normalized_url = norm.normalized_url
            profile.domain = norm.domain
            profile.scheme = norm.scheme
            profile.homepage_url = norm.homepage_url

            # Detect direct RSS/Atom inputs from their body, not only from URL
            # naming conventions. Many valid feeds end in /index, backend.xml,
            # an API query, or a FeedBurner route with no "rss" token.
            try:
                direct_status, direct_body = self._fetch_text(norm.input_url)
            except Exception:
                direct_status, direct_body = 0, ""
            if direct_status < 400 and validate_feed_body(direct_body, norm.input_url):
                profile.has_rss = True
                profile.rss_urls = [norm.input_url]
                profile.rss_valid_count = 1
                profile = decide_best_strategy(profile, self.rules)
                self.db.upsert_source_profile(profile_to_db_row(profile))
                logger.info(
                    "[PROFILE] {} | direct_rss_body=true | strategy={}",
                    profile.source_id,
                    profile.best_strategy,
                )
                return profile

            parsed = urlparse(norm.normalized_url)
            netloc_with_host = parsed.netloc.lower()

            robots = check_robots(
                scheme=norm.scheme,
                domain_with_host=netloc_with_host,
                homepage_url=norm.homepage_url,
                user_agent=self.rules.user_agent,
                fetch_text=self._fetch_text,
            )
            profile.robots_url = robots.robots_url
            profile.robots_ok = robots.robots_ok
            profile.robots_sitemaps = robots.robots_sitemaps
            profile.robots_disallow_detected = robots.robots_disallow_detected
            profile.robots_can_fetch_homepage = robots.can_fetch_homepage

            homepage_url = norm.homepage_url
            if robots.can_fetch_homepage:
                try:
                    hp_status, homepage_html = self._fetch_text(homepage_url)
                except Exception:
                    hp_status, homepage_html = 0, ""
            else:
                hp_status, homepage_html = 403, ""

            rss_urls, rss_valid = discover_rss_urls(
                norm,
                homepage_html,
                homepage_url,
                self.rules,
                self._fetch_text,
            )
            profile.rss_urls = rss_urls
            profile.rss_valid_count = rss_valid
            profile.has_rss = rss_valid > 0

            if profile.has_rss and norm.input_url in rss_urls:
                # Direct feed catalogs already provide the acquisition
                # endpoint. Do not spend additional requests probing sitemap,
                # HTML, JS and paywall signals for the site homepage.
                profile = decide_best_strategy(profile, self.rules)
                self.db.upsert_source_profile(profile_to_db_row(profile))
                logger.info(
                    "[PROFILE] {} | direct_rss=true | strategy={}",
                    profile.source_id,
                    profile.best_strategy,
                )
                return profile

            sm_urls, sm_count = discover_sitemap_urls(
                norm,
                self.rules,
                robots.robots_sitemaps,
                self._fetch_bytes,
            )
            profile.sitemap_urls = sm_urls
            profile.sitemap_url_count = sm_count
            profile.has_sitemap = sm_count > 0

            if robots.can_fetch_homepage:
                probe = run_html_probe(norm, homepage_url, self.rules, self._fetch_text, self.raw_store)
            else:
                probe = HTMLProbeResult(
                    status_code=403,
                    html_title="",
                    html_text_length=0,
                    html_link_count=0,
                    script_count=0,
                    html_extract_ok=False,
                    sample_extracted_text_length=0,
                    raw_path="",
                    raw_html="",
                )

            profile.html_status_code = probe.status_code
            profile.html_title = probe.html_title
            profile.html_text_length = probe.html_text_length
            profile.html_link_count = probe.html_link_count
            profile.html_extract_ok = probe.html_extract_ok
            profile.sample_extracted_text_length = probe.sample_extracted_text_length

            profile.js_required = detect_js_heavy(probe.raw_html, probe, self.rules)

            pay = detect_paywall_signals(probe.raw_html or homepage_html, self.rules)
            profile.paywall_detected = pay.paywall_detected
            profile.login_detected = pay.login_detected
            profile.captcha_detected = pay.captcha_detected

            profile = decide_best_strategy(profile, self.rules)

            gov_msg = apply_robots_homepage_governance(profile)
            if gov_msg:
                self.db.insert_crawl_error(
                    {
                        "id": new_id(),
                        "source_id": profile.source_id,
                        "url": profile.homepage_url or profile.normalized_url or "",
                        "stage": "profile",
                        "error_type": "RobotsDisallowHomepage",
                        "error_message": gov_msg,
                        "created_at": utc_now(),
                    }
                )

            logger.info(
                "[PROFILE] {} | api={} | rss={} | sitemap={} | html_ok={} | js={} | strategy={}",
                profile.source_id,
                profile.has_known_api,
                profile.has_rss,
                profile.has_sitemap,
                profile.html_extract_ok,
                profile.js_required,
                profile.best_strategy,
            )
        except Exception as exc:  # noqa: BLE001
            tb = traceback.format_exc(limit=5)
            profile.error_message = f"{exc}\n{tb}"
            profile.best_strategy = "manual_review"
            profile.status = "review"
            profile.tos_risk = "unknown"
            logger.error("[ERROR] {} | {}", profile.source_id or input_url, exc)
            self.db.insert_crawl_error(
                {
                    "id": new_id(),
                    "source_id": profile.source_id or "unknown",
                    "url": input_url,
                    "stage": "profile",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "created_at": utc_now(),
                }
            )

        self.db.upsert_source_profile(profile_to_db_row(profile))
        return profile

    def should_skip(self, norm: NormalizedSource, *, cache_days: int, force_refresh: bool) -> bool:
        if force_refresh:
            return False
        row = self.db.get_profile(norm.source_id)
        if not row or row.get("profiled_at") is None:
            return False
        prof_at = row["profiled_at"]
        if hasattr(prof_at, "to_pydatetime"):
            prof_at = prof_at.to_pydatetime()
        if prof_at.tzinfo is None:
            prof_at = prof_at.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - prof_at
        if age <= timedelta(days=cache_days):
            logger.info("[SKIP] {} already profiled within {} days", norm.source_id, cache_days)
            return True
        return False

    def profile_many(
        self,
        urls: list[str],
        *,
        limit: int | None = None,
        concurrency: int | None = None,
        cache_days: int | None = None,
        force_refresh: bool = False,
    ) -> list[SourceProfile]:
        concurrency = concurrency or self.rules.concurrency
        cache_days = cache_days if cache_days is not None else self.rules.profile_cache_days

        norms: list[NormalizedSource] = []
        for u in urls:
            try:
                norms.append(normalize_url(u))
            except Exception as exc:  # noqa: BLE001
                logger.warning("skip invalid url {}: {}", u, exc)

        uniq = dedupe_sources(norms)

        if limit is not None:
            uniq = uniq[:limit]

        to_run: list[NormalizedSource] = []
        for n in uniq:
            if self.should_skip(n, cache_days=cache_days, force_refresh=force_refresh):
                continue
            to_run.append(n)

        results: list[SourceProfile] = []

        def task(norm: NormalizedSource) -> SourceProfile:
            return self.profile_source(norm.input_url)

        with ThreadPoolExecutor(max_workers=max(1, concurrency)) as ex:
            futures = {ex.submit(task, n): n for n in to_run}
            for fut in tqdm(as_completed(futures), total=len(futures), desc="Profiling"):
                try:
                    results.append(fut.result())
                except Exception as exc:  # noqa: BLE001
                    n = futures[fut]
                    logger.error("executor failure for {}: {}", n.input_url, exc)

        return results
