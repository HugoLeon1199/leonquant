#!/usr/bin/env python3
"""Helpers for standalone tech/ wrappers."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TECH_ROOT = ROOT / "tech"


def configure_tech_env() -> None:
    os.environ.setdefault("LEON_TECH_BASE_DIR", str(TECH_ROOT))
