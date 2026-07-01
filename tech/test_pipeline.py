#!/usr/bin/env python3
"""Standalone entrypoint for Tech pipeline tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tech._bootstrap import configure_tech_env


def main() -> None:
    configure_tech_env()
    from scripts import test_tech_pipeline as impl  # noqa: WPS433

    impl.main()


if __name__ == "__main__":
    main()
