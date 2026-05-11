# LEON Quant — Vietnam Macro & Market Strategy Brief

**Repo:** [github.com/HugoLeon1199/leonquant](https://github.com/HugoLeon1199/leonquant)

Trang tĩnh (GitHub Pages): `https://hugoleon1199.github.io/leonquant/`

## Pipeline (giữ nguyên thứ tự)

1. `crawl_financial_news.py` — thu thập tin.
2. `summarize_news_gemini.py` — tóm tắt nội bộ / themes / important articles.
3. `finalize_summary_gpt.py` — lớp biên tập cuối: sinh **`final_summary.json`** theo **Investment Strategy Brief** (tiếng Việt, ghi chú chiến lược), có validator + sửa JSON + bản dự phòng khi lỗi.
4. `build_website_content.py` — gộp brief + toàn bộ bài enriched → **`content.json`** (camelCase cho web, không đẩy metadata nội bộ ra trang công khai).
5. `landing_page.html` — đọc `content.json`, hiển thị brief (dark, static).

Trang công khai được định vị như **ấn phẩm nghiên cứu vĩ mô / chiến lược** cho nhà đầu tư Việt Nam; **không** hiển thị disclaimer, bảng điều khiển kiểu dashboard, hay nhãn về chất lượng nguồn / liên kết xác minh.

## Schema (`final_summary.json` → `summary`)

Các trường chính: `title`, `date`, `generated_at`, `publication_intro`, `main_thesis`, `global_macro_drivers`, `vietnam_transmission`, `quick_actions`, `allocation_guide`, `sector_priority`, `increase_risk_signals`, `reduce_risk_signals`, `scenario_plan`, `final_takeaway`. Chi tiết trong `finalize_summary_gpt.py` (`validate_final_summary`). Thống kê pipeline (số bài quét, v.v.) nằm ở `meta`, không nằm trong `summary`.

## Biến môi trường (chi phí & chất lượng)

| Biến | Mặc định | Ý nghĩa |
|------|----------|---------|
| `OPENAI_API_KEY` | (bắt buộc khi chạy bước OpenAI) | Secret — **không commit**. |
| `OPENAI_MODEL` | `gpt-5.4-mini` (fallback `OPENAI_FINAL_MODEL`) | Model bước cuối. |
| `OPENAI_TEMPERATURE` | `0.2` | |
| `OPENAI_MAX_OUTPUT_TOKENS` | `4500` | |
| `MAX_FINAL_ARTICLES` | `18` | Giới hạn bài gửi vào prompt. |
| `MAX_EVIDENCE_CHARS` | `1200` | Cắt mỗi bài trước khi gửi GPT. |
| `MAX_LIVE_SNIPPETS` | `6` | Số URL fetch live verify. |
| `MAX_REPAIR_RETRIES` | `1` | Sửa JSON lần 2 nếu validate fail. |

**Tiết kiệm:** cache nội dung cắt tại `.cache/article_cache.json`; bước sửa JSON chỉ gửi bản lỗi + message lỗi.

## Chạy local

```powershell
cd path\to\leonquant-repo
# Cần OPENAI_API_KEY trong môi trường hoặc `.env`
python finalize_summary_gpt.py --update-content --skip-web-verify
# Hoặc chỉ build web từ final_summary hiện có:
python build_website_content.py --skip-images
python validate_content.py
```

**GitHub Pages chỉ thấy thay đổi sau khi bạn `git push`.** Nếu `python`/`py` trên Windows trỏ sai (ví dụ `D:\python.exe` không tồn tại), đồng bộ `final_summary.json` + `content.json` từ seed bằng Node:

```powershell
node scripts/sync_public_brief.mjs
```

Preview UI không gọi API (Python):

```powershell
python scripts\inject_preview_brief.py
python build_website_content.py --skip-images
python validate_content.py
```

## GitHub Actions

- **`daily.yml`:** crawl → Gemini → GPT → `build_website_content` → **`python -m json.tool`** trên `final_summary.json` và `content.json` → **`python validate_content.py`** → commit.
- **Secrets:** `GEMINI_API_KEY`, `OPENAI_API_KEY` (repository secrets).

## Tài liệu thêm

`CRAWLER_README.md`, `GPT_SUMMARY_README.md`.
