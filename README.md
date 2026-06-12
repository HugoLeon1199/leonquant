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
| `market_pulse.json` | Tab **Tin nóng toàn cầu** LIVE (đa lĩnh vực) |
| `invest_world_pulse.json` | Tab đầu tư khối **Thế giới** — cùng enrich GDELT, Gemini lọc **kinh tế/CK/vàng/crypto/vĩ mô** (không trùng LIVE) |
| `invest_pulse.json` | Legacy (`leon.py --channel invest`); tab web không dùng |
| `invest_vn_brief.json`, `web/invest_vn_brief.json` | Tab đầu tư — khối **Việt Nam** (Gemini từ `content.json`, sau daily digest) |
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

Output: **`market_pulse.json`** (LIVE đa lĩnh vực) + **`invest_world_pulse.json`** (tab đầu tư — lọc kinh tế/CK/vàng/crypto/vĩ mô từ cùng pool enrich, một lần `leon.py --channel world`). Production: workflow **LIVE pulse 12h** — commit `market_pulse.json` → Pages.

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

## DuckDB — git nhỏ, CI chỉ cào web

**Vì sao trước hay lỗi:** không phải do “phân loại web” trên CI — do **bài cũ trong cache** + export/prune lệch cửa sổ, đôi khi **re-seed .gz** nạp lại hàng nghìn bài lỗi thời thay vì tin vừa crawl.

**CI hàng ngày (tự động):** xóa bài cũ → **Scrapy cào 48h** → Gemini digest. Daily recovery chỉ **cào lại** với source_profiles sẵn có; **không** full re-profile mỗi ngày.

**Khi bạn đổi link nguồn (tay):**

```powershell
# 1. Sửa config/sources_seed.txt và/hoặc config/tiers/*.txt
# 2. Profile một lần (local)
cd leon_web_intel
python run_profile.py --input ../config/sources_seed.txt --profile-only --db ../data/web_intel_leonquant.duckdb
# 3. Đóng gói seed nhỏ cho git (chỉ profiles, không articles cũ)
cd ..
python scripts/pack_db_seed.py --mode profiles-only
git add data/web_intel_leonquant.duckdb.gz config/
```

| Lưu trữ | Nội dung |
|---------|----------|
| **Git** | `data/web_intel_leonquant.duckdb.gz` — **profiles-only** (~ vài MB) |
| **Actions cache** | `data/web_intel_leonquant.duckdb` — bài sau mỗi lần crawl |

Gate: `prepare_digest_db.py` (sau crawl, **không** re-seed bài cũ) → `data/digest_export_window.json`.

## GitHub Actions

- **`daily.yml`:** hai job **song song** lúc **05:00 VN** (`0 22 * * *` UTC), pipeline tách riêng:
  - **build-digest** — cào web 48h → `content.json` + `invest_vn_brief.json` (Việt Nam trong nước).
  - **invest-world** — `leon.py --channel invest` → `invest_world_pulse.json` (Tin thế giới quan trọng, GDELT 24h).
- **`profile-refresh-monthly.yml`:** refresh `source_profiles` từ `config/sources_seed.txt` mỗi tháng một lần (và có thể chạy tay), rồi pack lại `data/web_intel_leonquant.duckdb.gz` theo mode `profiles-only`.
- **`pulse-hourly.yml`:** chỉ **LIVE** `market_pulse.json` mỗi **12h** (`leon.py --channel world`); không cập nhật invest desk.
- **`pages.yml`:** deploy sau khi workflow *Tin Việt Nam 48h digest* hoàn tất (cả digest + invest-world).
  - Chạy tay digest: Actions → *Tin Việt Nam 48h digest* → *Run workflow*, hoặc `.ci-run-digest` / `.ci-run-invest-daily` trên `main`.
  - Workflow tự gọi Pages API: `cname=leonquant.com`, `https_enforced=true` (tránh trình duyệt báo `NET::ERR_CERT_COMMON_NAME_INVALID` khi server chỉ có cert `*.github.io`).
- **Secret bắt buộc:** repo → Settings → Secrets → `GEMINI_API_KEY` (Google AI Studio).

### Custom domain `leonquant.com` (HTTPS)

DNS (đã đúng hướng GitHub Pages): apex **A** → `185.199.108.153` … `185.199.111.153`; **www** CNAME → `hugoleon1199.github.io`.

Nếu Chrome vẫn báo *Your connection isn't private*:

1. Repo → **Settings → Pages** → Custom domain: `leonquant.com` → đợi DNS check xanh → bật **Enforce HTTPS** (có thể mất vài phút–24h để cert Let's Encrypt `approved`).
2. Actions → **Deploy GitHub Pages** → *Run workflow* (sau khi sửa `pages.yml` có bước Pages API).
3. Cloudflare (nếu có): record **DNS only** (grey cloud) hoặc SSL **Full (strict)** — tránh **Flexible** với GitHub Pages.

Prompt mẫu: `prompts/gemini_digest_multisector_prompt_samples.md`
