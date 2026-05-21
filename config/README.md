# Crawl configuration (Leon Web Intel)

**6 nhóm nguồn** trong `sources_seed.txt`: (1) Thời sự & chính trị, (2) Kinh tế & đầu tư, (3) Công nghệ & AI, (4) Khoa học & y tế, (5) Pháp luật & đời sống, (6) Crypto.

Bước thu tin dùng **`leon_web_intel/`**: `run_profile.py` (đọc URL seed) + `run_scrapy.py` (theo tier).

| File | Vai trò |
|------|--------|
| **`sources_seed.txt`** | Tier headers (`# …`) + **URL trang / chuyên mục** — input cho **`run_profile.py --input`**. |
| **`tiers/*.txt`** | Mỗi file = allowlist domain cho một tier; **`run_intel_full_daily.py`** truyền vào Scrapy. |
| **`tiers_manifest.json`** | `hostname` → `tier_id` khi **`export_intel_to_news_output.py`**. |
| **`sources_uncrawlable.txt`** | Domain **bỏ qua khi Scrapy** (HTTP/SSL block hoặc profile `manual_review`). Tự refresh sau daily. |
| **`news_sources_tiered.json`** | *(Đã bỏ)* — trước đây dành cho crawler RSS, không còn dùng. |

### Export / audit (sau profile hoặc crawl)

| File | Ý nghĩa |
|------|--------|
| `leon_web_intel/data/exports/review_sources.csv` | **Rộng**: mọi nguồn có tín hiệu paywall/login/captcha/4xx — *không* có nghĩa “ngừng crawl”. |
| `leon_web_intel/data/exports/review_sources_strict.csv` | **Hẹp**: `manual_review`, 4xx, `error_message` — nên xử lý trước. |
| `leon_web_intel/data/exports/source_coverage_report.csv` | `python scripts/source_coverage_report.py` — bài trong DB + lỗi + skip theo `source_id`. |
| `scripts/crawl_baseline_snapshot.md` | `python scripts/crawl_baseline_snapshot.py` — NotToday, số bài, export today. |
| `scripts/zero_article_investigation.md` | `python scripts/investigate_zero_article_sources.py` — phân loại 0 bài. |

**`playwright_fallback`**: profiler có thể chọn Playwright; **daily Scrapy không render JS** — chỉ fallback RSS/sitemap/HTML nếu có.

## Chạy

```powershell
pip install -r leon_web_intel/requirements.txt
playwright install
python scripts/run_intel_full_daily.py --date today --timezone Asia/Ho_Chi_Minh
```

Thêm site: đặt URL vào đúng nhóm trong **`sources_seed.txt`**, chạy `scripts/split_sources_seed_into_tiers.py` nếu cần tách lại tier files, rồi chạy lại **profiler** (bỏ `--skip-profile` một lần).
