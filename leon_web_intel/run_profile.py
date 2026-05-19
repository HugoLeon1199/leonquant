#!/usr/bin/env python3
"""CLI entry for profiling + lightweight sample crawling."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx
from loguru import logger

# project roots
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from collectors.html_collector import discover_internal_links  # noqa: E402
from collectors.playwright_fallback import fetch_rendered_html  # noqa: E402
from collectors.rss_collector import discover_from_rss  # noqa: E402
from collectors.sitemap_collector import discover_from_sitemap  # noqa: E402
from extraction.article_extractor import compute_quality_score, extract_article  # noqa: E402
from extraction.metadata_extractor import extract_meta_description  # noqa: E402
from profiler.normalize import dedupe_sources, normalize_url  # noqa: E402
from profiler.paywall_detector import detect_paywall_signals  # noqa: E402
from profiler.source_profiler import SourceProfiler  # noqa: E402
from reporting.profile_report import console_strategy_counts, write_profile_summary  # noqa: E402
from settings import load_crawl_rules  # noqa: E402
from storage.db import WebIntelDB, new_id, utc_now  # noqa: E402
from storage.raw_store import RawStore  # noqa: E402
from utils.cache import CachedHttpClient  # noqa: E402
from utils.hashing import sha256_text  # noqa: E402
from utils.logging_config import configure_logging  # noqa: E402


def read_source_lines(path: Path) -> list[str]:
    out: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out.append(s)
    return out


def dry_run(urls: list[str], *, raw_nonempty_lines: int) -> None:
    norms = []
    for u in urls:
        try:
            norms.append(normalize_url(u))
        except Exception as exc:  # noqa: BLE001
            logger.warning("invalid url skipped {}: {}", u, exc)
    uniq = dedupe_sources(norms)
    print("===== DRY RUN =====")
    print(f"Total raw lines: {raw_nonempty_lines}")
    print(f"Valid URLs: {len(urls)}")
    print(f"Unique sources: {len(uniq)}")
    print("Preview:")
    print("source_id | normalized_url | domain")
    for n in uniq[:20]:
        print(f"{n.source_id} | {n.normalized_url} | {n.domain}")


def ensure_dirs() -> None:
    for sub in ("data/db", "data/exports", "data/cache/http", "logs"):
        (ROOT / sub).mkdir(parents=True, exist_ok=True)


def export_outputs(db: WebIntelDB, export_csv: bool, export_parquet: bool) -> None:
    exports = ROOT / "data" / "exports"
    exports.mkdir(parents=True, exist_ok=True)
    if export_csv:
        db.export_source_profiles_csv(exports / "source_profiles.csv")
        db.export_review_sources_csv(exports / "review_sources.csv")
        db.export_review_sources_strict_csv(exports / "review_sources_strict.csv")
    if export_parquet:
        db.export_source_profiles_parquet(exports / "source_profiles.parquet")
    write_profile_summary(db, exports / "profile_summary.md")


def print_profile_summary(db: WebIntelDB) -> None:
    counts = console_strategy_counts(db)
    print("")
    print("===== PROFILE SUMMARY =====")
    rows = db.fetch_all_profiles()
    print(f"Total sources: {len(rows)}")
    print(f"RSS: {counts.get('rss_then_article_extract', 0)}")
    print(f"Sitemap: {counts.get('sitemap_then_article_extract', 0)}")
    print(f"HTML: {counts.get('html_then_trafilatura', 0)}")
    print(f"Playwright fallback: {counts.get('playwright_fallback', 0)}")
    print(f"Metadata only: {counts.get('metadata_only', 0)}")
    print(f"Manual review: {counts.get('manual_review', 0)}")
    print("Exports:")
    print(f"  CSV: {ROOT / 'data' / 'exports' / 'source_profiles.csv'}")
    print(f"  Parquet: {ROOT / 'data' / 'exports' / 'source_profiles.parquet'}")
    print(f"  Review CSV: {ROOT / 'data' / 'exports' / 'review_sources.csv'}")
    print(f"  Review strict: {ROOT / 'data' / 'exports' / 'review_sources_strict.csv'}")
    print(f"  Summary MD: {ROOT / 'data' / 'exports' / 'profile_summary.md'}")
    print(f"Database: {db.db_path.resolve()}")
    print("")


def existing_hashes(db: WebIntelDB) -> set[str]:
    return db.fetch_distinct_content_hashes()


def robots_allows_homepage_row(row: dict) -> bool:
    v = row.get("robots_can_fetch_homepage")
    if v is None:
        return True
    return bool(v)


def crawl_samples(
    *,
    db: WebIntelDB,
    http: CachedHttpClient,
    raw_store: RawStore,
    rules,
    source_filter: set[str],
    max_articles: int,
    with_playwright: bool,
) -> None:
    profiles = [r for r in db.fetch_all_profiles() if r.get("source_id") in source_filter]
    hash_set = existing_hashes(db)

    client = httpx.Client(
        headers={"User-Agent": rules.user_agent},
        timeout=rules.request_timeout_seconds,
        follow_redirects=True,
    )
    try:
        for row in profiles:
            sid = row["source_id"]
            strategy = row.get("best_strategy") or ""
            status = row.get("status") or ""
            source_active = status in ("active", "active_candidate")

            def fetch_text(u: str) -> tuple[int, str]:
                return http.get_text(u)

            def fetch_bytes(u: str) -> tuple[int, bytes]:
                e = http.get(u)
                return e.status_code, e.body

            try:
                if strategy == "manual_review":
                    continue

                if strategy == "metadata_only":
                    title = row.get("html_title") or ""
                    url = row.get("homepage_url") or row.get("normalized_url") or ""
                    desc = ""
                    if url and robots_allows_homepage_row(row):
                        st, html = fetch_text(url)
                        if st < 400:
                            desc = extract_meta_description(html) or ""
                    content = (title + "\n\n" + desc).strip() or title
                    content_length = len(content)
                    content_hash = sha256_text(content)
                    q = compute_quality_score(
                        title=title,
                        content_length=content_length,
                        published_at=None,
                        source_active=source_active,
                        content_hash=content_hash,
                        url=url or sid,
                        strategy=strategy,
                        raw_path="",
                        extract_ok=bool(content),
                        paywall_triplet=(
                            bool(row.get("paywall_detected")),
                            bool(row.get("login_detected")),
                            bool(row.get("captcha_detected")),
                        ),
                        existing_hashes=hash_set,
                    )
                    db.insert_article(
                        {
                            "id": new_id(),
                            "source_id": sid,
                            "url": url,
                            "title": title,
                            "published_at": None,
                            "content": content,
                            "content_length": content_length,
                            "content_hash": content_hash,
                            "language": None,
                            "crawl_strategy_used": strategy,
                            "raw_path": "",
                            "extracted_at": utc_now(),
                            "quality_score": float(q),
                        }
                    )
                    if content_hash:
                        hash_set.add(content_hash)
                    continue

                discovered: list[dict] = []

                if strategy == "rss_then_article_extract":
                    rss_urls = json.loads(row.get("rss_urls") or "[]")
                    if rss_urls:
                        discovered.extend(
                            discover_from_rss(
                                source_id=sid,
                                rss_url=rss_urls[0],
                                max_items=max_articles,
                                fetch_text=fetch_text,
                                raw_store=raw_store,
                                db=db,
                            )
                        )

                elif strategy == "sitemap_then_article_extract":
                    sm_urls = json.loads(row.get("sitemap_urls") or "[]")
                    if sm_urls:
                        discovered.extend(
                            discover_from_sitemap(
                                source_id=sid,
                                sitemap_url=sm_urls[0],
                                max_items=max_articles,
                                fetch_bytes=fetch_bytes,
                                raw_store=raw_store,
                                db=db,
                                max_urls_probe=rules.max_urls_from_sitemap_in_profiler,
                            )
                        )

                elif strategy == "html_then_trafilatura":
                    if not robots_allows_homepage_row(row):
                        db.insert_crawl_error(
                            {
                                "id": new_id(),
                                "source_id": sid,
                                "url": row.get("homepage_url") or "",
                                "stage": "sample_crawl",
                                "error_type": "RobotsDisallowHomepage",
                                "error_message": "Skipping HTML link crawl: robots disallow homepage fetch",
                                "created_at": utc_now(),
                            }
                        )
                        continue
                    hp = row.get("homepage_url") or row.get("normalized_url") or ""
                    if hp:
                        st, html = fetch_text(hp)
                        if st < 400:
                            discovered.extend(
                                discover_internal_links(
                                    source_id=sid,
                                    homepage_url=hp,
                                    html=html,
                                    max_items=max_articles,
                                    db=db,
                                )
                            )

                elif strategy == "playwright_fallback":
                    if not robots_allows_homepage_row(row):
                        db.insert_crawl_error(
                            {
                                "id": new_id(),
                                "source_id": sid,
                                "url": row.get("homepage_url") or "",
                                "stage": "sample_crawl",
                                "error_type": "RobotsDisallowHomepage",
                                "error_message": "Skipping Playwright: robots disallow homepage fetch",
                                "created_at": utc_now(),
                            }
                        )
                        continue
                    if not with_playwright:
                        db.insert_crawl_error(
                            {
                                "id": new_id(),
                                "source_id": sid,
                                "url": row.get("homepage_url") or "",
                                "stage": "sample_crawl",
                                "error_type": "PlaywrightDisabled",
                                "error_message": "playwright_fallback requires --with-playwright",
                                "created_at": utc_now(),
                            }
                        )
                        continue
                    hp = row.get("homepage_url") or row.get("normalized_url") or ""
                    rendered = fetch_rendered_html(hp) if hp else None
                    if not rendered:
                        continue
                    pay = detect_paywall_signals(rendered, rules)
                    if pay.paywall_detected or pay.login_detected or pay.captcha_detected:
                        db.insert_crawl_error(
                            {
                                "id": new_id(),
                                "source_id": sid,
                                "url": hp,
                                "stage": "extract",
                                "error_type": "AccessControlDetected",
                                "error_message": f"paywall={pay.paywall_detected} login={pay.login_detected} captcha={pay.captcha_detected}",
                                "created_at": utc_now(),
                            }
                        )
                        continue
                    try:
                        import trafilatura

                        text = trafilatura.extract(rendered) or ""
                        title = row.get("html_title") or ""
                        if len(text.strip()) >= rules.min_article_content_length:
                            content_hash = sha256_text(text)
                            q = compute_quality_score(
                                title=title,
                                content_length=len(text),
                                published_at=None,
                                source_active=source_active,
                                content_hash=content_hash,
                                url=hp,
                                strategy=strategy,
                                raw_path="",
                                extract_ok=True,
                                paywall_triplet=(False, False, False),
                                existing_hashes=hash_set,
                            )
                            db.insert_article(
                                {
                                    "id": new_id(),
                                    "source_id": sid,
                                    "url": hp,
                                    "title": title,
                                    "published_at": None,
                                    "content": text,
                                    "content_length": len(text),
                                    "content_hash": content_hash,
                                    "language": None,
                                    "crawl_strategy_used": strategy,
                                    "raw_path": "",
                                    "extracted_at": utc_now(),
                                    "quality_score": float(q),
                                }
                            )
                            hash_set.add(content_hash)
                    except Exception as exc:  # noqa: BLE001
                        db.insert_crawl_error(
                            {
                                "id": new_id(),
                                "source_id": sid,
                                "url": hp,
                                "stage": "playwright_extract",
                                "error_type": type(exc).__name__,
                                "error_message": str(exc),
                                "created_at": utc_now(),
                            }
                        )
                    continue

                for disc in discovered[:max_articles]:
                    url = disc["url"]
                    art = extract_article(
                        url,
                        sid,
                        strategy,
                        rules=rules,
                        raw_store=raw_store,
                        client=client,
                    )
                    if art.paywall_detected or art.login_detected or art.captcha_detected:
                        db.insert_crawl_error(
                            {
                                "id": new_id(),
                                "source_id": sid,
                                "url": url,
                                "stage": "extract",
                                "error_type": "AccessControlDetected",
                                "error_message": (
                                    f"paywall={art.paywall_detected} login={art.login_detected} captcha={art.captcha_detected}"
                                ),
                                "created_at": utc_now(),
                            }
                        )
                        continue
                    if strategy != "metadata_only" and art.content_length < rules.min_article_content_length:
                        db.insert_crawl_error(
                            {
                                "id": new_id(),
                                "source_id": sid,
                                "url": url,
                                "stage": "extract",
                                "error_type": "ShortContent",
                                "error_message": f"len={art.content_length}",
                                "created_at": utc_now(),
                            }
                        )
                        continue
                    q = compute_quality_score(
                        title=art.title,
                        content_length=art.content_length,
                        published_at=art.published_at,
                        source_active=source_active,
                        content_hash=art.content_hash,
                        url=url,
                        strategy=strategy,
                        raw_path=art.raw_path,
                        extract_ok=art.extract_ok,
                        paywall_triplet=(
                            art.paywall_detected,
                            art.login_detected,
                            art.captcha_detected,
                        ),
                        existing_hashes=hash_set,
                    )
                    db.insert_article(
                        {
                            "id": new_id(),
                            "source_id": sid,
                            "url": url,
                            "title": art.title,
                            "published_at": art.published_at,
                            "content": art.content or "",
                            "content_length": art.content_length,
                            "content_hash": art.content_hash,
                            "language": art.language,
                            "crawl_strategy_used": strategy,
                            "raw_path": art.raw_path,
                            "extracted_at": utc_now(),
                            "quality_score": float(q),
                        }
                    )
                    if art.content_hash:
                        hash_set.add(art.content_hash)

            except Exception as exc:  # noqa: BLE001
                logger.exception("sample crawl failed for {}: {}", sid, exc)
                db.insert_crawl_error(
                    {
                        "id": new_id(),
                        "source_id": sid,
                        "url": row.get("homepage_url") or "",
                        "stage": "sample_crawl",
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                        "created_at": utc_now(),
                    }
                )
    finally:
        client.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Leon Global Web Intelligence Engine — profiler CLI")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="DuckDB path (default: ./data/db/web_intel.duckdb)",
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--profile-only", action="store_true")
    parser.add_argument("--crawl-sample", action="store_true")
    parser.add_argument("--max-articles-per-source", type=int, default=None)
    parser.add_argument("--with-playwright", action="store_true")
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument("--cache-days", type=int, default=None)
    parser.add_argument("--concurrency", type=int, default=None)
    parser.add_argument("--export-csv", action="store_true", default=True)
    parser.add_argument("--no-export-csv", action="store_true")
    parser.add_argument("--export-parquet", action="store_true", default=True)
    parser.add_argument("--no-export-parquet", action="store_true")
    parser.add_argument(
        "--skip-profiling",
        action="store_true",
        help="Skip profile_many; use existing source_profiles in DuckDB (requires --crawl-sample)",
    )

    args = parser.parse_args(argv)

    if args.skip_profiling:
        if not args.crawl_sample:
            parser.error("--skip-profiling requires --crawl-sample")
        if args.profile_only:
            parser.error("--skip-profiling cannot be combined with --profile-only")

    ensure_dirs()
    log_path = ROOT / "logs" / "app.log"
    configure_logging(log_path)

    urls = read_source_lines(args.input)

    if args.dry_run:
        raw = Path(args.input).read_text(encoding="utf-8").splitlines()
        nonempty = len([ln for ln in raw if ln.strip()])
        dry_run(urls, raw_nonempty_lines=nonempty)
        return 0

    rules = load_crawl_rules(ROOT / "config" / "crawl_rules.yaml")

    if args.concurrency is not None:
        rules = rules.model_copy(update={"concurrency": args.concurrency})
    max_art = args.max_articles_per_source or rules.sample_max_articles_per_source

    norms = []
    for u in urls:
        try:
            norms.append(normalize_url(u))
        except Exception:
            continue
    uniq = dedupe_sources(norms)
    if args.limit is not None and args.limit > 0:
        uniq = uniq[: args.limit]
    source_ids = {n.source_id for n in uniq}

    db_path = (args.db if args.db is not None else ROOT / "data" / "db" / "web_intel.duckdb").resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = WebIntelDB(db_path)
    raw_store = RawStore(ROOT / "data" / "raw")
    cache_dir = ROOT / "data" / "cache" / "http"
    cache_days = args.cache_days if args.cache_days is not None else rules.profile_cache_days
    http = CachedHttpClient(rules, cache_dir=cache_dir, profile_cache_days=cache_days)

    export_csv = args.export_csv and not args.no_export_csv
    export_parquet = args.export_parquet and not args.no_export_parquet

    try:
        # Safe default: profiling unless user explicitly chose crawl-only via --crawl-sample alone is allowed
        if not args.profile_only and not args.crawl_sample:
            args.profile_only = True

        if (args.profile_only or args.crawl_sample) and not args.skip_profiling:
            profiler = SourceProfiler(rules=rules, http=http, db=db, raw_store=raw_store)
            profiler.profile_many(
                [n.input_url for n in uniq],
                limit=None,
                concurrency=args.concurrency,
                cache_days=cache_days,
                force_refresh=args.force_refresh,
            )
            export_outputs(db, export_csv, export_parquet)
            print_profile_summary(db)

        if args.crawl_sample:
            crawl_samples(
                db=db,
                http=http,
                raw_store=raw_store,
                rules=rules,
                source_filter=source_ids,
                max_articles=max_art,
                with_playwright=args.with_playwright,
            )
            export_outputs(db, export_csv, export_parquet)
            print_profile_summary(db)
        return 0
    finally:
        http.close()
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())