#!/usr/bin/env python3
"""DB → export → clean → Gemini digest → content.json (no crawl)."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

QUANT_ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> int:
    print("\n===== RUN =====")
    print(" ".join(cmd))
    return int(subprocess.call(cmd, cwd=str(QUANT_ROOT), env=env))


def main() -> int:
    parser = argparse.ArgumentParser(description="Digest from existing DuckDB (no Scrapy)")
    parser.add_argument("--db", type=Path, default=QUANT_ROOT / "data" / "web_intel_leonquant.duckdb")
    parser.add_argument("--date", default="today")
    parser.add_argument("--timezone", default="Asia/Ho_Chi_Minh")
    parser.add_argument("--recent-calendar-days", type=int, default=2)
    parser.add_argument("--skip-gemini", action="store_true")
    parser.add_argument("--skip-web", action="store_true")
    parser.add_argument("--min-clean-articles", type=int, default=1)
    args = parser.parse_args()

    db = args.db.resolve()
    if not db.is_file():
        print(f"ERROR: DuckDB not found: {db}", file=sys.stderr)
        return 2

    pin = subprocess.check_output(
        [PY, str(QUANT_ROOT / "scripts" / "pin_crawl_calendar_date.py"), "--date", args.date, "--timezone", args.timezone],
        cwd=str(QUANT_ROOT),
        text=True,
    ).strip()
    print(f"Calendar date: {pin} ({args.timezone})")

    rc = run(
        [
            PY,
            str(QUANT_ROOT / "scripts" / "export_news_full_for_ai.py"),
            "--db",
            str(db),
            "--date",
            pin,
            "--timezone",
            args.timezone,
            "--recent-calendar-days",
            str(args.recent_calendar_days),
            "--clean",
        ]
    )
    if rc != 0:
        return rc

    rc = run([PY, str(QUANT_ROOT / "scripts" / "clean_news_for_ai.py")])
    if rc != 0:
        return rc

    import json

    clean_path = QUANT_ROOT / "news_for_ai_clean.json"
    data = json.loads(clean_path.read_text(encoding="utf-8"))
    n = len(data.get("articles") or [])
    print(f"Articles for Gemini: {n}")
    if n < args.min_clean_articles:
        print(f"ERROR: need >= {args.min_clean_articles} articles in {clean_path.name}", file=sys.stderr)
        return 5

    if not args.skip_gemini:
        if not os.environ.get("GEMINI_API_KEY"):
            print("ERROR: set GEMINI_API_KEY for Gemini digest", file=os.stderr)
            return 2
        for stale in ("gemini_digest_summary.json", "gemini_digest_partials.json", "gemini_digest_outline.json"):
            p = QUANT_ROOT / stale
            if p.is_file():
                p.unlink()
        env = os.environ.copy()
        env["DIGEST_LOOP_FORCE"] = "1"
        rc = run([PY, str(QUANT_ROOT / "scripts" / "run_digest_loop.py")], env=env)
        if rc != 0:
            return rc

    if not args.skip_web:
        summary = QUANT_ROOT / "gemini_digest_summary.json"
        if not summary.is_file():
            print(f"ERROR: missing {summary.name} (run Gemini or pass existing file)", file=sys.stderr)
            return 2
        rc = run(
            [
                PY,
                str(QUANT_ROOT / "build_website_content.py"),
                "--digest-input",
                str(summary),
                "--enriched-input",
                str(clean_path),
                "--skip-images",
            ]
        )
        if rc != 0:
            return rc
        rc = run(
            [
                PY,
                str(QUANT_ROOT / "validate_content.py"),
                "--content-input",
                str(QUANT_ROOT / "content.json"),
            ]
        )
        if rc != 0:
            return rc

    print("\nDone: news_for_ai_clean.json" + ("" if args.skip_web else " + content.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
