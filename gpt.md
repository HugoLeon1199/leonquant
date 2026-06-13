# GPT Notes

## Repo nay lam gi

`leonquant` la repo cho web tin tuc kinh te/thi truong cua LeonQuant.

Pipeline chinh:
- Crawl tin tu nhieu nguon vao DuckDB: `scripts/run_intel_full_daily.py` + `leon_web_intel/`
- Loc va xuat du lieu cho AI: `scripts/export_news_full_for_ai.py` -> `news_for_ai.json` -> `news_for_ai_clean.json`
- Tao ban tin 48h bang Gemini: `scripts/run_digest_from_db.py`, `scripts/run_digest_loop.py`, `summarize_news_gemini.py`
- Dung du lieu web cong khai: `build_website_content.py` -> `content.json` -> `landing_page.html`
- Tab the gioi/invest dung GDELT: `leon.py`, `invest_world_pulse.json`, `market_pulse.json`

Output quan trong:
- `content.json`: du lieu web public
- `landing_page.html`: HTML trang chinh
- `gemini_digest_summary.json`: tom tat Tin48h
- `invest_vn_brief.json`: khoi Viet Nam cho tab dau tu
- `data/web_intel_leonquant.duckdb.gz`: seed DB nho de GitHub Actions bootstrap

## GitHub Actions

Workflow chinh:
- `.github/workflows/daily.yml`: crawl Tin48h + Gemini + build web + invest-world
- `.github/workflows/pages.yml`: deploy GitHub Pages
- `.github/workflows/profile-refresh-monthly.yml`: refresh `source_profiles` moi thang 1 lan hoac chay tay

Logic hien tai:
- Daily run mac dinh dung `--skip-profile`
- Neu gate fail vi DB stale/thin (`rc=6`), daily chi crawl lai 1 lan nua voi source profiles san co
- Khong full re-profile trong cron hang ngay
- Re-profile tach rieng sang workflow monthly/manual

## Ban da sua gi

Commit da push lien quan den gate Tin48h:
- `d9c1f3c` - `Harden Tin48h gate recovery on Actions`
- them stale detection trong `scripts/prepare_digest_db.py`

Commit da push lien quan den daily/profile cadence:
- workflow daily recovery quay lai che do nhe: recrawl, khong `force-refresh-profile`
- them workflow `profile-refresh-monthly.yml`
- cap nhat `README.md`

Commit dang chuan bi push sua CI 2026-06-13:
- Scrapy 2.16 bo goi `start_requests()`: them `async start()` cho 3 spider RSS/Sitemap/HTML
- Pin `scrapy>=2.11.0,<2.17`
- Tang cap BigQuery invest len `750_000_000`

Commit cleanup an toan:
- Bo khoi git `enriched_news.json` va `final_summary.json` vi la output regenerate/stale
- Giu lai output workflow dang dung: `content.json`, `news_for_ai*.json`, `gemini_digest_summary.json`, `invest*.json`
- Local co the xoa `_tmp*`, `_site*`, cache/raw crawl; khong xoa `.env`, `credentials.json`, DB seed

Muc tieu:
- Daily cron nhanh va on dinh hon
- Re-profile nguon web chi chay dinh ky/thu cong
- Giam nguy co job Tin48h bi treo rat lau o pha profile

## Cach nho nhanh cho lan sau

Neu Tin48h hong:
1. Xem run moi nhat cua `Tin Viet Nam 48h digest`
2. Kiem tra no dung o `gate`, `Gemini`, hay `commit`
3. Neu fail o gate, uu tien xem `scripts/prepare_digest_db.py` va block recovery trong `daily.yml`
4. Neu nhieu nguon doi structure, chay workflow `profile-refresh-monthly.yml` bang tay truoc khi retrigger digest
