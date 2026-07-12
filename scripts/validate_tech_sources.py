#!/usr/bin/env python3
"""Phase 0 validation gate for the standalone tech/AI crawl pipeline."""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any

import httpx
import feedparser

ROOT = Path(__file__).resolve().parents[1]
LEON_ROOT = ROOT / "leon_web_intel"
SRC = LEON_ROOT / "src"

import sys

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collectors.html_collector import discover_internal_links  # noqa: E402
from collectors.rss_collector import discover_from_rss  # noqa: E402
from collectors.sitemap_collector import discover_from_sitemap  # noqa: E402
from extraction.article_extractor import extract_article  # noqa: E402
from profiler.source_profiler import SourceProfiler  # noqa: E402
from settings import load_crawl_rules  # noqa: E402
from storage.db import WebIntelDB, new_id, utc_now  # noqa: E402
from storage.raw_store import RawStore  # noqa: E402
from utils.cache import CachedHttpClient  # noqa: E402
from utils.today_filter import parse_any_datetime  # noqa: E402

from scripts.tech_common import (  # noqa: E402
    ACTIVE_TIER_FILE_BY_STATUS,
    PASS_STATUSES,
    RECHECK_STATUSES,
    TECH_ACTIVE,
    TECH_CATALOG,
    TECH_DISABLED,
    TECH_TIERS_DIR,
    TECH_TIERS_MANIFEST,
    TECH_VALIDATION_JSON,
    TECH_VALIDATION_MD,
    TECH_VALIDATION_DB,
    canonical_domain,
    dump_json,
    ensure_parent,
    host_from_url,
    parse_catalog,
    text_looks_tech,
)

