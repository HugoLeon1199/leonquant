#!/usr/bin/env python3
"""Run the standalone tech crawl/export/clean pipeline after Phase 0 validation."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from scripts.tech_common import (
    TECH_ACTIVE,
    TECH_NEWS_ALL,
    TECH_NEWS_FOR_AI,
    TECH_NEWS_FOR_AI_CLEAN,
    TECH_NEWS_TODAY,
    TECH_TIERS_DIR,
    TECH_TIERS_MANIFEST,
    validation_report_is_ready,
)

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> int:
    print("+", " ".join(cmd), flush=True)
    return subprocess.call(cmd, cwd=ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validated tech crawl -> export -> clean")
    parser.add_argument("--db", type=Path, default=ROOT / "data" / "web_intel_tech.duckdb")
    parser.add_argument("--seed", type=Path, default=TECH_ACTIVE)
    parser.add_argument("--tiers-dir", type=Path, default=TECH_TIERS_DIR)
    parser.add_argument("--manifest", type=Path, default=TECH_TIERS_MANIFEST)
    parser.add_argument("--output-today", type=Path, default=TECH_NEWS_TODAY)
    parser.add_argument("--output-all", type=Path, default=TECH_NEWS_ALL)
    parser.add_argument("--ai-output", type=Path, default=TECH_NEWS_FOR_AI)
    parser.add_argument("--clean-output", type=Path, default=TECH_NEWS_FOR_AI_CLEAN)
    parser.add_argument("--date", default="today")
    parser.add_argument("--timezone", default="Asia/Ho_Chi_Minh")
    parser.add_argument("--skip-profile", action="store_true")
    parser.add_argument("--min-clean-articles", type=int, default=5)
    args = parser.parse_args()

    ok, reason = validation_report_is_ready()
    if not ok:
        print(f"ERROR: {reason}", file=sys.stderr)
        print("Run scripts/validate_tech_sources.py first.", file=sys.stderr)
        return 2
    if not args.seed.is_file():
        print(f"ERROR: missing active seed file: {args.seed}", file=sys.stderr)
        return 2
    if not args.tiers_dir.is_dir():
        print(f"ERROR: missing active tiers dir: {args.tiers_dir}", file=sys.stderr)
        return 2

    py = sys.executable
    crawl_cmd = [
        py,
        str(ROOT / "scripts" / "run_intel_full_daily.py"),
        "--date",
        args.date,
        "--timezone",
        args.timezone,
        "--db",
        str(args.db),
        "--seed",
        str(args.seed),
        "--tiers-dir",
        str(args.tiers_dir),
        "--output-today",
        str(args.output_today),
        "--output-all",
        str(args.output_all),
    ]
    if args.skip_profile:
        crawl_cmd.append("--skip-profile")
    rc = run(crawl_cmd)
    if rc != 0:
        return rc

    rc = run(
        [
            py,
            str(ROOT / "scripts" / "export_intel_to_news_output.py"),
            "--db",
            str(args.db),
            "--date",
            args.date,
            "--timezone",
            args.timezone,
            "--manifest",
            str(args.manifest),
            "--output-today",
            str(args.output_today),
            "--output-all",
            str(args.output_all),
        ]
    )
    if rc != 0:
        return rc

    rc = run(
        [
            py,
            str(ROOT / "scripts" / "export_news_full_for_ai.py"),
            "--db",
            str(args.db),
            "--date",
            args.date,
            "--timezone",
            args.timezone,
            "--output",
            str(args.ai_output),
        ]
    )
    if rc != 0:
        return rc

    rc = run(
        [
            py,
            str(ROOT / "scripts" / "clean_news_for_ai.py"),
            "--input",
            str(args.ai_output),
            "--output",
            str(args.clean_output),
            "--min-text-chars",
            "500",
        ]
    )
    if rc != 0:
        return rc

    import json

    data = json.loads(args.clean_output.read_text(encoding="utf-8"))
    n = len(data.get("articles") or [])
    print(f"Clean tech AI articles: {n}")
    if n < args.min_clean_articles:
        print(
            f"ERROR: need >= {args.min_clean_articles} clean tech articles; got {n}",
            file=sys.stderr,
        )
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
