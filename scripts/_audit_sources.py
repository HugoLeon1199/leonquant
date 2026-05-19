#!/usr/bin/env python3
"""Audit seed sources: articles in DB, errors, skip list, quick HTTP probe."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "web_intel_leonquant.duckdb"
OUT = ROOT / "scripts" / "_source_audit_report.txt"

BLOCK = frozenset(
    {
        "FetchError",
        "ConnectError",
        "ConnectTimeout",
        "ReadTimeout",
        "HttpError",
        "AccessControlDetected",
        "PlaywrightDisabled",
    }
)
DATE_ONLY = frozenset({"NotToday", "PublishedDateMissingLikelyToday"})

seed: dict[str, str] = {}
for line in (ROOT / "config/sources_seed.txt").read_text(encoding="utf-8").splitlines():
    s = line.strip()
    if s.startswith("http"):
        h = urlparse(s).netloc.lower().removeprefix("www.")
        seed[h] = s

skip_domains: set[str] = set()
for line in (ROOT / "config/sources_uncrawlable.txt").read_text(encoding="utf-8").splitlines():
    s = line.strip()
    if s.startswith("http"):
        skip_domains.add(urlparse(s).netloc.lower().removeprefix("www."))
    m = re.search(r"source_id=(\S+)", s)
    if m:
        pass

c = duckdb.connect(str(DB), read_only=True)
profiles = {
    str(r[0]): r
    for r in c.execute(
        "SELECT source_id, domain, input_url, status, best_strategy, error_message FROM source_profiles"
    ).fetchall()
}
art = dict(c.execute("SELECT source_id, COUNT(*) FROM articles GROUP BY 1").fetchall())
pub18 = Counter(
    r[0]
    for r in c.execute(
        "SELECT source_id FROM articles WHERE CAST(published_at AS VARCHAR) LIKE '2026-05-18%'"
    ).fetchall()
)
errs: dict[str, Counter[str]] = defaultdict(Counter)
for sid, et, n in c.execute(
    "SELECT source_id, error_type, COUNT(*) FROM crawl_errors GROUP BY 1,2"
).fetchall():
    if sid:
        errs[sid][et] += int(n)
skip_sids = {r[0] for r in c.execute("SELECT source_id FROM source_crawl_skip").fetchall()}
skip_info = {
    r[0]: (r[1], r[2], r[3])
    for r in c.execute(
        "SELECT source_id, reason, detail, block_errors FROM source_crawl_skip"
    ).fetchall()
}
c.close()

lines: list[str] = []


def pr(s: str = "") -> None:
    lines.append(s)


def dom_of_sid(sid: str) -> str:
    row = profiles.get(sid)
    if row and row[1]:
        return str(row[1]).lower().removeprefix("www.")
    return sid.replace("_", ".")


def summarize_site(domain: str) -> None:
    row = next((profiles[s] for s, p in profiles.items() if p[1] and str(p[1]).lower().removeprefix("www.") == domain), None)
    if not row:
        pr(f"  [{domain}] KHONG CO PROFILE")
        return
    sid, dom, url, status, strat, perr = row
    n_art = art.get(sid, 0)
    n18 = pub18.get(sid, 0)
    e = errs.get(sid, Counter())
    block_n = sum(e.get(k, 0) for k in BLOCK)
    date_n = sum(e.get(k, 0) for k in DATE_ONLY)
    on_skip = sid in skip_sids
    reason = skip_info.get(sid, (None, None, None))

    if n_art > 0:
        crawl_verdict = "CRAWL DUOC (co bai trong DB)"
    elif date_n > 0 and block_n == 0:
        crawl_verdict = "CRAWL DUOC (chi NotToday - site co bai nhung khong dung ngay crawl)"
    elif block_n >= 5 and (block_n >= date_n or date_n == 0):
        crawl_verdict = "KHONG CRAWL DUOC (chu yeu bi chan/HTTP)"
    elif status == "review" or strat == "manual_review":
        crawl_verdict = "KHONG CRAWL DUOC (profile loi - chua vao Scrapy on dinh)"
    elif not e:
        crawl_verdict = "CHUA RO (it/khong co log crawl)"
    else:
        crawl_verdict = "MOT PHAN (loi le hoac ShortContent)"

    pr(f"  {domain}")
    pr(f"    URL seed: {url or seed.get(domain, '')}")
    pr(f"    Profile: {status} | strategy={strat}")
    if perr:
        pr(f"    Profile error: {str(perr)[:120]}")
    pr(f"    Bai DB (tat ca ngay): {n_art} | pub 2026-05-18: {n18}")
    if e:
        pr(f"    Loi crawl: {', '.join(f'{t}:{n}' for t, n in e.most_common(5))}")
    else:
        pr(f"    Loi crawl: (khong)")
    pr(f"    Danh sach skip: {'CO' if on_skip else 'KHONG'} {reason[0] or ''}")
    pr(f"    => {crawl_verdict}")
    pr()


pr("=== AUDIT 99 NGUON SEED (tu DuckDB) ===")
pr()

# 1) Skip list
pr(f"## A. 38 nguon TRONG sources_uncrawlable.txt (lan sau bo qua)")
pr()
for dom in sorted(skip_domains):
    summarize_site(dom)

# 2) Crawl OK not skip
pr("## B. Nguon KHONG skip - chung minh crawl duoc (co bai DB hoac chi NotToday)")
pr()
ok_domains = []
for dom in sorted(seed):
    row = next((profiles[s] for s, p in profiles.items() if p[1] and str(p[1]).lower().removeprefix("www.") == dom), None)
    if not row:
        continue
    sid = row[0]
    if sid in skip_sids:
        continue
    n_art = art.get(sid, 0)
    e = errs.get(sid, Counter())
    block_n = sum(e.get(k, 0) for k in BLOCK)
    date_n = sum(e.get(k, 0) for k in DATE_ONLY)
    if n_art > 0 or (date_n > 0 and block_n == 0):
        ok_domains.append(dom)

for dom in ok_domains[:20]:
    summarize_site(dom)
if len(ok_domains) > 20:
    pr(f"  ... +{len(ok_domains) - 20} nguon tuong tu")
pr(f"  Tong nhom B (crawl duoc ro rang): {len(ok_domains)}")
pr()

# 3) Unclear - not skip, no articles, has some errors
pr("## C. KHONG skip nhung CHUA RO (0 bai DB, co loi hoac chua crawl)")
pr()
unclear = []
for dom in sorted(seed):
    row = next((profiles[s] for s, p in profiles.items() if p[1] and str(p[1]).lower().removeprefix("www.") == dom), None)
    if not row:
        unclear.append(dom)
        continue
    sid = row[0]
    if sid in skip_sids or dom in ok_domains:
        continue
    unclear.append(dom)

for dom in unclear:
    summarize_site(dom)

pr("=== TOM TAT ===")
pr(f"Seed: {len(seed)} | Skip: {len(skip_domains)} | Crawl OK ro: {len(ok_domains)} | Chua ro: {len(unclear)}")

OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Wrote {OUT}")
