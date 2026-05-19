#!/usr/bin/env python3
"""Production crawl layer (Scrapy) — runs after SourceProfiler wrote DuckDB profiles."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scrapy_engine.db_source_loader import domains_from_allowlist_file  # noqa: E402
from scrapy_engine.runner import run_scrapy_engine  # noqa: E402
from utils.full_run import resolve_max_urls_per_source  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="Leon Web Intel — Scrapy crawl layer (post-profiler)")
    p.add_argument(
        "--strategy",
        choices=("rss", "sitemap", "html", "all"),
        default="all",
        help="Which profiler strategies to crawl (maps to rss/sitemap/html spiders)",
    )
    p.add_argument("--limit", type=int, default=50, help="Max sources per spider lane (0 = all)")
    p.add_argument(
        "--max-articles-per-source",
        type=int,
        default=5,
        help="Cap article URL attempts per source (sample mode; ignored as primary cap when --today-only)",
    )
    p.add_argument(
        "--db",
        type=Path,
        default=ROOT / "data" / "db" / "web_intel.duckdb",
        help="Path to DuckDB written by run_profile.py",
    )
    p.add_argument("--run-id", default=None, help="Optional crawl_runs.run_id (orchestration meta)")
    p.add_argument(
        "--close-spider-timeout",
        type=int,
        default=600,
        metavar="SEC",
        help="Scrapy CLOSESPIDER_TIMEOUT (wall-clock seconds for entire crawl)",
    )
    p.add_argument(
        "--today-only",
        action="store_true",
        help="Public-discovery mode: filter to target calendar day (RSS dates / sitemap lastmod / URL heuristics)",
    )
    p.add_argument(
        "--date",
        default="today",
        metavar="DATE",
        help='Calendar day as YYYY-MM-DD or the literal "today" (interpreted in --timezone)',
    )
    p.add_argument(
        "--timezone",
        default="Asia/Ho_Chi_Minh",
        metavar="TZ",
        help="IANA timezone for interpreting --date and RSS/sitemap day bounds",
    )
    p.add_argument(
        "--max-urls-per-source",
        type=int,
        default=1000,
        metavar="N",
        help="Per-source URL/article attempt budget (today & wide); 0 = full-run ceiling (~2M)",
    )
    p.add_argument(
        "--domain-allowlist-file",
        type=Path,
        default=None,
        metavar="PATH",
        help="Leon Quant tier file: only crawl sources whose domain is listed (URL or hostname per line).",
    )
    p.add_argument(
        "--no-crawl-skip",
        action="store_true",
        help="Ignore source_crawl_skip / sources_uncrawlable.txt (retry blocked sources).",
    )
    args = p.parse_args()

    allow_path = args.domain_allowlist_file
    if allow_path is not None:
        allow_path = allow_path.resolve()
        if not allow_path.is_file():
            p.error(f"--domain-allowlist-file not found: {allow_path}")

    resolved_cap = resolve_max_urls_per_source(args.max_urls_per_source)
    # Single per-source budget from --max-urls-per-source (today-only spiders still filter to target day in pipeline).
    max_art_eff = int(resolved_cap)

    allowed = domains_from_allowlist_file(allow_path)

    summary = run_scrapy_engine(
        root=ROOT,
        strategy=args.strategy,
        limit=args.limit,
        max_articles_per_source=max_art_eff,
        db_path=args.db,
        run_id=args.run_id,
        close_spider_timeout=args.close_spider_timeout,
        today_only=bool(args.today_only),
        target_date=args.date,
        timezone_name=args.timezone,
        max_urls_per_source=int(resolved_cap),
        allowed_domains=allowed,
        respect_crawl_skip=not args.no_crawl_skip,
    )

    print("")
    print("===== SCRAPY RUN SUMMARY =====")
    print(f"Sources loaded (all lanes): {summary.sources_loaded}")
    print(f"HTTP requests scheduled (approx): {summary.requests_scheduled}")
    print(f"Pipeline items processed: {summary.pipeline_items}")
    print(f"Articles inserted: {summary.articles_inserted}")
    print(f"Crawl errors logged: {summary.errors_logged}")
    print(f"Duplicate content hashes skipped: {summary.duplicates_skipped}")
    print(
        f"Per-source budget: today_only={bool(args.today_only)} "
        f"max_urls_per_source={resolved_cap} effective_max_articles_per_source={max_art_eff}"
    )
    if args.run_id:
        print(f"Run ID: {args.run_id}")
    print(f"Database: {args.db.resolve()}")
    print("")


if __name__ == "__main__":
    main()
