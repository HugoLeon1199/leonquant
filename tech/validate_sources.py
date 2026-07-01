#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import validate_tech_sources as legacy
from tech.common import (
    ACTIVE, DISABLED, PASS_STATUSES, REPORTS_DIR, TIERS_DIR, TIERS_MANIFEST,
    VALIDATION_DB, VALIDATION_JSON, VALIDATION_MD, VALIDATION_SCHEMA,
    dump_json, ensure_parent, host_from_url, load_json, parse_catalog, source_type,
)

BASE_CATALOG = ROOT / "config" / "tech_sources_catalog.txt"
MIN_RECENT_ARTICLES = 3


def effective_status(row: dict) -> str:
    status = str(row.get("validation_status") or "ARTICLE_EXTRACTION_FAILED")
    samples = row.get("article_samples") or []
    recent_ok = sum(
        1 for item in samples
        if item.get("extract_ok") and item.get("published_recent")
    )
    if status in PASS_STATUSES and recent_ok < MIN_RECENT_ARTICLES:
        return "NO_RECENT_CONTENT"
    if row.get("source_type") == "community" and status == "PASS_RSS":
        return "PASS_FORUM_RSS"
    return status


def checkpoint(sources: list[dict], catalog_count: int, complete: bool) -> dict:
    for row in sources:
        row["validation_status"] = effective_status(row)
        row["production_ready"] = row["validation_status"] in PASS_STATUSES
    active_count = sum(1 for row in sources if row["production_ready"])
    payload = {
        "schema_version": VALIDATION_SCHEMA,
        "validation_meta": {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "catalog_source_count": catalog_count,
            "checked_source_count": len(sources),
            "active_source_count": active_count,
            "disabled_source_count": len(sources) - active_count,
            "report_valid": bool(complete and active_count > 0),
            "complete": complete,
            "window_hours": 72,
            "status_counts": dict(Counter(row["validation_status"] for row in sources)),
        },
        "sources": sources,
    }
    dump_json(VALIDATION_JSON, payload)
    return payload


def write_outputs(report: dict) -> None:
    active = [x for x in report["sources"] if x.get("production_ready")]
    disabled = [x for x in report["sources"] if not x.get("production_ready")]
    ensure_parent(ACTIVE)
    ACTIVE.write_text("\n".join(["# Validated tech sources", *[x["input_url"] for x in active]]) + "\n", encoding="utf-8")
    DISABLED.write_text(
        "\n".join(["# Disabled tech sources", *[f"# {x['validation_status']} | {x['name']}\n{x['input_url']}" for x in disabled]]) + "\n",
        encoding="utf-8",
    )
    TIERS_DIR.mkdir(parents=True, exist_ok=True)
    for old in TIERS_DIR.glob("*.txt"):
        old.unlink()
    grouped: dict[str, list[str]] = defaultdict(list)
    manifest: dict[str, str] = {}
    for row in active:
        tier = {
            "PASS_RSS": "01_rss",
            "PASS_SITEMAP": "02_sitemap",
            "PASS_HTML": "03_html",
            "PASS_FORUM_RSS": "04_forum_rss",
        }[row["validation_status"]]
        grouped[tier].append(row["domain"])
        manifest[row["domain"]] = tier
    for tier, domains in grouped.items():
        (TIERS_DIR / f"{tier}.txt").write_text("\n".join(sorted(set(domains))) + "\n", encoding="utf-8")
    dump_json(TIERS_MANIFEST, manifest)
    lines = [
        "# Tech source validation — 72h",
        "",
        f"- Checked: **{report['validation_meta']['checked_source_count']}**",
        f"- Active: **{report['validation_meta']['active_source_count']}**",
        f"- Complete: **{report['validation_meta']['complete']}**",
        "",
        "## Status",
    ]
    for key, value in sorted(report["validation_meta"]["status_counts"].items()):
        lines.append(f"- `{key}`: {value}")
    lines += ["", "## Review", ""]
    for row in disabled:
        lines.append(f"- `{row['validation_status']}` — {row['name']} — {row['input_url']}")
    VALIDATION_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    entries = parse_catalog(BASE_CATALOG)
    if args.limit > 0:
        entries = entries[: args.limit]

    if args.force_refresh:
        VALIDATION_DB.unlink(missing_ok=True)
        VALIDATION_JSON.unlink(missing_ok=True)

    previous = load_json(VALIDATION_JSON, {}) if args.resume else {}
    finished = {x.get("input_url"): x for x in previous.get("sources") or []}
    rows: list[dict] = []
    seen_domains: set[str] = set()

    rules = legacy.load_crawl_rules(legacy.LEON_ROOT / "config" / "crawl_rules.yaml")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    http = legacy.CachedHttpClient(rules, cache_dir=legacy.LEON_ROOT / "data" / "cache" / "http", profile_cache_days=0)
    db = legacy.WebIntelDB(VALIDATION_DB)
    raw_store = legacy.RawStore(legacy.LEON_ROOT / "data" / "raw")
    profiler = legacy.SourceProfiler(rules=rules, http=http, db=db, raw_store=raw_store)
    try:
        for entry in entries:
            url = entry["url"]
            domain = host_from_url(url)
            duplicate = domain in seen_domains
            if duplicate:
                row = {
                    "name": entry["name"], "input_url": url, "domain": domain,
                    "source_type": source_type(url), "validation_status": "DUPLICATE_DOMAIN",
                    "production_ready": False, "article_samples": [],
                }
            elif url in finished:
                row = finished[url]
                row["source_type"] = source_type(url)
            else:
                try:
                    row = legacy.validate_source(
                        entry=entry, profiler=profiler, db=db,
                        raw_store=raw_store, http=http, rules=rules,
                    )
                except Exception as exc:
                    row = {
                        "name": entry["name"], "input_url": url, "domain": domain,
                        "validation_status": "VALIDATION_ERROR", "production_ready": False,
                        "article_samples": [], "notes": str(exc),
                    }
                row["source_type"] = source_type(url)
            if not duplicate:
                seen_domains.add(domain)
            rows.append(row)
            checkpoint(rows, len(entries), complete=False)
    finally:
        http.close()
        db.close()

    report = checkpoint(rows, len(entries), complete=True)
    write_outputs(report)
    print(f"Validated {len(rows)} sources; active={report['validation_meta']['active_source_count']}")
    return 0 if report["validation_meta"]["report_valid"] else 5


if __name__ == "__main__":
    raise SystemExit(main())
