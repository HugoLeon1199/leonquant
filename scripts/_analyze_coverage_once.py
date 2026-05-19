"""One-off: why seed sources missing from 2026-05-18 export."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

import duckdb

ROOT = Path(__file__).resolve().parents[1]
TARGET = "2026-05-18"
DB = ROOT / "data" / "web_intel_leonquant.duckdb"

# seed domain -> first url
seed: dict[str, str] = {}
for line in (ROOT / "config/sources_seed.txt").read_text(encoding="utf-8").splitlines():
    s = line.strip()
    if s.startswith("http"):
        h = urlparse(s).netloc.lower()
        if h.startswith("www."):
            h = h[4:]
        seed.setdefault(h, s)

export_hosts: set[str] = set()
export_n: Counter[str] = Counter()
data = json.loads((ROOT / "news_output.json").read_text(encoding="utf-8"))
for a in data["articles"]:
    h = (a.get("source") or "").lower()
    export_hosts.add(h)
    export_n[h] += 1

c = duckdb.connect(str(DB), read_only=True)
profiles = c.execute("SELECT * FROM source_profiles ORDER BY source_id").fetchdf()
prof_by_domain = {str(r.domain).lower(): r for _, r in profiles.iterrows() if r.domain}

# articles per source_id
art_pub18 = Counter(
    r[0]
    for r in c.execute(
        "SELECT source_id FROM articles WHERE CAST(published_at AS VARCHAR) LIKE ?",
        [f"{TARGET}%"],
    ).fetchall()
)
art_any = Counter(r[0] for r in c.execute("SELECT source_id FROM articles").fetchall())

# errors per source_id (top types)
err_rows = c.execute(
    "SELECT source_id, error_type, COUNT(*) n FROM crawl_errors GROUP BY 1,2"
).fetchall()
err_by_sid: dict[str, Counter[str]] = defaultdict(Counter)
for sid, et, n in err_rows:
    err_by_sid[sid][et] += int(n)

# classify each seed domain
def classify(domain: str) -> tuple[str, str]:
    row = prof_by_domain.get(domain)
    if row is None:
        return "no_profile", "Chưa có profile trong DuckDB"

    sid = str(row.source_id)
    strat = str(row.best_strategy or "")
    status = str(row.status or "")
    n_exp = 0
    for eh, cnt in export_n.items():
        if domain == eh or domain.endswith("." + eh) or eh.endswith("." + domain):
            n_exp += cnt
    if n_exp > 0:
        return "ok_export", f"{n_exp} bài trong export"

    n18 = art_pub18.get(sid, 0)
    if n18 > 0:
        return "db_pub18_not_export", f"Có {n18} bài pub18 trong DB nhưng không vào export (lạ)"

    errs = err_by_sid.get(sid, Counter())
    top_err = errs.most_common(3)
    err_str = ", ".join(f"{t}:{n}" for t, n in top_err[:3]) if top_err else "không có crawl_errors"

    if status == "review" or strat == "manual_review":
        return "profile_failed", f"Profile manual_review — {str(row.error_message or '')[:80]}"

    if strat == "playwright_fallback":
        return "playwright_lane", f"Playwright (thường không chạy đủ trong Scrapy batch) — lỗi: {err_str}"

    if not errs and art_any.get(sid, 0) == 0:
        if strat in ("rss_then_article_extract", "sitemap_then_article_extract", "html_then_trafilatura"):
            return "crawled_no_articles", "Crawl chạy nhưng 0 bài lưu DB (có thể NotToday hết hoặc không enqueue)"
        return "not_crawled_or_empty", f"Strategy={strat}, không bài DB, ít lỗi ghi nhận"

    if errs.get("NotToday", 0) >= max(1, sum(errs.values()) // 2):
        return "not_today", f"Chủ yếu NotToday ({errs.get('NotToday',0)}) — có crawl, không đúng ngày"

    if errs.get("FetchError", 0) or errs.get("ConnectError", 0) or errs.get("HttpError", 0):
        return "fetch_blocked", f"Lỗi mạng/HTTP — {err_str}"

    if errs.get("AccessControlDetected", 0):
        return "access_control", f"Paywall/login/captcha — {err_str}"

    if errs.get("ShortContent", 0):
        return "short_content", f"Trích xuất quá ngắn — {err_str}"

    if art_any.get(sid, 0) > 0:
        return "has_articles_other_days", f"Có {art_any[sid]} bài DB nhưng không pub {TARGET} — {err_str}"

    return "other", f"status={status} strat={strat} — {err_str}"

buckets: dict[str, list[str]] = defaultdict(list)
for dom in sorted(seed.keys()):
    cat, detail = classify(dom)
    buckets[cat].append(f"{dom} | {detail}")

out_lines: list[str] = []
def pr(s: str = "") -> None:
    out_lines.append(s)

pr(f"=== Phan tich export ngay {TARGET} ===")
pr()
pr(f"Seed domains: {len(seed)}")
pr(f"Export hosts: {len(export_hosts)} | articles: {data['count']}")
pr()

labels = {
    "ok_export": "Có bài trong export",
    "not_today": "Đã crawl — lọc NotToday (không đúng ngày)",
    "fetch_blocked": "Lỗi fetch / HTTP / timeout / SSL",
    "access_control": "Chặn truy cập (paywall/login/captcha)",
    "profile_failed": "Profile lỗi (manual_review)",
    "playwright_lane": "Cần Playwright (lane thường không đủ)",
    "short_content": "Nội dung quá ngắn",
    "crawled_no_articles": "Crawl nhưng 0 bài vào DB",
    "has_articles_other_days": "Có bài DB ngày khác, không có pub18",
    "not_crawled_or_empty": "Không thấy bài / ít hoạt động crawl",
    "no_profile": "Không có profile",
    "db_pub18_not_export": "Anomaly",
    "other": "Khác",
}

for key in labels:
    items = buckets.get(key, [])
    if not items:
        continue
    pr()
    pr(f"## {labels[key]} ({len(items)})")
    for line in items[:25]:
        pr(f"  - {line}")
    if len(items) > 25:
        pr(f"  ... +{len(items)-25} nua")

pr()
pr("=== Strategy cua nguon KHONG co export ===")
no_exp = [d for d in seed if classify(d)[0] != "ok_export"]
strat_c = Counter()
for d in no_exp:
    r = prof_by_domain.get(d)
    if r is not None:
        strat_c[str(r.best_strategy)] += 1
for s, n in strat_c.most_common():
    pr(f"  {n:3d}  {s}")

c.close()
report_path = ROOT / "scripts" / "_coverage_report.txt"
report_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
print(f"Wrote {report_path}")
