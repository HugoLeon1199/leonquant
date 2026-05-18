#!/usr/bin/env python3
"""Leon Quant: profile once on full seed, then Scrapy today-mode per tier → news_output.json.

Requires sibling repo ``leon_web_intel`` (or ``LEON_WEB_INTEL_ROOT``). Does **not** run Gemini/GPT/build web.

Typical:
  python scripts/run_intel_full_daily.py --date today --timezone Asia/Ho_Chi_Minh
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

QUANT_ROOT = Path(__file__).resolve().parents[1]


def intel_root() -> Path:
    env = os.environ.get("LEON_WEB_INTEL_ROOT")
    if env:
        return Path(env).resolve()
    return QUANT_ROOT.parent / "leon_web_intel"


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
    parser = argparse.ArgumentParser(description="Profiler + tiered Scrapy → news_output.json")
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
    parser.add_argument("--profile-timeout", type=int, default=None)
    parser.add_argument("--tier-timeout", type=int, default=None)
    parser.add_argument("--news-output", type=Path, default=QUANT_ROOT / "news_output.json")
    args = parser.parse_args()

    root = intel_root()
    if not (root / "run_profile.py").is_file():
        print(f"ERROR: leon_web_intel not found at {root}", file=sys.stderr)
        print("Set LEON_WEB_INTEL_ROOT or place leon_web_intel next to leonquant.", file=sys.stderr)
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
                args.date,
                "--timezone",
                args.timezone,
                "--max-urls-per-source",
                str(args.max_urls_per_source),
                "--close-spider-timeout",
                str(args.close_spider_timeout),
                "--domain-allowlist-file",
                str(tier_path.resolve()),
            ],
            cwd=root,
            timeout=args.tier_timeout,
        )
        if rc != 0:
            print(f"WARN: tier {tier_path.name} exited {rc}", file=sys.stderr)

    return run(
        [
            py,
            str((QUANT_ROOT / "scripts" / "export_intel_to_news_output.py").resolve()),
            "--db",
            str(db),
            "--date",
            args.date,
            "--timezone",
            args.timezone,
            "--output",
            str(args.news_output.resolve()),
        ],
        cwd=QUANT_ROOT,
        timeout=None,
    )


if __name__ == "__main__":
    raise SystemExit(main())
