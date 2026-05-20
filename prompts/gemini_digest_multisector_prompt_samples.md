# Mẫu prompt — Tổng hợp tin đa ngành (48h / 2 ngày)

Dùng với `news_for_ai_clean.json` + batch digest (`summarize_news_gemini.py --batch-digest`).

**Lưu ý:** Đây là bản **mẫu để bạn đọc/ chỉnh**. Khi chạy script, prompt thật được ghép trong code (`build_digest_outline_prompt`, `build_digest_chunk_prompt`, `build_digest_merge_prompt`). Chỗ `{...}` là dữ liệu tự động chèn.

---

## Quy tắc chung (cả 3 bước)

- Chỉ dùng dữ liệu JSON đính kèm — **không** mở URL, không tìm web, không bịa số liệu.
- Tiếng **Việt**, gom chủ đề trùng, ưu tiên tin lặp nhiều nguồn.
- **Đa ngành:** kinh tế & tài chính, chính trị & địa chính trị, xã hội & pháp luật, công nghệ, y tế & môi trường, thể thao & văn hóa — **chỉ** viết mảng có tin trong dữ liệu.
- Mỗi ý quan trọng nên kèm `url` từ dữ liệu khi có.

---

## Bước 0 — Khung toàn cảnh (chỉ title + url, ~2108 bài)

**Mục đích:** Quét hết tiêu đề → chủ đề trội, VN vs quốc tế, timeline sơ bộ. **1 lần API.**

```
Bạn là tổng biên tập tin. Nhiệm vụ: đọc **TOÀN BỘ** danh mục {total_articles} bài (chỉ title, url) và vẽ **bức tranh toàn cảnh** 48 giờ qua.

## Quy tắc
- CHỈ dùng danh mục bên dưới. KHÔNG mở URL, KHÔNG tìm web.
- Phát hiện chủ đề lặp lại trên nhiều nguồn, tin VN vs quốc tế, sự kiện nổi bật nhất.
- Đây là bước **khung xương**; các bước sau sẽ đọc nội dung chi tiết từng phần — khung phải phản ánh **đủ** {total_articles} bài.
- JSON gọn: **tối đa 12** `dominant_themes`, **tối đa 3** mục `timeline_sketch`, **không** liệt kê từng bài trong output (chỉ ước lượng số lượng).

Cửa sổ: {window_meta JSON}

Trả về DUY NHẤT JSON:
{
  "total_articles": {total_articles},
  "panorama_summary": "2-3 đoạn: bức tranh tổng thể 48h",
  "dominant_themes": [
    {
      "theme": "Tên chủ đề/sự kiện",
      "why_dominant": "Vì sao nổi bật (nhiều bài/nguồn)",
      "approx_article_count": "ước lượng số bài liên quan trong danh mục",
      "regions": ["vietnam", "international"],
      "sectors": ["kinh tế", "chính trị", "xã hội", "công nghệ", "thể thao", "..."]
    }
  ],
  "vietnam_vs_global": "So sánh trọng tâm VN và thế giới",
  "timeline_sketch": [
    {"date": "YYYY-MM-DD", "top_headlines": ["5-10 tiêu đề hoặc sự kiện chính"]}
  ],
  "sources_most_active": ["domain1", "domain2"],
  "gaps": "Mảng tin có vẻ thiếu trong danh mục (nếu có)"
}

Danh mục đầy đủ ({total_articles} bài):
[{ "title": "...", "url": "..." }, ...]
```

**Output file:** `gemini_digest_outline.json`

---

## Bước 1…N — Tóm tắt từng chunk (title + url + text đầy đủ)

**Mục đích:** Đọc nội dung từng phần, gắn vào khung. **~N lần API** (tự chia theo token).

```
Bạn là biên tập viên tổng hợp tin. Đây là **phần {batch_index}/{batch_total}** của bản tin 48 giờ (LEON Quant Labs).

## Quy tắc
- CHỈ dùng JSON bài viết bên dưới + khung toàn cảnh (nếu có). KHÔNG mở URL, KHÔNG tìm web, KHÔNG bịa.
- Toàn bộ pipeline có {total_articles} bài; bạn thấy phần này — ghi nhận đủ sự kiện **trong phần được giao**, đối chiếu khung để biết phần này thuộc chủ đề lớn nào.

## Khung toàn cảnh (đã quét HẾT {total_articles} tiêu đề — dùng để không lệch chủ đề)
{global_outline JSON từ bước 0}

## Cửa sổ: {window_meta JSON}

Trả về DUY NHẤT JSON:
{
  "batch_index": {batch_index},
  "batch_total": {batch_total},
  "articles_in_batch": {số bài trong chunk},
  "sector_notes": [
    {
      "name": "Kinh tế & tài chính | Chính trị & địa chính trị | Xã hội & pháp luật | Công nghệ | Y tế & môi trường | Thể thao & văn hóa | ...",
      "summary": "Tóm tắt chi tiết từ phần bài này (chỉ mảng có tin)",
      "key_points": ["...", "..."],
      "source_urls": ["https://...", "..."]
    }
  ],
  "vietnam_notes": "Tin VN trong phần này",
  "international_notes": "Tin quốc tế trong phần này",
  "notable_articles": [
    {"title": "...", "source": "tên báo/domain", "url": "...", "why_notable": "1 câu"}
  ]
}

Dữ liệu phần {batch_index}:
[{ "title": "...", "url": "...", "text": "nội dung full" }, ...]
```

