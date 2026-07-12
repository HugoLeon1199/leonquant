#!/usr/bin/env python3
"""Standalone entrypoint for the Tech crawl/export/clean pipeline."""

from __future__ import annotations

import argparse
import json
import sys
import subprocess
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


def profiles_cover_seed(db_path: Path, seed_path: Path) -> bool:
    if not db_path.is_file():
        return False
    try:
        import duckdb

        required_urls = {
            line.strip()
            for line in seed_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        if not required_urls:
            return False
        con = duckdb.connect(str(db_path), read_only=True)
        try:
            profiled_urls = {
                str(row[0]).strip()
                for row in con.execute("SELECT input_url FROM source_profiles").fetchall()
                if row and str(row[0]).strip()
            }
            return required_urls.issubset(profiled_urls)
        finally:
            con.close()
    except Exception:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Standalone Tech crawl wrapper")
    parser.add_argument("--force", action="store_true", help="Deprecated: crawl now refreshes data by default")
    parser.add_argument("--respect-publish-gate", action="store_true", help="Skip crawl when publication is newer than 72h")
    args, passthrough = parser.parse_known_args()

    publish_path = TECH_ROOT / "data" / "publication.json"
    age = publication_age_hours(publish_path)
    if args.respect_publish_gate and not args.force and age is not None and age < HOURS_LIMIT:
        print(f"Tech publish age {age:.1f}h < {HOURS_LIMIT}h; skipping crawl/export.")
        return 0

    configure_tech_env()
    from scripts import run_tech_intel_pipeline as impl  # noqa: WPS433

    db_path = TECH_ROOT / "data" / "web_intel_tech.duckdb"
    seed_path = TECH_ROOT / "config" / "sources_active.txt"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if not profiles_cover_seed(db_path, seed_path):
        profile_cmd = [
            sys.executable,
            str(ROOT / "leon_web_intel" / "run_profile.py"),
            "--input",
            str(seed_path),
            "--profile-only",
            "--db",
            str(db_path),
            "--force-refresh",
        ]
        print("+", " ".join(profile_cmd), flush=True)
        rc = subprocess.call(profile_cmd, cwd=TECH_ROOT)
        if rc != 0:
            return rc

    sys.argv = [
        sys.argv[0],
        "--db",
        str(db_path),
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
