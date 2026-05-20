#!/usr/bin/env python3
"""Export news_for_ai.json (2 recent days) then run Gemini batch digest."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> int:
    print("+", " ".join(cmd), flush=True)
    return subprocess.call(cmd, cwd=ROOT)


def _gemini_key_in_dotenv() -> bool:
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
    if not _gemini_key_in_dotenv() and not os.environ.get("GEMINI_API_KEY"):
        print(
            f"Missing GEMINI_API_KEY. Copy {ROOT / '.env.example'} → {ROOT / '.env'} and set your key.",
            file=sys.stderr,
        )
        return 2

    rc = run(
        [
            sys.executable,
            str(ROOT / "scripts" / "export_news_full_for_ai.py"),
            "--date",
            "today",
            "--recent-calendar-days",
            "2",
        ]
    )
    if rc:
        return rc

    return run(
        [
            sys.executable,
            str(ROOT / "summarize_news_gemini.py"),
            "--input",
            str(ROOT / "news_for_ai.json"),
            "--mode",
            "digest",
            "--batch-digest",
            "--model",
            os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite"),
            "--use-existing-outline",
            "--resume-partials",
            "--api-pause",
            "60",
            "--min-request-interval",
            "60",
            "--gemini-timeout",
            "3600",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
