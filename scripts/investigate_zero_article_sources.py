#!/usr/bin/env python3
"""Per-seed-source root cause when 0 articles in DB (excl. explain NotToday-only)."""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "web_intel_leonquant.duckdb"
SNAPSHOT = ROOT / "data" / "web_intel_snapshot_audit.duckdb"
OUT = ROOT / "scripts" / "zero_article_investigation.md"

PLAYWRIGHT = "playwright_fallback"
REAL_BLOCK_ERRORS = frozenset(
    {"FetchError", "ConnectError", "ConnectTimeout", "ReadTimeout", "HttpError", "PlaywrightDisabled"}
)
DATE_ONLY = frozenset({"NotToday", "PublishedDateMissingLikelyToday"})
SOFT = frozenset({"ShortContent", "DuplicateContent", "NonHtmlSkipped", "PublishedDateMissingLikelyToday"})


def load_seed() -> dict[str, str]:
    out: dict[str, str] = {}
    for line in (ROOT / "config/sources_seed.txt").read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("http"):
            h = urlparse(s).netloc.lower().removeprefix("www.")
            out[h] = s
    return out


def classify_zero(
    *,
    status: str,
    strat: str,
    on_skip: bool,
    skip_reason: str | None,
    n_art: int,
    errs: Counter[str],
    has_rss: bool,
    has_sitemap: bool,
) -> tuple[str, str]:
    if n_art > 0:
        return "has_articles", "OK"

    if strat == PLAYWRIGHT:
        return "needs_playwright", "Profiler chon Playwright; Scrapy khong render JS"

    if status == "review" or strat == "manual_review":
        return "profile_failed", "Profile loi — chua lane Scrapy on dinh"

    if on_skip and skip_reason == "profile_failed":
        return "profile_failed", "Tren skip list (profile)"

    if on_skip and skip_reason == "blocked":
        return "blocked_real", "Tren skip list (HTTP/SSL that)"

    date_n = sum(errs.get(k, 0) for k in DATE_ONLY)
    block_n = sum(errs.get(k, 0) for k in REAL_BLOCK_ERRORS)
    ac_n = errs.get("AccessControlDetected", 0)
    short_n = errs.get("ShortContent", 0)

    if not errs:
        if not has_rss and not has_sitemap and strat != "html_then_trafilatura":
            return "no_discovery", "Khong RSS/sitemap trong profile — spider khong enqueue"
        return "no_crawl_log", "Khong co crawl_errors — co the chua vao tier / chua chay toi"

    if date_n > 0 and block_n == 0 and ac_n == 0 and short_n == 0:
        return "only_not_today", "Crawl duoc; 0 bai vi loc ngay (NotToday) — KHONG phai loi code"

    if date_n > block_n and block_n < 5 and ac_n < 5:
        return "mostly_not_today", f"Chu yeu NotToday ({date_n}); co the co bai ngay khac"

    if block_n >= 5 and block_n >= date_n:
        return "blocked_real", f"HTTP/fetch: {', '.join(f'{t}:{errs[t]}' for t in REAL_BLOCK_ERRORS if errs.get(t))}"

    if ac_n >= 5 and n_art == 0:
        return "access_heuristic", f"AccessControl con {ac_n} — xem lai extract/HTML (sau fix nen giam)"

    if short_n >= 5:
        return "short_extract", f"Trich xuat ngan ({short_n}) — template/selector hoac trang listing"

    if errs.get("FetchError") or errs.get("HttpError"):
        return "blocked_partial", errs.most_common(3).__repr__()

    return "other", ", ".join(f"{t}:{n}" for t, n in errs.most_common(4))


