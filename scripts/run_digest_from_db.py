#!/usr/bin/env python3
"""DB → export → clean → Gemini digest → content.json (no crawl)."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

QUANT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = QUANT_ROOT / "scripts"
PY = sys.executable
DEFAULT_WINDOW_STATE = QUANT_ROOT / "data" / "digest_export_window.json"
ENV_FILE = QUANT_ROOT / ".env"


def _load_env_file() -> None:
    if not ENV_FILE.is_file():
        return
    for line in ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        k = key.strip()
        if k and not os.environ.get(k):
            os.environ[k] = value.strip().strip('"').strip("'")


def _gemini_key_ok() -> bool:
    _load_env_file()
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    return bool(key) and key != "your-gemini-api-key"


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> int:
    print("\n===== RUN =====")
    print(" ".join(cmd))
    return int(subprocess.call(cmd, cwd=str(QUANT_ROOT), env=env))


def main() -> int:
    parser = argparse.ArgumentParser(description="Digest from existing DuckDB (no Scrapy)")
    parser.add_argument("--db", type=Path, default=QUANT_ROOT / "data" / "web_intel_leonquant.duckdb")
    parser.add_argument("--date", default="today")
    parser.add_argument("--timezone", default="Asia/Ho_Chi_Minh")
    parser.add_argument(
        "--recent-calendar-days",
        type=int,
        default=0,
        help="Fallback when no window state file (0 = use state file or 2)",
    )
    parser.add_argument(
        "--window-state",
        type=Path,
        default=DEFAULT_WINDOW_STATE,
        help="Written by prepare_digest_db.py; keeps export aligned with gate",
    )
    parser.add_argument("--skip-gemini", action="store_true")
    parser.add_argument("--skip-web", action="store_true")
    parser.add_argument(
        "--skip-invest-vn",
        action="store_true",
        help="Skip invest_vn_brief.json (tab đầu tư khối VN)",
    )
    parser.add_argument("--min-clean-articles", type=int, default=1)
    args = parser.parse_args()

    db = args.db.resolve()
    if not db.is_file():
        print(f"ERROR: DuckDB not found: {db}", file=sys.stderr)
        return 2

    window_state = args.window_state.resolve()
    if not window_state.is_file():
        print(
            f"ERROR: missing {window_state.name} — run scripts/prepare_digest_db.py after crawl first.",
            file=sys.stderr,
        )
        return 2

    pin = subprocess.check_output(
        [PY, str(SCRIPTS / "pin_crawl_calendar_date.py"), "--date", args.date, "--timezone", args.timezone],
        cwd=str(QUANT_ROOT),
        text=True,
    ).strip()
    print(f"Calendar date: {pin} ({args.timezone})")

    export_cmd = [
        PY,
        str(SCRIPTS / "export_news_full_for_ai.py"),
        "--db",
        str(db),
        "--date",
        pin,
        "--timezone",
        args.timezone,
        "--window-state",
        str(window_state),
        "--clean",
    ]
    if args.recent_calendar_days > 0:
        export_cmd.extend(["--recent-calendar-days", str(args.recent_calendar_days)])

    rc = run(export_cmd)
    if rc != 0:
        return rc

    rc = run([PY, str(SCRIPTS / "clean_news_for_ai.py"), "--keep-listings", "--no-dedupe", "--min-text-chars", "0"])
    if rc != 0:
        return rc

    clean_path = QUANT_ROOT / "news_for_ai_clean.json"
    data = json.loads(clean_path.read_text(encoding="utf-8"))
    n = len(data.get("articles") or [])
    print(f"Articles for Gemini: {n}")
    if n < args.min_clean_articles:
        print(
            f"ERROR: need >= {args.min_clean_articles} articles in {clean_path.name} "
            f"(export window state: {window_state})",
            file=sys.stderr,
        )
        return 5

    if not args.skip_gemini:
        if not _gemini_key_ok():
            print(
                f"ERROR: set GEMINI_API_KEY (env or {ENV_FILE.name}) for Gemini digest",
                file=sys.stderr,
            )
            return 2
        for stale in ("gemini_digest_summary.json", "gemini_digest_partials.json", "gemini_digest_outline.json"):
            p = QUANT_ROOT / stale
            if p.is_file():
                p.unlink()
        env = os.environ.copy()
        env["DIGEST_LOOP_FORCE"] = "1"
        rc = run([PY, str(SCRIPTS / "run_digest_loop.py")], env=env)
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
        if not args.skip_invest_vn:
            rc = run(
                [
                    PY,
                    str(SCRIPTS / "build_invest_vn_brief.py"),
                    "--content",
                    str(QUANT_ROOT / "content.json"),
                ]
            )
            if rc != 0:
                return rc

    print(
        "\nDone: news_for_ai_clean.json"
        + ("" if args.skip_web else " + content.json")
        + ("" if args.skip_web or args.skip_invest_vn else " + invest_vn_brief.json")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
