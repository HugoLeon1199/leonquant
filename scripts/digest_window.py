"""Shared digest export window — one source of truth for CI export, prune, and gate."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

QUANT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WINDOW_STATE = QUANT_ROOT / "data" / "digest_export_window.json"
DEFAULT_DB = QUANT_ROOT / "data" / "web_intel_leonquant.duckdb"
DEFAULT_GZ = QUANT_ROOT / "data" / "web_intel_leonquant.duckdb.gz"

# Smallest calendar window first; widen only when cache/crawl is thin.
CALENDAR_DAY_LADDER = (2, 3, 5, 7, 14)
ROLLING_HOURS_FALLBACK = 48
MIN_ARTICLES_DEFAULT = 10
MIN_CONTENT_CHARS = 200
MIN_SOURCE_PROFILES = 10


def intel_root() -> Path:
    vendored = QUANT_ROOT / "leon_web_intel"
    if (vendored / "src" / "storage" / "db.py").is_file():
        return vendored
    return QUANT_ROOT.parent / "leon_web_intel"


def open_db(db_path: Path):
    import sys

    root = intel_root()
    sys.path.insert(0, str(root / "src"))
    from storage.db import WebIntelDB  # noqa: E402

    return WebIntelDB(db_path.resolve())


def count_calendar_articles(
    db_path: Path, *, date: str, timezone_name: str, recent_calendar_days: int
) -> int:
    db = open_db(db_path)
    try:
        rows = db.fetch_today_articles(
            target_date_str=date,
            timezone_name=timezone_name,
            recent_calendar_days=max(1, recent_calendar_days),
        )
        return len(rows)
    finally:
        db.close()


def count_rolling_articles(db_path: Path, *, hours: int = ROLLING_HOURS_FALLBACK) -> int:
    h = max(1, int(hours))
    db = open_db(db_path)
    try:
        row = db.conn.execute(
            f"""
            SELECT COUNT(*) FROM articles
            WHERE extracted_at >= CURRENT_TIMESTAMP - INTERVAL {h} HOUR
              AND COALESCE(content_length, 0) >= {MIN_CONTENT_CHARS}
            """
        ).fetchone()
        return int(row[0] if row else 0)
    finally:
        db.close()


def db_diagnostics(db_path: Path) -> dict[str, Any]:
    db = open_db(db_path)
    try:
        total = int(db.conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0])
        profiles = int(db.conn.execute("SELECT COUNT(*) FROM source_profiles").fetchone()[0])
        max_ext = db.conn.execute("SELECT MAX(extracted_at) FROM articles").fetchone()[0]
        rolling = count_rolling_articles(db_path)
        return {
            "articles_total": total,
            "source_profiles": profiles,
            "latest_extracted_at": str(max_ext) if max_ext is not None else None,
            "rolling_48h_articles": rolling,
        }
    finally:
        db.close()


def resolve_export_window(
    db_path: Path,
    *,
    date: str,
    timezone_name: str,
    min_articles: int = MIN_ARTICLES_DEFAULT,
) -> dict[str, Any] | None:
    """Pick smallest usable window; prefer calendar days, else rolling 48h by extracted_at."""
    for days in CALENDAR_DAY_LADDER:
        n = count_calendar_articles(
            db_path, date=date, timezone_name=timezone_name, recent_calendar_days=days
        )
        if n >= min_articles:
            return {
                "mode": "calendar",
                "recent_calendar_days": days,
                "rolling_hours": None,
                "article_count": n,
                "min_articles": min_articles,
                "end_date": date,
                "timezone": timezone_name,
            }

    rolling = count_rolling_articles(db_path)
    if rolling >= min_articles:
        return {
            "mode": "rolling",
            "recent_calendar_days": CALENDAR_DAY_LADDER[0],
            "rolling_hours": ROLLING_HOURS_FALLBACK,
            "article_count": rolling,
            "min_articles": min_articles,
            "end_date": date,
            "timezone": timezone_name,
        }
    return None


def write_window_state(state: dict[str, Any], path: Path = DEFAULT_WINDOW_STATE) -> Path:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(state)
    payload["written_at_utc"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_window_state(path: Path = DEFAULT_WINDOW_STATE) -> dict[str, Any] | None:
    p = path.resolve()
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def prune_calendar_days_from_state(state: dict[str, Any]) -> int:
    """Keep at least export window; never prune tighter than articles were exported."""
    if state.get("mode") == "rolling":
        return max(CALENDAR_DAY_LADDER[0], 3)
    return max(int(state.get("recent_calendar_days") or CALENDAR_DAY_LADDER[0]), 3)


def recent_calendar_day_set(
    end_date_str: str | None,
    timezone_name: str,
    num_days: int,
) -> set[date]:
    """Local calendar dates covered by the export window (inclusive end day)."""
    sys_path = intel_root() / "src"
    import sys

    if str(sys_path) not in sys.path:
        sys.path.insert(0, str(sys_path))
    from utils.today_filter import resolve_calendar_date  # noqa: E402

    anchor = resolve_calendar_date(end_date_str, timezone_name)
    n = max(1, int(num_days))
    return {anchor - timedelta(days=i) for i in range(n)}


def _parse_article_datetime(val: Any) -> datetime | None:
    if val is None:
        return None
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "null"):
        return None
    sys_path = intel_root() / "src"
    import sys

    if str(sys_path) not in sys.path:
        sys.path.insert(0, str(sys_path))
    from utils.today_filter import parse_any_datetime  # noqa: E402

    return parse_any_datetime(s)


def article_local_calendar_day(
    art: dict[str, Any],
    *,
    timezone_name: str,
) -> date | None:
    """Best-effort local publish day; falls back to extracted_at when publish is missing."""
    pub_dt = _parse_article_datetime(art.get("published_at"))
    if pub_dt is not None:
        return pub_dt.astimezone(ZoneInfo(timezone_name)).date()
    for key in ("extracted_at", "extractedAt"):
        ext_dt = _parse_article_datetime(art.get(key))
        if ext_dt is not None:
            return ext_dt.astimezone(ZoneInfo(timezone_name)).date()
    return None


def filter_articles_recent_calendar_days(
    articles: list[dict[str, Any]],
    *,
    end_date_str: str | None,
    timezone_name: str = "Asia/Ho_Chi_Minh",
    num_days: int = 2,
) -> list[dict[str, Any]]:
    """Keep articles whose publish day (or crawl day if publish missing) is in the window."""
    allowed = recent_calendar_day_set(end_date_str, timezone_name, num_days)
    out: list[dict[str, Any]] = []
    for art in articles:
        if not isinstance(art, dict):
            continue
        day = article_local_calendar_day(art, timezone_name=timezone_name)
        if day is not None and day in allowed:
            out.append(art)
    return out