def main() -> int:
    db_path = DB
    if not db_path.is_file():
        print(f"DB missing: {db_path}")
        return 2

    try:
        c = duckdb.connect(str(db_path), read_only=True)
    except duckdb.IOException:
        if SNAPSHOT.is_file():
            db_path = SNAPSHOT
            c = duckdb.connect(str(db_path), read_only=True)
            print(f"Using snapshot: {SNAPSHOT}")
        else:
            print("DuckDB locked; run again after crawl or create snapshot copy")
            return 3

    seed = load_seed()
    prof = c.execute(
        """
        SELECT source_id, domain, input_url, status, best_strategy,
               has_rss, has_sitemap, error_message
        FROM source_profiles
        """
    ).fetchall()
    dom_map: dict[str, dict] = {}
    for sid, dom, url, st, strat, hrss, hsmap, perr in prof:
        if not dom:
            continue
        d = str(dom).lower().removeprefix("www.")
        dom_map[d] = {
            "source_id": sid,
            "url": url,
            "status": st,
            "strat": strat,
            "has_rss": bool(hrss),
            "has_sitemap": bool(hsmap),
            "perr": perr,
        }

    art = dict(c.execute("SELECT source_id, COUNT(*) FROM articles GROUP BY 1").fetchall())
    errs: dict[str, Counter[str]] = defaultdict(Counter)
    for sid, et, n in c.execute(
        "SELECT source_id, error_type, COUNT(*) FROM crawl_errors GROUP BY 1,2"
    ).fetchall():
        if sid:
            errs[sid][et] += int(n)

    skip = {
        r[0]: (r[1], r[2])
        for r in c.execute("SELECT source_id, reason, detail FROM source_crawl_skip").fetchall()
    }

    buckets: dict[str, list[str]] = defaultdict(list)
    lines = [
        "# Dieu tra nguon 0 bai trong DB",
        "",
        f"Tong seed: {len(seed)}",
        "",
    ]

    zero = 0
    for dom in sorted(seed):
        info = dom_map.get(dom)
        if not info:
            buckets["no_profile"].append(f"- **{dom}** — khong co profile")
            zero += 1
            continue
        sid = info["source_id"]
        n_art = art.get(sid, 0)
        if n_art > 0:
            continue
        zero += 1
        on_skip = sid in skip
        sk_reason = skip[sid][0] if on_skip else None
        cat, detail = classify_zero(
            status=str(info["status"] or ""),
            strat=str(info["strat"] or ""),
            on_skip=on_skip,
            skip_reason=sk_reason,
            n_art=0,
            errs=errs.get(sid, Counter()),
            has_rss=info["has_rss"],
            has_sitemap=info["has_sitemap"],
        )
        top_err = ", ".join(f"{t}:{n}" for t, n in errs.get(sid, Counter()).most_common(3))
        buckets[cat].append(
            f"- **{dom}** | `{info['strat']}` | skip={on_skip} | {detail}"
            + (f" | loi: {top_err}" if top_err else "")
        )

    lines.append(f"Nguon **0 bai DB**: {zero}")
    lines.append("")
    order = [
        "only_not_today",
        "mostly_not_today",
        "needs_playwright",
        "profile_failed",
        "blocked_real",
        "access_heuristic",
        "short_extract",
        "no_discovery",
        "no_crawl_log",
        "blocked_partial",
        "other",
        "no_profile",
    ]
    labels = {
        "only_not_today": "Chi NotToday (crawl OK, sai ngay) — khong sua code",
        "mostly_not_today": "Chu yeu NotToday",
        "needs_playwright": "Can Playwright (bo qua theo yeu cau)",
        "profile_failed": "Profile loi",
        "blocked_real": "Chan that (HTTP/SSL)",
        "access_heuristic": "AccessControl (die tra heuristic)",
        "short_extract": "Noi dung qua ngan",
        "no_discovery": "Khong co RSS/sitemap",
        "no_crawl_log": "Chua thay log crawl",
        "blocked_partial": "Loi mang mot phan",
        "other": "Khac",
        "no_profile": "Khong profile",
    }
    for cat in order:
        items = buckets.get(cat, [])
        if not items:
            continue
        lines.append(f"## {labels.get(cat, cat)} ({len(items)})")
        lines.append("")
        lines.extend(items)
        lines.append("")

    # Code risk notes
    lines.append("## Rui ro trong code (can xem)")
    lines.append("")
    lines.append("- `playwright_fallback` -> RSS/sitemap/HTML Scrapy, khong Playwright")
    lines.append("- RSS 404 (vd dantri feed path) -> 0 URL enqueue")
    lines.append("- `today_only` + cap 50 link moi nhat -> nhieu NotToday")
    lines.append("- Listing URL vao DB neu extract du dai (tieu de 'trang 1')")
    lines.append("")

    c.close()
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT} ({zero} sources with 0 articles)")
    for cat in order:
        if buckets.get(cat):
            print(f"  {cat}: {len(buckets[cat])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
