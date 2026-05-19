"""Count seed sources that can be crawled (fetch/extract), not 'no article today'."""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "web_intel_leonquant.duckdb"

BLOCK_TYPES = frozenset(
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
DATE_ONLY_TYPES = frozenset({"NotToday", "PublishedDateMissingLikelyToday"})

seed: dict[str, str] = {}
for line in (ROOT / "config" / "sources_seed.txt").read_text(encoding="utf-8").splitlines():
    s = line.strip()
    if s.startswith("http"):
        h = urlparse(s).netloc.lower().removeprefix("www.")
        seed.setdefault(h, s)

c = duckdb.connect(str(DB), read_only=True)
profiles = c.execute(
    "SELECT source_id, domain, status, best_strategy FROM source_profiles"
).fetchall()
dom_to_sid: dict[str, tuple] = {}
sid_to_dom: dict[str, str] = {}
for sid, dom, status, strat in profiles:
    if dom:
        d = str(dom).lower().removeprefix("www.")
        dom_to_sid[d] = (sid, status, strat)
        sid_to_dom[sid] = d

art_any = Counter(
    r[0] for r in c.execute("SELECT source_id, COUNT(*) FROM articles GROUP BY 1").fetchall()
)
err_by_sid: dict[str, Counter[str]] = defaultdict(Counter)
for sid, et, n in c.execute(
    "SELECT source_id, error_type, COUNT(*) FROM crawl_errors GROUP BY 1,2"
).fetchall():
    if sid:
        err_by_sid[sid][et] += int(n)

frontier_by_sid = Counter(
    r[0]
    for r in c.execute(
        "SELECT source_id, COUNT(*) FROM crawl_frontier WHERE status IN ('crawled','failed','skipped') GROUP BY 1"
    ).fetchall()
    if r[0]
)

lines: list[str] = []


def pr(s: str = "") -> None:
    lines.append(s)


def classify(domain: str) -> str:
    info = dom_to_sid.get(domain)
    if info is None:
        return "no_profile"
    sid, status, strat = info
    if status == "review" or strat == "manual_review":
        return "profile_failed"

    n_art = art_any.get(sid, 0)
    if n_art > 0:
        return "has_articles"

    errs = err_by_sid.get(sid, Counter())
    if not errs and frontier_by_sid.get(sid, 0) == 0:
        return "no_crawl_activity"

    non_date = {k: v for k, v in errs.items() if k not in DATE_ONLY_TYPES}
    date_only = sum(v for k, v in errs.items() if k in DATE_ONLY_TYPES)
    block_n = sum(v for k, v in errs.items() if k in BLOCK_TYPES)

    if not non_date and date_only > 0:
        return "crawl_ok_date_only"  # fetched, pipeline date filter only

    if block_n > 0 and block_n >= sum(non_date.values()) // 2 + 1:
        if date_only > 0:
            return "mixed_block_and_date"
        return "mostly_blocked"

    if non_date.get("ShortContent", 0) and block_n == 0:
        return "crawl_weak_short"  # reached page, extract thin

    if sum(non_date.values()) > 0:
        return "crawl_partial_errors"

    return "other"


buckets: dict[str, list[str]] = defaultdict(list)
for dom in sorted(seed):
    cat = classify(dom)
    sid = dom_to_sid.get(dom, (None,))[0]
    n_art = art_any.get(sid, 0) if sid else 0
    errs = err_by_sid.get(sid, Counter()) if sid else Counter()
    top = ", ".join(f"{t}:{n}" for t, n in errs.most_common(3))
    buckets[cat].append(f"{dom} | articles={n_art} | {top or 'no errors'}")

# Aggregate
crawl_success = buckets["has_articles"] + buckets["crawl_ok_date_only"] + buckets["crawl_weak_short"]
crawl_success_domains = {x.split(" |")[0] for x in crawl_success}

pr("=== Nguon seed vs kha nang crawl (KHONG tinh 'khong co bai hom nay') ===")
pr()
pr(f"Tong domain seed: {len(seed)}")
pr(f"Co profile trong DB: {len(dom_to_sid)}")
pr()
pr("--- DINH NGHIA 'CRAWL DUOC' ---")
pr("A) Co it nhat 1 bai trong DB (bat ky ngay): extract thanh cong")
pr("B) Chi loi NotToday (da fetch, pipeline loc ngay): crawl duoc, khong luu bai")
pr("C) ShortContent: vao duoc trang, noi dung qua ngan")
pr()
pr(f"A - Co bai trong DB: {len(buckets['has_articles'])}")
pr(f"B - Chi NotToday (0 bai DB): {len(buckets['crawl_ok_date_only'])}")
pr(f"C - ShortContent chinh: {len(buckets['crawl_weak_short'])}")
pr(f"TONG crawl duoc (A+B+C): {len(crawl_success_domains)}")
pr()
pr(f"Profile loi (khong crawl du): {len(buckets['profile_failed'])}")
pr(f"Chu yeu bi chan (HTTP/access/fetch): {len(buckets['mostly_blocked'])}")
pr(f"Hon hop chan + NotToday: {len(buckets['mixed_block_and_date'])}")
pr(f"Loi khac / mot phan: {len(buckets['crawl_partial_errors'])}")
pr(f"Khong thay hoat dong crawl: {len(buckets['no_crawl_activity'])}")
pr(f"Khong co profile: {len(buckets['no_profile'])}")
pr(f"Khac: {len(buckets['other'])}")

# Also: distinct sources with any article
pr()
pr(f"Nguon co >=1 article (distinct source_id): {len(art_any)}")
pr(f"Tong bai trong articles: {sum(art_any.values())}")

for key in (
    "has_articles",
    "crawl_ok_date_only",
    "crawl_weak_short",
    "mostly_blocked",
    "profile_failed",
    "mixed_block_and_date",
    "no_crawl_activity",
):
    items = buckets.get(key, [])
    if not items:
        continue
    pr()
    pr(f"## {key} ({len(items)})")
    for line in items[:15]:
        pr(f"  - {line}")
    if len(items) > 15:
        pr(f"  ... +{len(items) - 15}")

out = ROOT / "scripts" / "_crawl_success_report.txt"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Wrote {out}")
c.close()
