#!/usr/bin/env python3
"""Fail CI if deploy HTML is missing #invest or nests invest inside #pulse."""
from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> None:
    page = Path(sys.argv[1] if len(sys.argv) > 1 else "_site/index.html").resolve()
    html = page.read_text(encoding="utf-8")
    if not re.search(r'<section\s+id="invest"', html, re.I):
        raise SystemExit(f"{page}: missing <section id=\"invest\">")
    pulse_before_invest = re.search(
        r"<section\s+id=\"pulse\"[^>]*>([\s\S]*?)</section>\s*<section\s+id=\"invest\"",
        html,
        re.I,
    )
    if not pulse_before_invest:
        raise SystemExit(f"{page}: expected #pulse then #invest as sibling sections")
    if re.search(r'<div\s+id="sectionInvest"', pulse_before_invest.group(1), re.I):
        raise SystemExit(f"{page}: sectionInvest must not be inside #pulse")
    print(f"OK: {page} has #invest sibling layout")


if __name__ == "__main__":
    main()
