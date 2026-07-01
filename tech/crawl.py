#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tech.common import ACTIVE, NEWS_CLEAN, NEWS_RAW, TIERS_DIR, VALIDATION_JSON, load_json

DB = ROOT / "data" / "web_intel_tech.duckdb"
TIMEZONE = "Asia/Ho_Chi_Minh"


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


def validation_ready() -> None:
    report = load_json(VALIDATION_JSON, {})
    meta = report.get("validation_meta") or {}
    if not meta.get("report_valid") or int(meta.get("active_source_count") or 0) <= 0:
        raise SystemExit("Tech source validation is missing or invalid.")
    if not ACTIVE.is_file() or not list(TIERS_DIR.glob("*.txt")):
        raise SystemExit("Validated active source and tier files are missing.")


def has_profiles(db_path: Path) -> bool:
    if not db_path.is_file():
        return False
    try:
        import duckdb
        con = duckdb.connect(str(db_path), read_only=True)
        try:
            return int(con.execute("SELECT COUNT(*) FROM source_profiles").fetchone()[0]) > 0
        finally:
            con.close()
    except Exception:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Crawl latest three tech calendar days and export a 72h window.")
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--timezone", default=TIMEZONE)
    parser.add_argument("--max-urls-per-source", type=int, default=30)
    parser.add_argument("--min-clean-articles", type=int, default=5)
    args = parser.parse_args()

    validation_ready()
    py = sys.executable
    args.db.parent.mkdir(parents=True, exist_ok=True)
    if not has_profiles(args.db):
        run([
            py, "leon_web_intel/run_profile.py",
            "--input", str(ACTIVE), "--profile-only",
            "--db", str(args.db), "--force-refresh",
        ])

    today = datetime.now(ZoneInfo(args.timezone)).date()
    temp_dir = ROOT / "tech" / "data" / "crawl_days"
    temp_dir.mkdir(parents=True, exist_ok=True)
    for offset in (2, 1, 0):
        day = (today - timedelta(days=offset)).isoformat()
        run([
            py, "scripts/run_intel_full_daily.py",
            "--date", day, "--timezone", args.timezone,
            "--db", str(args.db), "--seed", str(ACTIVE),
            "--tiers-dir", str(TIERS_DIR), "--skip-profile", "--no-crawl-skip",
            "--max-urls-per-source", str(args.max_urls_per_source),
            "--output-today", str(temp_dir / f"{day}.json"),
            "--output-all", str(temp_dir / "all.json"),
        ])

    run([
        py, "scripts/export_news_full_for_ai.py",
        "--db", str(args.db), "--timezone", args.timezone,
        "--rolling-hours", "72", "--output", str(NEWS_RAW),
    ])
    run([
        py, "scripts/clean_news_for_ai.py",
        "--input", str(NEWS_RAW), "--output", str(NEWS_CLEAN),
        "--min-text-chars", "500",
    ])
    payload = json.loads(NEWS_CLEAN.read_text(encoding="utf-8"))
    count = len(payload.get("articles") or [])
    print(f"Clean technology articles in the latest 72 hours: {count}")
    if count < args.min_clean_articles:
        raise SystemExit(f"Need at least {args.min_clean_articles} clean articles; got {count}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
