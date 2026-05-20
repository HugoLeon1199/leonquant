# Prompt: Tổng hợp tin 2 ngày (news_for_ai.json)

## Export 2 ngày gần nhất (chỉ `title`, `url`, `text`)

```bash
python scripts/export_news_full_for_ai.py
# mặc định: --date today --recent-calendar-days 2
```

## Lệnh khuyến nghị (chia batch — vừa context 1M)

```bash
python summarize_news_gemini.py --input news_for_ai.json --mode digest --batch-digest --model gemini-1.5-flash
```

- **Bước 0:** đọc **toàn bộ tiêu đề** (~2482 bài / 2 ngày) → khung toàn cảnh (`gemini_digest_outline.json`).
- **Bước 1–6:** đọc nội dung full từng phần (~2M ký tự/phần), có khung → `gemini_digest_partials.json`.
- **Bước 7:** gộp khung + các phần → `gemini_digest_summary.json` (~**8 lần API**/ngày).
- Không fetch URL. Partial: `gemini_digest_partials.json` → kết quả: `gemini_digest_summary.json`.

## Một lần gọi (dễ vượt 1M token)

```bash
python summarize_news_gemini.py --input news_for_ai.json --mode digest
```

`GEMINI_API_KEY` trong `.env`. Xem quota thật: [AI Studio → Rate limits](https://aistudio.google.com/rate-limit).
