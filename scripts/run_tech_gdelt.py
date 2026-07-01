#!/usr/bin/env python3
"""Standalone GDELT technology & AI pulse."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from google.cloud import bigquery

from scripts.tech_common import (
    TECH_GDELT_OUTPUT,
    TECH_GDELT_SCHEMA,
    TECH_GDELT_WEB_OUTPUT,
    canonical_domain,
    dump_json,
    infer_section,
    is_official_host,
)

ROOT = Path(__file__).resolve().parents[1]
SQL_PATH = ROOT / "sql" / "gdelt_tech_pulse.sql"


def get_client() -> bigquery.Client:
    return bigquery.Client()


def run_query(
    client: bigquery.Client,
    sql: str,
    *,
    dry_run: bool,
    maximum_bytes_billed: int,
) -> tuple[list[dict[str, Any]] | None, dict[str, Any]]:
    job_config = bigquery.QueryJobConfig(
        maximum_bytes_billed=maximum_bytes_billed,
        dry_run=dry_run,
        use_query_cache=not dry_run,
    )
    job = client.query(sql, job_config=job_config)
    meta = {
        "dry_run": dry_run,
        "bytes_billed": int(getattr(job, "total_bytes_processed", 0) or 0),
    }
    if dry_run:
        return None, meta
    rows = [dict(row.items()) for row in job.result()]
    return rows, meta


def event_tags(blob: str) -> list[str]:
    tags: list[str] = []
    checks = {
        "model_agent_moi": ("model", "llm", "agent", "multimodal", "copilot", "chatgpt", "claude", "gemini"),
        "chip_ha_tang": ("gpu", "semiconductor", "chip", "hbm", "datacenter", "cloud", "server"),
        "cybersecurity": ("cyber", "ransomware", "breach", "vulnerability", "zero-day", "prompt injection"),
        "robotics": ("robot", "humanoid", "drone", "robotaxi", "autonomous"),
        "chinh_sach_cuoc_dua_toan_cau": ("regulation", "policy", "governance", "copyright", "export control"),
        "open_source_developer_tools": ("open source", "github", "developer", "sdk", "framework"),
        "radar_khu_vuc": ("china", "japan", "korea", "india", "taiwan", "europe", "arab"),
    }
    low = blob.lower()
    for tag, kws in checks.items():
        if any(kw in low for kw in kws):
            tags.append(tag)
    return tags or [infer_section(blob)]


def companies_from_blob(blob: str) -> list[str]:
    names = [
        "OpenAI", "Anthropic", "Google", "DeepMind", "Meta", "Microsoft", "NVIDIA",
        "xAI", "Mistral", "Cohere", "Hugging Face", "Databricks", "TSMC", "AMD",
        "Intel", "Broadcom", "ASML", "Alibaba", "Baidu", "Tencent", "Huawei",
    ]
    out = [name for name in names if name.lower() in blob.lower()]
    return out[:8]


def build_event(row: dict[str, Any]) -> dict[str, Any]:
    source_urls = [u for u in (row.get("SourceURLs") or []) if isinstance(u, str) and u.startswith("http")]
    domains = sorted({canonical_domain(u) for u in source_urls if canonical_domain(u)})
    official_present = any(is_official_host(d) for d in domains)
    actor1 = str(row.get("Actor1Name") or "").strip()
    actor2 = str(row.get("Actor2Name") or "").strip()
    orgs = str(row.get("V2Organizations") or "").strip()
    themes = str(row.get("V2Themes") or "").strip()
    blob = " ".join(
        part for part in [actor1, actor2, orgs, themes, str(row.get("Link_Bai_Bao") or "")] if part
    )
    title_parts = [part for part in [actor1, actor2] if part]
    title = " — ".join(title_parts) or str(row.get("Link_Bai_Bao") or "Technology event")
    return {
        "event_id": str(row.get("GlobalEventID") or ""),
        "title": title,
        "summary": themes or orgs or title,
        "source_urls": source_urls[:8],
        "source_count": max(int(row.get("source_count") or 0), len(source_urls), 1),
        "independent_domain_count": len(domains),
        "official_source_present": official_present,
        "topic_tags": event_tags(blob),
        "company_tags": companies_from_blob(blob),
        "reported_at": str(row.get("DATEADDED") or ""),
        "freshness_hours": 24,
        "hot_candidate": len(domains) >= 2 or (official_present and len(domains) >= 2),
        "pool_kind": str(row.get("pool_kind") or ""),
        "avg_tone": float(row.get("AvgTone") or 0.0),
        "num_articles": int(row.get("NumArticles") or 0),
        "primary_url": str(row.get("Link_Bai_Bao") or ""),
    }


def load_existing(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Standalone GDELT technology/AI pulse")
    parser.add_argument("--output", type=Path, default=TECH_GDELT_OUTPUT)
    parser.add_argument("--web-output", type=Path, default=TECH_GDELT_WEB_OUTPUT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-bytes-billed", type=int, default=700_000_000)
    args = parser.parse_args()

    sql = SQL_PATH.read_text(encoding="utf-8")
    client = get_client()
    rows, meta = run_query(
        client,
        sql,
        dry_run=args.dry_run,
        maximum_bytes_billed=args.max_bytes_billed,
    )
    if args.dry_run:
        print(f"tech dry-run bytes_billed={meta['bytes_billed']}")
        return 0

    events = [build_event(row) for row in (rows or [])]
    events = [evt for evt in events if evt["source_urls"]]
    if not events:
        existing = load_existing(args.output)
        if existing is not None:
            print("No fresh tech GDELT events; kept previous valid JSON.")
            return 0
        print("No tech GDELT events and no previous JSON to retain.")
        return 5

    payload = {
        "schema_version": TECH_GDELT_SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "query_window_hours": 24,
        "bq_bytes_billed": int(meta.get("bytes_billed") or 0),
        "events": events,
    }
    dump_json(args.output, payload)
    dump_json(args.web_output, payload)
    print(f"Wrote {len(events)} tech GDELT events -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
