"""Date/time helpers for \"today\" full-article crawl mode (timezone-aware)."""

from __future__ import annotations

import calendar
import email.utils
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from dateutil import parser as date_parser


def parse_any_datetime(value: str | None) -> datetime | None:
    """Parse RSS dates, ISO-8601, W3C lastmod, RFC822, YYYY-MM-DD → timezone-aware UTC."""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None

    # Plain calendar date
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        d = date.fromisoformat(s)
        return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)

    # RFC822 / RFC2822 (HTTP Date, RSS pubDate)
    try:
        dt = email.utils.parsedate_to_datetime(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        pass

    # ISO / W3CDTF / loose formats
    try:
        dt = date_parser.parse(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, OverflowError, TypeError):
        return None


def parse_datetime_from_feedparser_struct(t: Any) -> datetime | None:
    """Convert ``published_parsed`` / ``updated_parsed`` time tuples to UTC."""
    if not t:
        return None
    try:
        if isinstance(t, datetime):
            dt = t
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        # time.struct_time — feedparser uses UTC for *_parsed
        if hasattr(t, "tm_year"):
            secs = calendar.timegm(t)
            return datetime.fromtimestamp(secs, tz=timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None
    return None


def resolve_calendar_date(date_str: str | None, timezone_name: str) -> date:
    """Resolve ``today`` or ``YYYY-MM-DD`` in the named IANA timezone."""
    tz = ZoneInfo(timezone_name)
    now_local = datetime.now(tz)
    if date_str is None or str(date_str).strip().lower() in ("", "today"):
        return now_local.date()
    return date.fromisoformat(str(date_str).strip())


def target_date_range(date_str: str | None, timezone_name: str) -> tuple[datetime, datetime]:
    """
    Inclusive start, exclusive end in UTC for the target calendar day in ``timezone_name``.
    """
    d = resolve_calendar_date(date_str, timezone_name)
    tz = ZoneInfo(timezone_name)
    start_local = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def target_recent_calendar_days_range(
    date_str: str | None, timezone_name: str, num_days: int
) -> tuple[datetime, datetime]:
    """
    UTC half-open window covering ``num_days`` consecutive local calendar days
    ending on ``resolve_calendar_date(date_str, timezone_name)`` (inclusive).
    ``num_days`` >= 1. For ``num_days == 1`` equals ``target_date_range``.
    """
    n = max(1, int(num_days))
    anchor = resolve_calendar_date(date_str, timezone_name)
    tz = ZoneInfo(timezone_name)
    start_day = anchor - timedelta(days=n - 1)
    start_local = datetime(start_day.year, start_day.month, start_day.day, 0, 0, 0, tzinfo=tz)
    end_local = datetime(anchor.year, anchor.month, anchor.day, 0, 0, 0, tzinfo=tz) + timedelta(days=1)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def is_datetime_in_range(dt: datetime | None, start_utc: datetime, end_utc: datetime) -> bool:
    """Half-open range ``[start_utc, end_utc)`` in UTC."""
    if dt is None:
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    u = dt.astimezone(timezone.utc)
    return start_utc <= u < end_utc


def is_url_likely_today(url: str, target_date: date) -> bool:
    """Heuristic: path segments ``/YYYY/MM/DD/`` or ``/YYYY-MM-DD/`` matching target."""
    if not url:
        return False
    y, m, d = target_date.year, target_date.month, target_date.day
    patterns = (
        rf"/{y:04d}/{m:02d}/{d:02d}/",
        rf"/{y:04d}-{m:02d}-{d:02d}/",
        rf"/{y:04d}/{m:02d}/{d:02d}$",
        rf"/{y:04d}-{m:02d}-{d:02d}$",
        rf"{y:04d}/{m:02d}/{d:02d}",
        rf"{y:04d}-{m:02d}-{d:02d}",
    )
    lower = url.lower()
    return any(p.lower() in lower for p in patterns)


def is_url_likely_recent_calendar_month(url: str, anchor: date, num_days: int) -> bool:
    """``/YYYY/MM/`` in path when that month contains any day in the recent window (e.g. vietstock.vn)."""
    if not url:
        return False
    m = re.search(r"/(\d{4})/(\d{1,2})(?:/|$)", url)
    if not m:
        return False
    try:
        uy, um = int(m.group(1)), int(m.group(2))
    except ValueError:
        return False
    n = max(1, int(num_days))
    for i in range(n):
        d = anchor - timedelta(days=i)
        if uy == d.year and um == d.month:
            return True
    return False


def is_url_likely_recent_calendar_days(url: str, anchor: date, num_days: int) -> bool:
    """True if URL path looks like any of the last ``num_days`` local days ending at ``anchor``."""
    n = max(1, int(num_days))
    for i in range(n):
        if is_url_likely_today(url, anchor - timedelta(days=i)):
            return True
    if is_url_likely_recent_calendar_month(url, anchor, n):
        return True
    return False
