#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from google.cloud import bigquery
from tech.common import GDELT_JSON, GDELT_SCHEMA, dump_json, host_from_url, hot_rule, infer_section, source_type

SQL_PATH = ROOT / "tech" / "sql" / "gdelt_tech_72h.sql"
DEFAULT_MAX_BYTES = 2_000_000_000


def query(client: bigquery.Client, sql: str, *, dry_run: bool, max_bytes: int):
    cfg = bigquery.QueryJobConfig(
        dry_run=dry_run,
        use_query_cache=not dry_run,
        maximum_bytes_billed=max_bytes,
    )
    job = client.query(sql, job_config=cfg)
    processed = int(getattr(job, "total_bytes_processed", 0) or 0)
    if dry_run:
        return [], processed
    return [dict(row.items()) for row in job.result()], processed


def event_from_row(row: dict[str, Any]) -> dict[str, Any]:
    urls: list[str] = []
    for raw in row.get("SourceURLs") or []:
        url = str(raw or "").strip()
        if url.startswith("http") and url not in urls:
            urls.append(url)
    primary = str(row.get("Link_Bai_Bao") or "").strip()
    if primary.startswith("http") and primary not in urls:
        urls.insert(0, primary)
    domains = []
    types = []
    for url in urls:
        domain = host_from_url(url)
        if domain and domain not in domains:
            domains.append(domain)
            types.append(source_type(url))
    is_hot, independent_count, official_present, community_count = hot_rule(types)
    actor1 = str(row.get("Actor1Name") or "").strip()
    actor2 = str(row.get("Actor2Name") or "").strip()
    orgs = str(row.get("V2Organizations") or "").strip()
    themes = str(row.get("V2Themes") or "").strip()
    title = " — ".join(x for x in (actor1, actor2) if x) or orgs or "Technology development"
    blob = " ".join((title, orgs, themes))
    return {
        "event_id": str(row.get("GlobalEventID") or ""),
        "title": title,
        "raw_summary": themes or orgs or title,
        "source_urls": urls[:12],
        "source_count": len(urls),
        "independent_domain_count": independent_count,
        "official_source_present": official_present,
        "community_domain_count": community_count,
        "hot_candidate": is_hot,
        "section": infer_section(blob),
        "reported_at": str(row.get("DATEADDED") or ""),
        "pool_kind": str(row.get("pool_kind") or ""),
        "num_articles": int(row.get("NumArticles") or 0),
        "avg_tone": float(row.get("AvgTone") or 0.0),
    }


def load_existing(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the cost-guarded 72-hour technology query.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-bytes-billed", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--output", type=Path, default=GDELT_JSON)
    args = parser.parse_args()

    sql = SQL_PATH.read_text(encoding="utf-8")
    client = bigquery.Client()
    _, estimated = query(client, sql, dry_run=True, max_bytes=args.max_bytes_billed)
    print(f"Estimated bytes: {estimated:,}; limit: {args.max_bytes_billed:,}")
    if estimated > args.max_bytes_billed:
        print("Query estimate exceeds the configured limit; live query not started.", file=sys.stderr)
        return 6
    if args.dry_run:
        return 0

    rows, processed = query(client, sql, dry_run=False, max_bytes=args.max_bytes_billed)
    events = [event_from_row(row) for row in rows]
    events = [event for event in events if event["source_urls"]]
    if not events:
        if load_existing(args.output):
            print("No new events; kept the previous valid output.")
            return 0
        print("No events and no previous output to retain.", file=sys.stderr)
        return 5

    payload = {
        "schema_version": GDELT_SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "query_window_hours": 72,
        "estimated_bytes": estimated,
        "processed_bytes": processed,
        "events": events,
    }
    dump_json(args.output, payload)
    print(f"Wrote {len(events)} events to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
