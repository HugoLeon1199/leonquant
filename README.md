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

Mỗi chuyên mục digest: mục tiêu **~12** tin (`DIGEST_TARGET_SUB_TOPICS_PER_SECTOR`), tối đa **20**; mỗi mục **bắt buộc 1 link** (`source_urls` từ Gemini). Tổng quan + tóm tắt: **chỉ từ bài crawl**, ưu tiên **tin nóng đa chủ đề** (không bịa, không chỉ 1–2 headline).
| `data/web_intel_leonquant.duckdb` | Cache crawl (Actions) |

Sinh local, không commit: `news_output_today.json`, `news_for_ai.json`, `gemini_digest_outline.json`, `gemini_digest_partials.json`.

## Biến môi trường

| Biến | Ý nghĩa |
|------|---------|
| `GEMINI_API_KEY` | Bắt buộc cho digest (secret) |
| `GEMINI_MODEL` | Mặc định trong code: `gemini-3.1-flash-lite` |

## Leon Web Intel

```powershell
pip install -r leon_web_intel/requirements.txt
playwright install
python scripts/run_intel_full_daily.py --date today --timezone Asia/Ho_Chi_Minh --skip-profile
```

## GitHub Actions

- **`daily.yml`:** crawl → export → clean → Gemini digest → `content.json` → commit → push `main`.
  - **Lịch:** mỗi ngày **05:00 giờ Việt Nam** (ICT, UTC+7) — cron `0 22 * * *` UTC.
  - Chạy tay: Actions → *Daily news digest* → *Run workflow*, hoặc push thay đổi `.ci-run-digest` lên `main`.
- **`pages.yml`:** deploy site sau push `main` và **sau khi Daily digest commit xong** (bot push không tự kích hoạt workflow khác).
- **Secret bắt buộc:** repo → Settings → Secrets → `GEMINI_API_KEY` (Google AI Studio).

Prompt mẫu: `prompts/gemini_digest_multisector_prompt_samples.md`
