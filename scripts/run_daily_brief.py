#!/usr/bin/env python3
"""Pipeline chính: crawl (tuỳ) → export → clean → Gemini digest → content.json (tuỳ)."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], *, cwd: Path | None = None) -> int:
    print("+", " ".join(cmd), flush=True)
    return subprocess.call(cmd, cwd=cwd or ROOT)


def _gemini_key_ok() -> bool:
    if os.environ.get("GEMINI_API_KEY", "").strip():
        return True
    env_path = ROOT / ".env"
    if not env_path.is_file():
        return False
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("GEMINI_API_KEY="):
            val = line.split("=", 1)[1].strip().strip('"').strip("'")
            return bool(val) and val != "your-gemini-api-key"
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Crawl → news_for_ai_clean → Gemini digest → web")
    parser.add_argument("--skip-crawl", action="store_true", help="Bỏ run_intel_full_daily")
    parser.add_argument("--skip-profile", action="store_true", help="Truyền --skip-profile cho crawl")
    parser.add_argument("--skip-digest", action="store_true", help="Chỉ export + clean")
    parser.add_argument("--skip-clean", action="store_true", help="Dùng news_for_ai.json thô")
    parser.add_argument("--build-site", action="store_true", help="Sinh content.json sau digest")
    parser.add_argument("--skip-images", action="store_true", help="Không fetch og:image khi build web")
    parser.add_argument("--recent-calendar-days", type=int, default=2)
    parser.add_argument(
        "--digest-loop",
        action="store_true",
        help="Chạy scripts/run_digest_loop.py (1 API call/lần, free tier)",
    )
    args = parser.parse_args()

    py = sys.executable
    clean_path = ROOT / "news_for_ai_clean.json"

    if not args.skip_crawl:
        crawl_cmd = [
            py,
            str(ROOT / "scripts" / "run_intel_full_daily.py"),
            "--date",
            "today",
            "--timezone",
            "Asia/Ho_Chi_Minh",
        ]
        if args.skip_profile:
            crawl_cmd.append("--skip-profile")
        rc = run(crawl_cmd)
        if rc != 0:
            return rc

    rc = run(
        [
            py,
            str(ROOT / "scripts" / "export_news_full_for_ai.py"),
            "--date",
            "today",
            "--recent-calendar-days",
            str(args.recent_calendar_days),
        ]
    )
    if rc != 0:
        return rc

    ai_input = ROOT / "news_for_ai.json"
    if not args.skip_clean:
        rc = run(
            [
                py,
                str(ROOT / "scripts" / "clean_news_for_ai.py"),
                "--input",
                str(ai_input),
                "--output",
                str(clean_path),
            ]
        )
        if rc != 0:
            return rc
        digest_input = clean_path
    else:
        digest_input = ai_input

    if args.skip_digest:
        if args.build_site:
            digest_path = ROOT / "gemini_digest_summary.json"
            if not digest_path.is_file():
                print(f"ERROR: missing {digest_path}", file=sys.stderr)
                return 2
            return _build_site(py, digest_path, digest_input, args.skip_images)
        return 0

    if not _gemini_key_ok():
        print(
            f"Missing GEMINI_API_KEY. Set env or copy {ROOT / '.env.example'} → {ROOT / '.env'}.",
            file=sys.stderr,
        )
        return 2

    if args.digest_loop:
        rc = run([py, str(ROOT / "scripts" / "run_digest_loop.py")])
    else:
        rc = run(
            [
                py,
                str(ROOT / "summarize_news_gemini.py"),
                "--input",
                str(digest_input),
                "--mode",
                "digest",
                "--batch-digest",
                "--model",
                os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite"),
                "--use-existing-outline",
                "--resume-partials",
                "--min-request-interval",
                "60",
                "--api-pause",
                "60",
            ]
        )
    if rc != 0:
        return rc

    if args.build_site:
        return _build_site(py, ROOT / "gemini_digest_summary.json", digest_input, args.skip_images)
    return 0


def _build_site(py: str, digest_path: Path, articles_path: Path, skip_images: bool) -> int:
    cmd = [
        py,
        str(ROOT / "build_website_content.py"),
        "--digest-input",
        str(digest_path),
        "--enriched-input",
        str(articles_path),
    ]
    if skip_images:
        cmd.append("--skip-images")
    return run(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