**Output file:** `gemini_digest_partials.json` (gộp dần từng partial)

---

## Bước cuối — Gộp thành bản tin đa ngành (5–10 phút đọc)

**Mục đích:** Một bản duy nhất, đủ lĩnh vực, dễ đọc. **1 lần API.**

```
Bạn là biên tập viên tổng hợp tin LEON Quant Labs.

Đã có {số_partial} bản tóm tắt **phần** (chi tiết nội dung) từ tổng {total_articles} bài tin 48h. Cửa sổ: {window_meta JSON}.

## Khung toàn cảnh (từ TOÀN BỘ {total_articles} tiêu đề — ưu tiên giữ đúng bức tranh tổng)
{global_outline JSON}

Nhiệm vụ: **Gộp** thành **một** bản tin duy nhất, tiếng Việt, đọc **5–10 phút** (~1.500–2.500 từ), **toàn cảnh đa ngành**.
- Khung toàn cảnh = xương sống (chủ đề trội trên toàn bộ {total_articles} bài).
- Partials = chi tiết từng phần — gộp không được làm mất chủ đề lớn trong khung.
- Gom `sector_notes` trùng lĩnh vực; không nhồi nhét từng bài riêng lẻ.
CHỈ dùng dữ liệu được cung cấp — không bổ sung từ bên ngoài.

Trả về DUY NHẤT JSON:
{
  "title": "Bản tin tổng hợp 48 giờ",
  "reading_time_minutes": "5-10",
  "executive_overview": "2-4 đoạn bức tranh chung hai ngày qua",
  "sectors": [
    {
      "name": "Kinh tế & tài chính",
      "summary": "1-3 đoạn",
      "key_points": ["...", "..."],
      "source_urls": ["...", "..."]
    }
  ],
  "vietnam_highlights": "Đoạn riêng tin Việt Nam nổi bật",
  "international_highlights": "Đoạn riêng tin quốc tế nổi bật",
  "timeline": [
    {"date": "YYYY-MM-DD", "headlines": ["sự kiện/tin chính trong ngày"]}
  ],
  "notable_articles": [
    {"title": "...", "source": "...", "url": "...", "why_notable": "..."}
  ],
  "gaps_and_limits": "Thiếu text, mâu thuẫn nguồn, chủ đề chỉ thấy ở tiêu đề (nếu có)"
}

Các partial batch:
[{ sector_notes, vietnam_notes, international_notes, notable_articles }, ...]
```

**Output file:** `gemini_digest_summary.json`

---

## Đa ngành (đã sync vào `summarize_news_gemini.py`)

- **Outline:** tối đa **18** `dominant_themes`, phủ đủ taxonomy (kinh tế, chính trị, xã hội, công nghệ, y tế, môi trường, thể thao, văn hóa, lao động, an ninh…).
- **Chunk:** tối đa **10** `sector_notes`/chunk, **4–8** `key_points`/sector.
- **Merge:** tối thiểu **8** `sectors`, **12** `notable_articles`, ~2.000–3.500 từ; **cấm** gom còn 2–3 mục (hạ tầng/CK/AI).
- Chạy lại **chỉ merge** (không tốn ~23 chunk): `--merge-only --use-existing-outline --resume-partials`

---

## Lệnh chạy (tham khảo)

```bash
python summarize_news_gemini.py --input news_for_ai_clean.json --mode digest --batch-digest --model gemini-2.5-flash --dry-run
# Preflight trước khi chạy full (tránh 429 / JSON lỗi):
python scripts/test_gemini_digest_preflight.py
python scripts/test_gemini_digest_preflight.py --live-chunk   # thử chunk 1 ~200k (tốn quota)

# Mặc định gemini-3.1-flash-lite ~100k/request (free TPM ~125k/min)
python summarize_news_gemini.py --input news_for_ai_clean.json --mode digest --batch-digest --model gemini-3.1-flash-lite --max-api-calls 1 --api-pause 60
# ... lặp với --resume-partials

# Đã có đủ partials — chỉ merge lại (prompt đa ngành mới):
python summarize_news_gemini.py --input news_for_ai_clean.json --mode digest --batch-digest --merge-only --use-existing-outline --resume-partials
```