VALIDATION_SCHEMA = "tech-source-validation-v1"
MIN_SAMPLE_URLS = 5
MIN_EXTRACT_SUCCESSES = 3
MIN_CONTENT_LENGTH = 500
MIN_FEED_SUMMARY_LENGTH = 180
MAX_DISCOVERED_URLS = 5
RECENT_DAYS = 45


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def response_meta(url: str, *, timeout: float, user_agent: str) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "input_url": url,
        "final_url": url,
        "redirect_chain": [],
        "http_status": 0,
        "content_type": "",
        "error": "",
    }
    try:
        with httpx.Client(
            headers={"User-Agent": user_agent},
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            resp = client.get(url)
        meta["http_status"] = int(resp.status_code)
        meta["final_url"] = str(resp.url)
        meta["content_type"] = str(resp.headers.get("content-type") or "")
        meta["redirect_chain"] = [str(r.url) for r in resp.history] + [str(resp.url)]
        return meta
    except Exception as exc:  # noqa: BLE001
        meta["error"] = str(exc)
        return meta


def published_is_recent(value: str | None) -> bool:
    if not value:
        return False
    try:
        dt = parse_any_datetime(str(value))
    except Exception:  # noqa: BLE001
        dt = None
    if dt is None:
        return False
    if getattr(dt, "tzinfo", None) is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (_now_utc() - dt.astimezone(timezone.utc)).days <= RECENT_DAYS


def _feed_entry_text(entry: Any) -> str:
    parts = entry.get("content") or []
    rich = " ".join(
        str(part.get("value") or "")
        for part in parts
        if isinstance(part, dict)
    )
    raw = rich or entry.get("summary") or entry.get("description") or ""
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", str(raw)))).strip()


def validate_direct_feed_source(entry: dict[str, str], *, rules: Any) -> dict[str, Any]:
    """Fast, conservative readiness check for a catalog of direct RSS/Atom feeds."""
    url = entry["url"]
    try:
        response = httpx.get(
            url,
            headers={"User-Agent": rules.user_agent, "Accept": "application/rss+xml,application/atom+xml,application/xml,text/xml,*/*"},
            follow_redirects=True,
            timeout=min(15.0, float(rules.request_timeout_seconds)),
        )
        status_code = int(response.status_code)
        final_url = str(response.url)
        content_type = str(response.headers.get("content-type") or "")
        parsed = feedparser.parse(response.content) if status_code < 400 else None
        entries = list(getattr(parsed, "entries", []) or [])[:MAX_DISCOVERED_URLS]
        error = ""
    except Exception as exc:  # noqa: BLE001
        status_code = 0
        final_url = url
        content_type = ""
        entries = []
        error = str(exc)

    samples: list[dict[str, Any]] = []
    discovered_urls: list[str] = []
    for feed_entry in entries:
        link = str(feed_entry.get("link") or feed_entry.get("id") or "").strip()
        title = str(feed_entry.get("title") or "").strip()
        published = str(feed_entry.get("published") or feed_entry.get("updated") or "").strip() or None
        content = _feed_entry_text(feed_entry)
        if link:
            discovered_urls.append(link)
        samples.append(
            {
                "url": link,
                "title": title or None,
                "published_at": published,
                "content_length": len(content),
                "extract_ok": bool(link and title and len(content) >= MIN_FEED_SUMMARY_LENGTH),
                "feed_summary_fallback": True,
                "paywall_detected": False,
                "login_detected": False,
                "captcha_detected": False,
                "published_recent": published_is_recent(published),
                "looks_tech": True,
            }
        )
    ready = [row for row in samples if row["extract_ok"] and row.get("published_at")]
    if status_code >= 400 or error:
        validation_status = "DEAD_URL"
    elif len(ready) >= MIN_EXTRACT_SUCCESSES and len(discovered_urls) >= MIN_SAMPLE_URLS:
        validation_status = "PASS_RSS"
    elif samples and any(row["extract_ok"] for row in samples):
        validation_status = "SOFT_PASS"
    else:
        validation_status = "ARTICLE_EXTRACTION_FAILED"
    return {
        "source_id": re.sub(r"[^a-z0-9]+", "_", host_from_url(url)).strip("_"),
        "name": entry["name"],
        "input_url": url,
        "domain": host_from_url(url),
        "normalized_url": url,
        "final_url": final_url,
        "redirect_chain": [url] + ([final_url] if final_url != url else []),
        "http_status": status_code,
        "content_type": content_type,
        "robots_can_fetch_homepage": True,
        "robots_disallow_detected": False,
        "has_rss": bool(samples),
        "has_sitemap": False,
        "html_extract_ok": False,
        "js_required": False,
        "paywall_detected": False,
        "login_detected": False,
        "captcha_detected": False,
        "best_strategy": "rss_then_article_extract" if samples else "manual_review",
        "discovered_article_urls": discovered_urls,
        "discovered_article_count": len(discovered_urls),
        "article_samples": samples,
        "validation_status": validation_status,
        "production_ready": validation_status in PASS_STATUSES,
        "notes": error,
    }


def classify_source(
    *,
    meta: dict[str, Any],
    profile: Any,
    discovered_count: int,
    article_results: list[dict[str, Any]],
    requires_playwright: bool,
) -> str:
    if meta.get("http_status", 0) >= 400 or meta.get("error"):
        return "DEAD_URL"
    if bool(profile.captcha_detected):
        return "CAPTCHA"
    if bool(profile.paywall_detected) or bool(profile.login_detected):
        if discovered_count == 0:
            return "PAYWALL"
    if requires_playwright:
        return "JS_ONLY"
    if profile.best_strategy == "manual_review" and not (
        profile.has_rss or profile.has_sitemap or profile.html_extract_ok
    ):
        return "BLOCKED"
    if discovered_count == 0:
        return "NO_ARTICLE_LINKS"

    extract_successes = [r for r in article_results if r.get("extract_ok")]
    if not extract_successes:
        return "ARTICLE_EXTRACTION_FAILED"

    tech_hits = [r for r in extract_successes if r.get("looks_tech")]
    if not tech_hits:
        return "OFF_TOPIC"

    recent_hits = [r for r in tech_hits if r.get("published_recent") or r.get("published_at")]
    content_hits = [
        r for r in tech_hits
        if int(r.get("content_length") or 0)
        >= (MIN_FEED_SUMMARY_LENGTH if r.get("feed_summary_fallback") else MIN_CONTENT_LENGTH)
    ]
    titled_hits = [r for r in tech_hits if str(r.get("title") or "").strip()]
    published_hits = [r for r in tech_hits if str(r.get("published_at") or "").strip()]

    prod_ready = (
        discovered_count >= MIN_SAMPLE_URLS
        and len(content_hits) >= MIN_EXTRACT_SUCCESSES
        and len(titled_hits) >= MIN_EXTRACT_SUCCESSES
        and len(published_hits) >= MIN_EXTRACT_SUCCESSES
    )
    if prod_ready:
        if profile.has_rss:
            source_url = str(profile.input_url or meta.get("input_url") or "").lower()
            if ".rss" in source_url or "forum" in source_url or "community" in source_url:
                return "PASS_FORUM_RSS"
            return "PASS_RSS"
        if profile.has_sitemap:
            return "PASS_SITEMAP"
        return "PASS_HTML"

    if recent_hits:
        return "SOFT_PASS"
    if len(published_hits) < MIN_EXTRACT_SUCCESSES:
        return "NO_RECENT_CONTENT"
    return "SOFT_PASS"


def discover_candidates(
    *,
    profile: Any,
    db: WebIntelDB,
    raw_store: RawStore,
    http: CachedHttpClient,
    rules: Any,
) -> list[dict[str, Any]]:
    source_id = profile.source_id

    def fetch_text(u: str) -> tuple[int, str]:
        return http.get_text(u)

    def fetch_bytes(u: str) -> tuple[int, bytes]:
        entry = http.get(u)
        return entry.status_code, entry.body

    candidates: list[dict[str, Any]] = []
    if profile.has_rss and profile.rss_urls:
        candidates = discover_from_rss(
            source_id=source_id,
            rss_url=profile.rss_urls[0],
            max_items=MAX_DISCOVERED_URLS,
            fetch_text=fetch_text,
            raw_store=raw_store,
            db=db,
        )
    elif profile.has_sitemap and profile.sitemap_urls:
        candidates = discover_from_sitemap(
            source_id=source_id,
            sitemap_url=profile.sitemap_urls[0],
            max_items=MAX_DISCOVERED_URLS,
            fetch_bytes=fetch_bytes,
            raw_store=raw_store,
            db=db,
            max_urls_probe=rules.max_urls_from_sitemap_in_profiler,
        )
    elif profile.html_extract_ok and profile.robots_can_fetch_homepage:
        status, html = fetch_text(profile.homepage_url or profile.normalized_url)
        if status < 400 and html:
            candidates = discover_internal_links(
                source_id=source_id,
                homepage_url=profile.homepage_url or profile.normalized_url,
                html=html,
                max_items=MAX_DISCOVERED_URLS,
                db=db,
            )
    return candidates[:MAX_DISCOVERED_URLS]


def validate_source(
    *,
    entry: dict[str, str],
    profiler: SourceProfiler,
    db: WebIntelDB,
    raw_store: RawStore,
    http: CachedHttpClient,
    rules: Any,
) -> dict[str, Any]:
    meta = response_meta(entry["url"], timeout=rules.request_timeout_seconds, user_agent=rules.user_agent)
    profile = profiler.profile_source(entry["url"])
    discovered = discover_candidates(profile=profile, db=db, raw_store=raw_store, http=http, rules=rules)
    discovered_urls = []
    client = httpx.Client(
        headers={"User-Agent": rules.user_agent},
        follow_redirects=True,
        timeout=rules.request_timeout_seconds,
    )
    try:
        article_results: list[dict[str, Any]] = []
        for row in discovered[:MAX_DISCOVERED_URLS]:
            url = str(row.get("url") or "").strip()
            if not url:
                continue
            discovered_urls.append(url)
            try:
                raw_metadata = json.loads(str(row.get("raw_metadata") or "{}"))
            except json.JSONDecodeError:
                raw_metadata = {}
            feed_summary = str(raw_metadata.get("feed_summary") or "").strip()
            if len(feed_summary) >= MIN_FEED_SUMMARY_LENGTH and str(row.get("title") or "").strip():
                effective_title = str(row.get("title") or "").strip()
                effective_published = str(row.get("published_at") or "").strip() or None
                text_blob = " ".join((effective_title, feed_summary, url))
                article_results.append(
                    {
                        "url": url,
                        "title": effective_title,
                        "published_at": effective_published,
                        "content_length": len(feed_summary),
                        "extract_ok": True,
                        "feed_summary_fallback": True,
                        "paywall_detected": False,
                        "login_detected": False,
                        "captcha_detected": False,
                        "published_recent": published_is_recent(effective_published),
                        # Entries in this catalog are manually curated direct
                        # technology feeds. Do not require every individual
                        # headline to repeat an AI keyword during source-level
                        # readiness validation.
                        "looks_tech": True,
                    }
                )
                continue
            if profile.has_rss and profile.input_url in profile.rss_urls:
                # Keep live validation bounded and conservative for direct
                # feeds: a headline-only feed is not counted as usable content.
                # Production may still deep-fetch its article pages, but that
                # is not enough to pass the source readiness gate here.
                article_results.append(
                    {
                        "url": url,
                        "title": str(row.get("title") or "").strip() or None,
                        "published_at": str(row.get("published_at") or "").strip() or None,
                        "content_length": len(feed_summary),
                        "extract_ok": False,
                        "feed_summary_fallback": False,
                        "paywall_detected": False,
                        "login_detected": False,
                        "captcha_detected": False,
                        "published_recent": published_is_recent(row.get("published_at")),
                        "looks_tech": True,
                    }
                )
                continue
            art = extract_article(
                url,
                profile.source_id,
                profile.best_strategy,
                rules=rules,
                raw_store=raw_store,
                client=client,
            )
            use_feed_summary = (
                (not art.extract_ok or int(art.content_length or 0) < MIN_CONTENT_LENGTH)
                and len(feed_summary) >= MIN_FEED_SUMMARY_LENGTH
            )
            effective_title = art.title or row.get("title")
            effective_published = art.published_at or row.get("published_at")
            effective_content = feed_summary if use_feed_summary else (art.content or "")
            effective_length = len(effective_content) if use_feed_summary else int(art.content_length or 0)
            text_blob = " ".join(
                part for part in [effective_title or "", effective_content, url] if part
            )
            article_results.append(
                {
                    "url": url,
                    "title": effective_title,
                    "published_at": effective_published,
                    "content_length": effective_length,
                    "extract_ok": bool(
                        (use_feed_summary or (art.extract_ok and int(art.content_length or 0) >= MIN_CONTENT_LENGTH))
                        and str(effective_title or "").strip()
                    ),
                    "feed_summary_fallback": use_feed_summary,
                    "paywall_detected": bool(art.paywall_detected),
                    "login_detected": bool(art.login_detected),
                    "captcha_detected": bool(art.captcha_detected),
                    "published_recent": published_is_recent(effective_published),
                    "looks_tech": text_looks_tech(text_blob),
                }
            )
    finally:
        client.close()

    status = classify_source(
        meta=meta,
        profile=profile,
        discovered_count=len(discovered_urls),
        article_results=article_results,
        requires_playwright=bool(profile.best_strategy == "playwright_fallback" or profile.js_required),
    )
    production_ready = status in PASS_STATUSES
    return {
        "source_id": profile.source_id,
        "name": entry["name"],
        "input_url": entry["url"],
        "domain": host_from_url(entry["url"]),
        "normalized_url": profile.normalized_url,
        "final_url": meta.get("final_url") or profile.normalized_url,
        "redirect_chain": meta.get("redirect_chain") or [],
        "http_status": int(meta.get("http_status") or 0),
        "content_type": str(meta.get("content_type") or ""),
        "robots_can_fetch_homepage": bool(profile.robots_can_fetch_homepage),
        "robots_disallow_detected": bool(profile.robots_disallow_detected),
        "has_rss": bool(profile.has_rss),
        "has_sitemap": bool(profile.has_sitemap),
        "html_extract_ok": bool(profile.html_extract_ok),
        "js_required": bool(profile.js_required),
        "paywall_detected": bool(profile.paywall_detected),
        "login_detected": bool(profile.login_detected),
        "captcha_detected": bool(profile.captcha_detected),
        "best_strategy": str(profile.best_strategy),
        "discovered_article_urls": discovered_urls,
        "discovered_article_count": len(discovered_urls),
        "article_samples": article_results,
        "validation_status": status,
        "production_ready": production_ready,
        "notes": str(profile.error_message or meta.get("error") or ""),
    }


def write_seed_files(report: dict[str, Any]) -> None:
    active = [src for src in report["sources"] if src["validation_status"] in PASS_STATUSES]
    disabled = [src for src in report["sources"] if src["validation_status"] not in PASS_STATUSES]

    active_lines = [
        "# LeonQuant — validated active technology / AI sources",
        "# Auto-generated by scripts/validate_tech_sources.py",
        "",
    ]
    disabled_lines = [
        "# LeonQuant — disabled or review-needed technology / AI sources",
        "# Auto-generated by scripts/validate_tech_sources.py",
        "",
    ]
    tiers: dict[str, list[str]] = defaultdict(list)
    manifest: dict[str, str] = {}

    for src in active:
        active_lines.append(f"# {src['name']} [{src['validation_status']}]")
        active_lines.append(src["input_url"])
        tier_file = ACTIVE_TIER_FILE_BY_STATUS[src["validation_status"]]
        tiers[tier_file].append(src["domain"])
        manifest[src["domain"]] = tier_file[:-4]

    for src in disabled:
        disabled_lines.append(f"# {src['name']} [{src['validation_status']}]")
        disabled_lines.append(src["input_url"])

    ensure_parent(TECH_ACTIVE)
    TECH_ACTIVE.write_text("\n".join(active_lines).strip() + "\n", encoding="utf-8")
    ensure_parent(TECH_DISABLED)
    TECH_DISABLED.write_text("\n".join(disabled_lines).strip() + "\n", encoding="utf-8")

    TECH_TIERS_DIR.mkdir(parents=True, exist_ok=True)
    for existing in TECH_TIERS_DIR.glob("*.txt"):
        existing.unlink()
    for tier_file, domains in sorted(tiers.items()):
        content = [
            "# Auto-generated by scripts/validate_tech_sources.py",
            f"# {tier_file}",
            *sorted(set(domains)),
            "",
        ]
        (TECH_TIERS_DIR / tier_file).write_text("\n".join(content), encoding="utf-8")
    dump_json(TECH_TIERS_MANIFEST, manifest)


def write_markdown(report: dict[str, Any]) -> None:
    counts = Counter(src["validation_status"] for src in report["sources"])
    sample_successes = sum(
        1
        for src in report["sources"]
        for art in src.get("article_samples") or []
        if art.get("extract_ok")
    )
    recheck = [src for src in report["sources"] if src["validation_status"] in RECHECK_STATUSES]
    lines = [
        "# Tech Source Validation",
        "",
        f"- Generated at: `{report['validation_meta']['generated_at_utc']}`",
        f"- Total sources in catalog: **{report['validation_meta']['catalog_source_count']}**",
        f"- Active sources: **{report['validation_meta']['active_source_count']}**",
        f"- Disabled or review-needed: **{report['validation_meta']['disabled_source_count']}**",
        f"- Sample extracts that passed content/title thresholds: **{sample_successes}**",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in sorted(counts.items()):
        lines.append(f"- `{status}`: {count}")
    lines += [
        "",
        "## Sources Needing Leon Review",
        "",
    ]
    if not recheck:
        lines.append("- None")
    else:
        for src in recheck:
            lines.append(
                f"- `{src['validation_status']}` — {src['name']} — {src['input_url']}"
            )
    lines += [
        "",
        "## Per-source Snapshot",
        "",
        "name | status | strategy | urls | extract_ok | notes",
        "--- | --- | --- | ---: | ---: | ---",
    ]
    for src in report["sources"]:
        ok_count = sum(1 for art in src.get("article_samples") or [] if art.get("extract_ok"))
        notes = str(src.get("notes") or "").replace("\n", " ")[:140]
        lines.append((
            f"{src['name']} | {src['validation_status']} | {src['best_strategy']} | "
            f"{src['discovered_article_count']} | {ok_count} | {notes}"
        ).rstrip())
    ensure_parent(TECH_VALIDATION_MD)
    TECH_VALIDATION_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_fixture_report(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("sources"), list):
        raise ValueError("Fixture must be an object with sources[]")
    report = {
        "schema_version": VALIDATION_SCHEMA,
        "validation_meta": {
            "generated_at_utc": _now_utc().isoformat(),
            "catalog_source_count": int(payload.get("catalog_source_count") or len(payload["sources"])),
            "active_source_count": 0,
            "disabled_source_count": 0,
            "report_valid": True,
            "fixture_mode": True,
        },
        "sources": payload["sources"],
    }
    report["validation_meta"]["active_source_count"] = sum(
        1 for src in report["sources"] if src.get("validation_status") in PASS_STATUSES
    )
    report["validation_meta"]["disabled_source_count"] = len(report["sources"]) - int(
        report["validation_meta"]["active_source_count"]
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate tech/AI sources before enabling production.")
    parser.add_argument("--input", type=Path, default=TECH_CATALOG)
    parser.add_argument("--output-json", type=Path, default=TECH_VALIDATION_JSON)
    parser.add_argument("--output-md", type=Path, default=TECH_VALIDATION_MD)
    parser.add_argument("--fixture", type=Path, default=None, help="Use fixture JSON instead of live validation")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--force-refresh", action="store_true")
    args = parser.parse_args()

    if args.fixture is not None:
        report = build_fixture_report(args.fixture)
        dump_json(args.output_json, report)
        write_seed_files(report)
        write_markdown(report)
        print(f"Wrote fixture validation report -> {args.output_json}")
        print(f"Wrote active sources -> {TECH_ACTIVE}")
        return 0

    entries = parse_catalog(args.input)
    if args.limit > 0:
        entries = entries[: args.limit]

    rules = load_crawl_rules(LEON_ROOT / "config" / "crawl_rules.yaml")
    if args.input.resolve() == TECH_CATALOG.resolve():
        with ThreadPoolExecutor(max_workers=min(12, max(1, len(entries)))) as pool:
            sources = list(pool.map(lambda entry: validate_direct_feed_source(entry, rules=rules), entries))
        counts = Counter(src["validation_status"] for src in sources)
        report = {
            "schema_version": VALIDATION_SCHEMA,
            "validation_meta": {
                "generated_at_utc": _now_utc().isoformat(),
                "catalog_source_count": len(entries),
                "active_source_count": sum(1 for src in sources if src["validation_status"] in PASS_STATUSES),
                "disabled_source_count": sum(1 for src in sources if src["validation_status"] not in PASS_STATUSES),
                "report_valid": True,
                "fixture_mode": False,
                "direct_feed_mode": True,
                "status_counts": dict(counts),
            },
            "sources": sources,
        }
        dump_json(args.output_json, report)
        write_seed_files(report)
        write_markdown(report)
        print(f"Wrote direct-feed validation report -> {args.output_json}")
        print(f"Active direct feeds -> {TECH_ACTIVE}")
        return 0

    REPORT_DB = TECH_VALIDATION_DB
    REPORT_DB.parent.mkdir(parents=True, exist_ok=True)

    http = CachedHttpClient(rules, cache_dir=LEON_ROOT / "data" / "cache" / "http", profile_cache_days=0)
    db = WebIntelDB(REPORT_DB)
    raw_store = RawStore(LEON_ROOT / "data" / "raw")
    profiler = SourceProfiler(rules=rules, http=http, db=db, raw_store=raw_store)

    try:
        sources = [
            validate_source(entry=entry, profiler=profiler, db=db, raw_store=raw_store, http=http, rules=rules)
            for entry in entries
        ]
    finally:
        http.close()
        db.close()

    counts = Counter(src["validation_status"] for src in sources)
    report = {
        "schema_version": VALIDATION_SCHEMA,
        "validation_meta": {
            "generated_at_utc": _now_utc().isoformat(),
            "catalog_source_count": len(entries),
            "active_source_count": sum(1 for src in sources if src["validation_status"] in PASS_STATUSES),
            "disabled_source_count": sum(1 for src in sources if src["validation_status"] not in PASS_STATUSES),
            "report_valid": True,
            "fixture_mode": False,
            "status_counts": dict(counts),
        },
        "sources": sources,
    }
    dump_json(args.output_json, report)
    write_seed_files(report)
    write_markdown(report)

    if args.output_md != TECH_VALIDATION_MD:
        ensure_parent(args.output_md)
        args.output_md.write_text(TECH_VALIDATION_MD.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote validation report -> {args.output_json}")
    print(f"Wrote markdown report -> {TECH_VALIDATION_MD}")
    print(f"Active sources -> {TECH_ACTIVE}")
    print(f"Disabled sources -> {TECH_DISABLED}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
