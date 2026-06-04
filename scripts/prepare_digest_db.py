#!/usr/bin/env python3
"""Gate before Gemini digest: resolve export window after crawl; write shared state file."""

from __future__ import annotations

import argparse
import gzip
import shutil
import subprocess
import sys
from pathlib import Path

QUANT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from digest_window import (  # noqa: E402
    CALENDAR_DAY_LADDER,
    DEFAULT_DB,
    DEFAULT_GZ,
    DEFAULT_WINDOW_STATE,
    MIN_ARTICLES_DEFAULT,
    MIN_SOURCE_PROFILES,
    ROLLING_HOURS_FALLBACK,
    db_diagnostics,
    open_db,
    resolve_export_window,
    write_window_state,
)


def reseed_from_gz(db_path: Path, gz_path: Path) -> None:
    if not gz_path.is_file():
        print(f"ERROR: seed not found: {gz_path}", file=sys.stderr)
        raise SystemExit(2)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.is_file():
        db_path.unlink()
    with gzip.open(gz_path, "rb") as fin, open(db_path, "wb") as fout:
        shutil.copyfileobj(fin, fout)
    mb = db_path.stat().st_size / 1024 / 1024
    print(f"Bootstrapped {db_path.name} from {gz_path.name} ({mb:.1f} MB)")


def count_profiles(db_path: Path) -> int:
    db = open_db(db_path)
    try:
        return int(db.conn.execute("SELECT COUNT(*) FROM source_profiles").fetchone()[0])
    finally:
        db.close()


def pin_date(date: str, timezone: str) -> str:
    return subprocess.check_output(
        [
            sys.executable,
            str(QUANT_ROOT / "scripts" / "pin_crawl_calendar_date.py"),
            "--date",
            date,
            "--timezone",
            timezone,
        ],
        text=True,
    ).strip()


def try_resolve(
    db_path: Path, *, date: str, timezone: str, min_articles: int, label: str
) -> dict | None:
    diag = db_diagnostics(db_path)
    print(f"[{label}] DB: {diag}")
    state = resolve_export_window(
        db_path, date=date, timezone_name=timezone, min_articles=min_articles
    )
    if state:
        print(
            f"[{label}] OK mode={state['mode']} "
            f"calendar_days={state.get('recent_calendar_days')} "
            f"rolling_hours={state.get('rolling_hours')} "
            f"articles={state['article_count']}"
        )
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare DuckDB + export window for 48h digest")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--gz", type=Path, default=DEFAULT_GZ)
    parser.add_argument("--date", default="today")
    parser.add_argument("--timezone", default="Asia/Ho_Chi_Minh")
    parser.add_argument("--min-articles", type=int, default=MIN_ARTICLES_DEFAULT)
    parser.add_argument("--window-state", type=Path, default=DEFAULT_WINDOW_STATE)
    args = parser.parse_args()

    db = args.db.resolve()
    gz = args.gz.resolve()

    if not db.is_file():
        if gz.is_file():
            reseed_from_gz(db, gz)
        else:
            print(f"ERROR: DuckDB missing and no {gz.name} to bootstrap.", file=sys.stderr)
            return 2

    profiles = count_profiles(db)
    if profiles < MIN_SOURCE_PROFILES:
        if gz.is_file():
            print(f"Only {profiles} source_profiles — bootstrap from {gz.name}")
            reseed_from_gz(db, gz)
            profiles = count_profiles(db)
        if profiles < MIN_SOURCE_PROFILES:
            print(
                f"ERROR: need >= {MIN_SOURCE_PROFILES} source_profiles in DuckDB.\n"
                "  Chạy profile tay (một lần / khi đổi link): "
                "cd leon_web_intel && python run_profile.py --input ../config/sources_seed.txt "
                "--profile-only --db ../data/web_intel_leonquant.duckdb\n"
                "  Rồi: python scripts/pack_db_seed.py --mode profiles-only",
                file=sys.stderr,
            )
            return 2

    pin = pin_date(args.date, args.timezone)
    print(f"Pinned calendar date: {pin} ({args.timezone})")

    state = try_resolve(db, date=pin, timezone=args.timezone, min_articles=args.min_articles, label="post-crawl")
    if not state:
        print(
            f"ERROR: fewer than {args.min_articles} articles in digest window "
            f"(calendar {list(CALENDAR_DAY_LADDER)}d or rolling {ROLLING_HOURS_FALLBACK}h).\n"
            "  Xem log bước Crawl; cache Actions cần tích lũy bài qua các lần chạy.\n"
            "  Local: python scripts/run_intel_full_daily.py --skip-profile --no-crawl-skip",
            file=sys.stderr,
        )
        return 5

    out = write_window_state(state, args.window_state)
    print(f"Wrote export window -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
