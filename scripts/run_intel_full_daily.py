#!/usr/bin/env python3
"""Leon Quant: profile seed sources, then Scrapy (today-mode) per tier → ``news_output_today.json``.

Engine: vendored ``leon_web_intel/`` or ``LEON_WEB_INTEL_ROOT``. Does **not** run Gemini/GPT/build web.

**Profile vs crawl**
  - First run (empty DB) or after you change ``config/sources_seed.txt`` / tiers / ``crawl_rules.yaml``:
    run **without** ``--skip-profile`` so ``run_profile.py`` refreshes DuckDB ``source_profiles``.
  - Day-to-day (profiles already OK): use ``--skip-profile`` — only Scrapy + export; much faster.

**Typical**
  python scripts/run_intel_full_daily.py --date today --timezone Asia/Ho_Chi_Minh
  python scripts/run_intel_full_daily.py --date today --timezone Asia/Ho_Chi_Minh --skip-profile
  Full re-profile (ignore 7-day cache) then crawl:
  python scripts/run_intel_full_daily.py --date today --timezone Asia/Ho_Chi_Minh --force-refresh-profile
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

QUANT_ROOT = Path(__file__).resolve().parents[1]


def intel_root() -> Path:
    env = os.environ.get("LEON_WEB_INTEL_ROOT")
    if env:
        return Path(env).resolve()
    vendored = QUANT_ROOT / "leon_web_intel"
    if (vendored / "run_profile.py").is_file():
        return vendored
    return QUANT_ROOT.parent / "leon_web_intel"


def resolve_crawl_calendar_date(date_arg: str, tz_name: str) -> str:
    """Pin ``today`` once per run so Scrapy and export use the same calendar day."""
    s = date_arg.strip()
    if s.lower() == "today":
        return datetime.now(ZoneInfo(tz_name)).date().isoformat()
    return s


def run(cmd: list[str], *, cwd: Path, timeout: int | None = None) -> int:
    print("")
    print("===== RUN =====")
    print(" ".join(cmd))
    try:
        p = subprocess.run(cmd, cwd=str(cwd), timeout=timeout)  # noqa: S603
    except subprocess.TimeoutExpired:
        print("TIMEOUT")
        return 124
    return int(p.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Profiler + tiered Scrapy → news_output_today.json")
    parser.add_argument("--date", default="today")
    parser.add_argument("--timezone", default="Asia/Ho_Chi_Minh")
    parser.add_argument(
        "--db",
        type=Path,
        default=QUANT_ROOT / "data" / "web_intel_leonquant.duckdb",
        help="Dedicated DuckDB for Leon Quant (not global web_intel)",
    )
    parser.add_argument("--seed", type=Path, default=QUANT_ROOT / "config" / "sources_seed.txt")
    parser.add_argument("--tiers-dir", type=Path, default=QUANT_ROOT / "config" / "tiers")
    parser.add_argument("--strategy", choices=("rss", "sitemap", "html", "all"), default="all")
    parser.add_argument("--profile-limit", type=int, default=0)
    parser.add_argument("--max-urls-per-source", type=int, default=50)
    parser.add_argument("--close-spider-timeout", type=int, default=3600)
    parser.add_argument("--skip-profile", action="store_true")
    parser.add_argument(
        "--force-refresh-profile",
        action="store_true",
        help="Pass --force-refresh to run_profile.py (re-profile every source; ignores 7-day cache).",
    )
    parser.add_argument("--profile-timeout", type=int, default=None)
    parser.add_argument("--tier-timeout", type=int, default=None)
    parser.add_argument(
        "--output-today",
        type=Path,
        default=QUANT_ROOT / "news_output_today.json",
        help="Articles for --date in --timezone",
    )
    parser.add_argument(
        "--output-all",
        type=Path,
        default=QUANT_ROOT / "news_output_all.json",
        help="All articles in DuckDB (any day)",
    )
    parser.add_argument(
        "--no-crawl-skip",
        action="store_true",
        help="Retry sources on source_crawl_skip (e.g. after access-control rule change)",
    )
    parser.add_argument(
        "--with-observability",
        action="store_true",
        help="Chạy thêm baseline/coverage/zero-article reports (debug, chậm hơn)",
    )
    parser.add_argument(
        "--require-today-articles",
        type=int,
        default=0,
        help="Exit 5 if news_output_today.json has fewer than N articles after export.",
    )
    args = parser.parse_args()

    crawl_date = resolve_crawl_calendar_date(args.date, args.timezone)
    if args.date.strip().lower() == "today":
        print(f"Crawl/export calendar date (pinned): {crawl_date} ({args.timezone})")

    if args.skip_profile and args.force_refresh_profile:
        print("ERROR: --force-refresh-profile cannot be used with --skip-profile", file=sys.stderr)
        return 2

    root = intel_root()
    if not (root / "run_profile.py").is_file():
        print(f"ERROR: leon_web_intel not found at {root}", file=sys.stderr)
        print(
            "Set LEON_WEB_INTEL_ROOT, clone github.com/HugoLeon1199/Crawl-Web-Repository, "
            "or use the vendored leonquant/leon_web_intel tree.",
            file=sys.stderr,
        )
        return 2

    py = sys.executable
    db = args.db.resolve()
    db.parent.mkdir(parents=True, exist_ok=True)

    tier_files = sorted(args.tiers_dir.glob("*.txt"))
    if not tier_files:
        print(f"ERROR: no tier files in {args.tiers_dir}; run scripts/split_sources_seed_into_tiers.py", file=sys.stderr)
        return 2

    if not args.skip_profile:
        profile_cmd = [
            py,
            "run_profile.py",
            "--input",
            str(args.seed.resolve()),
            "--profile-only",
            "--db",
            str(db),
        ]
        if args.profile_limit and args.profile_limit > 0:
            profile_cmd.extend(["--limit", str(args.profile_limit)])
        if args.force_refresh_profile:
            profile_cmd.append("--force-refresh")
        rc = run(profile_cmd, cwd=root, timeout=args.profile_timeout)
        if rc != 0:
            return rc

    for tier_path in tier_files:
        print(f"\n--- Tier file: {tier_path.name} ---")
        rc = run(
            [
                py,
                "run_scrapy.py",
                "--db",
                str(db),
                "--strategy",
                args.strategy,
                "--limit",
                str(args.profile_limit),
                "--today-only",
                "--date",
                crawl_date,
                "--timezone",
                args.timezone,
                "--max-urls-per-source",
                str(args.max_urls_per_source),
                "--close-spider-timeout",
                str(args.close_spider_timeout),
                "--domain-allowlist-file",
                str(tier_path.resolve()),
            ]
            + (["--no-crawl-skip"] if args.no_crawl_skip else []),
            cwd=root,
            timeout=args.tier_timeout,
        )
        if rc != 0:
            print(f"WARN: tier {tier_path.name} exited {rc}", file=sys.stderr)

    skip_refresh = run(
        [
            py,
            str((QUANT_ROOT / "scripts" / "refresh_source_crawl_skip.py").resolve()),
            "--db",
            str(db),
        ],
        cwd=QUANT_ROOT,
        timeout=120,
    )
    if skip_refresh != 0:
        print(f"WARN: refresh_source_crawl_skip exited {skip_refresh}", file=sys.stderr)

    export_rc = run(
        [
            py,
            str((QUANT_ROOT / "scripts" / "export_intel_to_news_output.py").resolve()),
            "--db",
            str(db),
            "--date",
            crawl_date,
            "--timezone",
            args.timezone,
            "--output-today",
            str(args.output_today.resolve()),
            "--today-only",
            "--recent-calendar-days",
            "2",
        ],
        cwd=QUANT_ROOT,
        timeout=None,
    )
    if args.with_observability:
        for post, post_args in (
            ("crawl_baseline_snapshot.py", [str(db)]),
            ("source_coverage_report.py", [str(db)]),
            ("investigate_zero_article_sources.py", []),
        ):
            post_rc = run(
                [py, str((QUANT_ROOT / "scripts" / post).resolve()), *post_args],
                cwd=QUANT_ROOT,
                timeout=120,
            )
            if post_rc != 0:
                print(f"WARN: {post} exited {post_rc}", file=sys.stderr)

    if args.require_today_articles > 0 and export_rc == 0 and args.output_today.is_file():
        import json

        try:
            payload = json.loads(args.output_today.read_text(encoding="utf-8"))
            n = len(payload.get("articles") or [])
        except (OSError, json.JSONDecodeError, TypeError):
            n = 0
        print(f"Today export articles: {n} (required >= {args.require_today_articles})")
        if n < args.require_today_articles:
            print("ERROR: today export below required article count.", file=sys.stderr)
            return 5

    return export_rc


if __name__ == "__main__":
    raise SystemExit(main())
