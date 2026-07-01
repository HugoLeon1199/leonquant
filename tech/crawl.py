#!/usr/bin/env python3
"""Standalone entrypoint for the Tech crawl/export/clean pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tech._bootstrap import TECH_ROOT, configure_tech_env

HOURS_LIMIT = 72


def publication_age_hours(path: Path) -> float | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        generated = str(payload.get("generated_at_utc") or payload.get("generated_at") or "").strip()
        if generated:
            dt = datetime.fromisoformat(generated.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            delta = datetime.now(timezone.utc) - dt.astimezone(timezone.utc)
            return delta.total_seconds() / 3600.0
    except Exception:
        pass
    try:
        mtime = path.stat().st_mtime
        delta = datetime.now(timezone.utc) - datetime.fromtimestamp(mtime, tz=timezone.utc)
        return delta.total_seconds() / 3600.0
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Standalone Tech crawl wrapper")
    parser.add_argument("--force", action="store_true", help="Ignore the 72h publish gate")
    args, passthrough = parser.parse_known_args()

    publish_path = TECH_ROOT / "data" / "publication.json"
    age = publication_age_hours(publish_path)
    if not args.force and age is not None and age < HOURS_LIMIT:
        print(f"Tech publish age {age:.1f}h < {HOURS_LIMIT}h; skipping crawl/export.")
        return 0

    configure_tech_env()
    from scripts import run_tech_intel_pipeline as impl  # noqa: WPS433

    sys.argv = [
        sys.argv[0],
        "--db",
        str(TECH_ROOT / "data" / "web_intel_tech.duckdb"),
        "--seed",
        str(TECH_ROOT / "config" / "sources_active.txt"),
        "--tiers-dir",
        str(TECH_ROOT / "config" / "tech_tiers"),
        "--manifest",
        str(TECH_ROOT / "config" / "tech_tiers_manifest.json"),
        "--output-today",
        str(TECH_ROOT / "data" / "news_output_today.json"),
        "--output-all",
        str(TECH_ROOT / "data" / "news_output_all.json"),
        "--ai-output",
        str(TECH_ROOT / "data" / "news_for_ai.json"),
        "--clean-output",
        str(TECH_ROOT / "data" / "news_for_ai_clean.json"),
        "--rolling-hours",
        str(HOURS_LIMIT),
        "--skip-profile",
    ] + passthrough
    return impl.main()


if __name__ == "__main__":
    raise SystemExit(main())
