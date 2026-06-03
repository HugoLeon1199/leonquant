# LEON Quant — Tin tức kinh tế 48h

**Repo:** [github.com/HugoLeon1199/leonquant](https://github.com/HugoLeon1199/leonquant)

Trang công khai: [hugoleon1199.github.io/leonquant](https://hugoleon1199.github.io/leonquant/) · [leonquant.com](https://leonquant.com)

## Pipeline

1. **Crawl** — `scripts/run_intel_full_daily.py` (+ `leon_web_intel/`): Scrapy theo tier → DuckDB. Hằng ngày thêm `--skip-profile` khi profile đã ổn.
2. **Chuẩn bị AI** — `scripts/export_news_full_for_ai.py` → `news_for_ai.json`, rồi `scripts/clean_news_for_ai.py` → **`news_for_ai_clean.json`**.
3. **Gemini digest** — `summarize_news_gemini.py` hoặc `scripts/run_digest_loop.py` → **`gemini_digest_summary.json`**.
4. **Web** — `build_website_content.py` → **`content.json`** → `landing_page.html` (GitHub Pages).

**Một lệnh local:**

```powershell
python scripts/run_daily_brief.py --skip-profile --digest-loop --build-site
```

Chỉ export + digest (đã crawl xong):

```powershell
python scripts/run_daily_brief.py --skip-crawl --digest-loop
```

Preflight: `python scripts/test_gemini_digest_preflight.py`

Merge đa ngành khi đã có partials:

```powershell
python summarize_news_gemini.py --input news_for_ai_clean.json --mode digest --batch-digest --merge-only --use-existing-outline --resume-partials
```

## Artefact chính (commit trên `main`)

| File | Vai trò |
|------|---------|
| `news_for_ai_clean.json` | Input digest (đã lọc) |
| `gemini_digest_summary.json` | Bản tin đa ngành 48h |
| `content.json` | Dữ liệu trang công khai |
| `market_pulse.json`, `web/market_pulse.json` | LIVE tab — GDELT hot events |
| `data/web_intel_leonquant.duckdb` | Cache crawl (Actions) |

Digest: ~12 tin/sector (max 20), mỗi mục 1 link; tổng quan từ bài crawl (không bịa).

## World Pulse — GDELT BigQuery (tab LIVE, tách khỏi digest 48h)

Radar sự kiện toàn cầu từ [GDELT](https://www.gdeltproject.org/) qua BigQuery — **đa lĩnh vực** (chính trị, xung đột, kinh tế, tech, y tế, khí hậu, crypto…), không chỉ tài chính.

```powershell
pip install -r requirements-gdelt.txt
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\sa.json"
$env:GOOGLE_CLOUD_PROJECT="your-gcp-project"
$env:GEMINI_API_KEY="..."
python leon.py --dry-run
python leon.py
```

Output: **`market_pulse.json`** + **`web/market_pulse.json`**. Production: workflow **LIVE pulse 6h** (`cron: 0 */6 * * *`) — commit JSON → GitHub Pages deploy.

Secrets Actions: `GEMINI_API_KEY`, `GCP_SA_JSON`, `GOOGLE_CLOUD_PROJECT`.

Sinh local, không commit: `news_output_today.json`, `news_for_ai.json`, `gemini_digest_outline.json`, `gemini_digest_partials.json`.

## Biến môi trường

| Biến | Ý nghĩa |
|------|---------|
| `GEMINI_API_KEY` | Bắt buộc cho digest (secret) |
| `GEMINI_MODEL` | Mặc định trong code: `gemini-3.1-flash-lite` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Service account JSON (GDELT / `leon.py`) |
| `GOOGLE_CLOUD_PROJECT` | GCP project id |

## Leon Web Intel

```powershell
pip install -r leon_web_intel/requirements.txt
playwright install
python scripts/run_intel_full_daily.py --date today --timezone Asia/Ho_Chi_Minh --skip-profile
```

## DuckDB — git nhỏ, cache CI

| Lưu trữ | Nội dung |
|---------|----------|
| **Git** | Chỉ `data/web_intel_leonquant.duckdb.gz` (gzip). Nên **profiles-only** (~ vài MB), không nhét hàng nghìn bài cũ. |
| **Actions cache** | `data/web_intel_leonquant.duckdb` (articles 48h sau mỗi lần crawl + prune). **Không commit** file `.duckdb` thô. |

Tạo seed nhỏ cho git (xóa articles cũ, giữ `source_profiles`):

```powershell
python scripts/pack_db_seed.py --mode profiles-only
git add data/web_intel_leonquant.duckdb.gz
```

Gate trước Gemini (tránh lỗi “0 bài” im lặng): `prepare_digest_db.py` ghi `data/digest_export_window.json` — export, digest và prune **dùng chung file này** (cùng cửa sổ 2→7 ngày hoặc rolling 48h).

## GitHub Actions

- **`daily.yml`:** crawl (bắt buộc ≥5 bài) → `prepare_digest_db.py` (gate) → Gemini → prune (cùng cửa sổ) → commit `content.json`.
  - **Lịch:** mỗi ngày **05:00 giờ Việt Nam** (ICT, UTC+7) — cron `0 22 * * *` UTC.
  - Chạy tay: Actions → *Daily news digest* → *Run workflow*, hoặc push thay đổi `.ci-run-digest` lên `main`.
- **`pages.yml`:** deploy site sau push `main` và **sau khi Daily digest commit xong** (bot push không tự kích hoạt workflow khác).
- **Secret bắt buộc:** repo → Settings → Secrets → `GEMINI_API_KEY` (Google AI Studio).

Prompt mẫu: `prompts/gemini_digest_multisector_prompt_samples.md`
