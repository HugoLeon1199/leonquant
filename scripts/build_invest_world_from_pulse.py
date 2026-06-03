#!/usr/bin/env python3
"""
Tái lọc invest_world_pulse.json (kinh tế/CK/vàng/crypto/vĩ mô) từ pool enrich đã lưu.
Ưu tiên: web/market_pulse_enriched_pool.json (sau leon.py --channel world).
Fallback: market_pulse.json (ít ứng viên hơn).

Usage: python scripts/build_invest_world_from_pulse.py [--input PATH] [--no-gemini]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_leon():
    spec = importlib.util.spec_from_file_location("leon", ROOT / "leon.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load leon.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=None)
    ap.add_argument("--no-gemini", action="store_true")
    args = ap.parse_args()
    leon = _load_leon()
    leon.load_dotenv()

    src = args.input
    if not src:
        for cand in (
            ROOT / "web" / "market_pulse_enriched_pool.json",
            ROOT / "market_pulse_enriched_pool.json",
            ROOT / "market_pulse.json",
            ROOT / "web" / "market_pulse.json",
        ):
            if cand.is_file():
                src = cand
                break
    if not src or not src.is_file():
        print("No input JSON found", file=sys.stderr)
        return 2

    data = json.loads(src.read_text(encoding="utf-8-sig"))
    events = data.get("events") if isinstance(data, dict) else data
    if not isinstance(events, list):
        print("Invalid input: need events array", file=sys.stderr)
        return 2

    print(f"Curate invest_world from {src} ({len(events)} candidates)")
    leon.export_invest_world_pulse(events, use_gemini=not args.no_gemini)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
