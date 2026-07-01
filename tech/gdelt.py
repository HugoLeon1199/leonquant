#!/usr/bin/env python3
"""Standalone entrypoint for Tech GDELT pulse."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tech._bootstrap import TECH_ROOT, configure_tech_env


def main() -> int:
    configure_tech_env()
    from scripts import run_tech_gdelt as impl  # noqa: WPS433

    sys.argv = [
        sys.argv[0],
        "--output",
        str(TECH_ROOT / "data" / "gdelt_pulse.json"),
        "--web-output",
        str(TECH_ROOT / "web" / "gdelt_pulse.json"),
    ] + sys.argv[1:]
    return impl.main()


if __name__ == "__main__":
    raise SystemExit(main())
