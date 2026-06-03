#!/usr/bin/env python3
"""Backward-compatible wrapper — use prepare_digest_db.py for CI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

QUANT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    cmd = [sys.executable, str(QUANT_ROOT / "scripts" / "prepare_digest_db.py"), *sys.argv[1:]]
    return int(subprocess.call(cmd, cwd=str(QUANT_ROOT)))


if __name__ == "__main__":
    raise SystemExit(main())
