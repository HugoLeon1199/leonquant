#!/usr/bin/env python3
"""Alias: export + clean + digest loop (không crawl). Dùng ``run_daily_brief.py`` cho pipeline đầy đủ."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    return subprocess.call(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_daily_brief.py"),
            "--skip-crawl",
            "--digest-loop",
        ],
        cwd=ROOT,
    )


if __name__ == "__main__":
    raise SystemExit(main())