# LEON Quant — AI Macro Research Desk

**Repo:** [github.com/HugoLeon1199/leonquant](https://github.com/HugoLeon1199/leonquant)

Trang tĩnh (GitHub Pages): `https://hugoleon1199.github.io/leonquant/`

## Pipeline (giữ nguyên thứ tự)

1. `crawl_financial_news.py` — crawl tin.
2. `summarize_news_gemini.py` — Gemini tóm tắt / themes / important articles.
3. `finalize_summary_gpt.py` — **bước duy nhất gọi GPT mạnh**: sinh **`final_summary.json`** theo schema **Daily Macro Intelligence** (tiếng Việt, desk note), có validator + repair 1 lần + fallback từ Gemini nếu vẫn lỗi.
4. `build_website_content.py` — gộp macro + toàn bộ bài enriched → **`content.json`** (camelCase cho web).
5. `landing_page.html` — đọc `content.json`, hiển thị research desk (dark, static).

## Schema output (`final_summary.json` → `summary`)

Trường chính: `title`, `date`, `market_regime`, `daily_thesis`, `thirty_second_summary`, `what_changed`, `top_macro_drivers` (3–5), `asset_impact_heatmap` (≥6), `vietnam_investor_lens`, `scenario_map` (xác suất tổng 100), `key_variables_to_watch`, `source_quality`, `final_takeaway`, `disclaimer`. Chi tiết trong `finalize_summary_gpt.py` (`validate_final_summary`).

## Biến môi trường (chi phí & chất lượng)

| Biến | Mặc định | Ý nghĩa |
|------|----------|---------|
| `OPENAI_API_KEY` | (bắt buộc khi chạy GPT) | Secret — **không commit**. |
| `OPENAI_MODEL` | `gpt-5.4-mini` (fallback `OPENAI_FINAL_MODEL`) | Model bước cuối. |
| `OPENAI_TEMPERATURE` | `0.2` | |
| `OPENAI_MAX_OUTPUT_TOKENS` | `4500` | |
| `MAX_FINAL_ARTICLES` | `18` | Giới hạn bài gửi vào prompt. |
| `MAX_EVIDENCE_CHARS` | `1200` | Cắt mỗi bài trước khi gửi GPT. |
| `MAX_LIVE_SNIPPETS` | `6` | Số URL fetch live verify. |
| `MAX_REPAIR_RETRIES` | `1` | Sửa JSON lần 2 nếu validate fail. |

**Tiết kiệm:** chỉ Gemini + crawl xử lý hàng loạt; GPT chỉ nhận evidence đã lọc + snippet; cache nội dung cắt tại `.cache/article_cache.json`; repair chỉ gửi JSON lỗi + message, không gửi lại toàn bộ evidence.

## Chạy local

```powershell
cd path\to\leonquant-repo
# Cần GEMINI_API_KEY / OPENAI_API_KEY trong môi trường hoặc file `.env`
python finalize_summary_gpt.py --update-content
# Hoặc chỉ build web từ final_summary hiện có:
python build_website_content.py --skip-images
```

Preview UI không gọi API:

```powershell
python scripts\inject_preview_brief.py
python build_website_content.py --skip-images
```

## GitHub Actions

- **`daily.yml`:** crawl → Gemini → GPT → `build_website_content` → **`python -m json.tool`** trên `final_summary.json` và `content.json` → **`python validate_content.py`** → commit.
- **Secrets:** `GEMINI_API_KEY`, `OPENAI_API_KEY` (repository secrets).

## Tài liệu thêm

`CRAWLER_README.md`, `GPT_SUMMARY_README.md`.
