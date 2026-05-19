#!/usr/bin/env python3
"""Per-source coverage: profile strategy, article count, top errors, skip list."""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "web_intel_leonquant.duckdb"
OUT = ROOT / "leon_web_intel" / "data" / "exports" / "source_coverage_report.csv"


def load_seed_hosts() -> dict[str, str]:
    hosts: dict[str, str] = {}
    seed = ROOT / "config" / "sources_seed.txt"
    if not seed.is_file():
        return hosts
    for line in seed.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("http"):
            h = urlparse(s).netloc.lower().removeprefix("www.")
            hosts[h] = s
    return hosts


def main() -> int:
    db_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DB
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT
    if not db_path.is_file():
        print(f"No DB: {db_path}", file=sys.stderr)
        return 2

    c = duckdb.connect(str(db_path), read_only=True)
    profiles = c.execute(
        """
        SELECT source_id, domain, best_strategy, status, has_rss, has_sitemap,
               html_status_code, paywall_detected, error_message
        FROM source_profiles ORDER BY source_id
        """
    ).fetchdf()
    arts = dict(
        c.execute("SELECT source_id, COUNT(*) FROM articles GROUP BY source_id").fetchall()
    )
    errs: dict[str, Counter[str]] = defaultdict(Counter)
    for sid, et, n in c.execute(
        "SELECT source_id, error_type, COUNT(*) FROM crawl_errors GROUP BY 1, 2"
    ).fetchall():
        if sid:
            errs[str(sid)][str(et)] += int(n)
    skip: dict[str, tuple[str, str]] = {}
    try:
        for row in c.execute("SELECT source_id, reason, detail FROM source_crawl_skip").fetchall():
            skip[str(row[0])] = (str(row[1] or ""), str(row[2] or ""))
    except duckdb.CatalogException:
        pass
    c.close()

    seed_hosts = load_seed_hosts()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cols = [
        "source_id",
        "domain",
        "seed_url",
        "best_strategy",
        "status",
        "has_rss",
        "has_sitemap",
        "html_status",
        "articles_in_db",
        "on_skip_list",
        "skip_reason",
        "top_errors",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for _, row in profiles.iterrows():
            sid = str(row["source_id"] or "")
            dom = str(row["domain"] or "")
            ec = errs.get(sid, Counter())
            top = ", ".join(f"{k}:{v}" for k, v in ec.most_common(4))
            sk = skip.get(sid)
            w.writerow(
                {
                    "source_id": sid,
                    "domain": dom,
                    "seed_url": seed_hosts.get(dom.lower().removeprefix("www."), ""),
                    "best_strategy": row["best_strategy"],
                    "status": row["status"],
                    "has_rss": row["has_rss"],
                    "has_sitemap": row["has_sitemap"],
                    "html_status": row["html_status_code"],
                    "articles_in_db": int(arts.get(sid, 0)),
                    "on_skip_list": bool(sk),
                    "skip_reason": sk[0] if sk else "",
                    "top_errors": top,
                }
            )
    print(f"Wrote {out_path} ({len(profiles)} sources)")
    zero = sum(1 for sid in profiles["source_id"] if int(arts.get(str(sid), 0)) == 0)
    print(f"Sources with 0 articles: {zero}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
