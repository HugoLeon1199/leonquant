# LEON Quant — Tin tức kinh tế 48h

**Repo:** [github.com/HugoLeon1199/leonquant](https://github.com/HugoLeon1199/leonquant)

Trang công khai: [hugoleon1199.github.io/leonquant](https://hugoleon1199.github.io/leonquant/) · [leonquant.com](https://leonquant.com)

## Pipeline

1. **Crawl** — `scripts/run_intel_full_daily.py` (+ `leon_web_intel/`): Scrapy theo tier → DuckDB → `news_output_today.json`. Hằng ngày thêm `--skip-profile` khi profile đã ổn.
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

## Artefact chính

| File | Vai trò |
|------|---------|
| `news_output_today.json` | Bài theo ngày crawl |
| `news_for_ai_clean.json` | Input digest (đã lọc) |
| `gemini_digest_summary.json` | Bản tin đa ngành 48h (commit) |
| `gemini_digest_outline.json` | Outline batch (commit, resume) |
| `gemini_digest_partials.json` | Trung gian (gitignore) |
| `content.json` | Dữ liệu trang công khai |

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

- **`daily.yml`:** crawl → export → clean → digest → `content.json` → commit.
- **`pages.yml`:** deploy từ `content.json` + HTML.
- **Secret:** `GEMINI_API_KEY`

Prompt mẫu: `prompts/gemini_digest_multisector_prompt_samples.md`
