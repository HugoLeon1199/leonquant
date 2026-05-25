#!/usr/bin/env python3
"""Print calendar crawl date (YYYY-MM-DD) for CI to pin across crawl + verify steps."""

from __future__ import annotations

import argparse
from datetime import datetime
from zoneinfo import ZoneInfo


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default="today")
    parser.add_argument("--timezone", default="Asia/Ho_Chi_Minh")
    args = parser.parse_args()
    tz = ZoneInfo(args.timezone)
    if args.date.strip().lower() == "today":
        print(datetime.now(tz).date().isoformat())
    else:
        print(args.date.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
