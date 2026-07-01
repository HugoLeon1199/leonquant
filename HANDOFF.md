# HANDOFF.md — Đồng bộ context giữa Claude và Codex

> File này được cập nhật sau mỗi session làm việc, bất kể dùng Claude hay Codex.
> **Luôn đọc file này trước khi bắt đầu làm việc.**

---

## Session mới nhất

<!-- Cập nhật block này sau mỗi session -->

## [2026-07-01 00:00] - [Codex]

### Da lam
- Trien khai scaffold cho nhanh Bao Cong nghe & AI tach biet khoi Tin 48h / Kinh te dau tu / The gioi LIVE.
- Them config/tech_sources_catalog.txt chua du 100 URL goc theo danh sach user cung cap.
- Them scripts/validate_tech_sources.py cho Phase 0: profile + discovery + sample extract + phan loai + sinh tech_sources_active.txt / tech_disabled_sources.txt / tech_tiers/** / report JSON+MD.
- Them scripts/run_tech_intel_pipeline.py voi precheck validation report, dung seed active + tier active + DB rieng data/web_intel_tech.duckdb.
- Them GDELT tech rieng qua sql/gdelt_tech_pulse.sql va scripts/run_tech_gdelt.py.
- Them publication tech rieng qua scripts/build_tech_publication.py va scripts/validate_tech_publication.py.
- Them tech/index.html standalone; them anchor /tech/ trong landing_page.html; append copy artifact tech trong .github/workflows/pages.yml.
- Them .github/workflows/tech-radar.yml va .github/workflows/tech-profile-refresh.yml.
- Them scripts/test_tech_pipeline.py cho fixture/offline validation.

### Quyet dinh quan trong
- Phase 0 la gate bat buoc: khong cau hinh production tech truoc khi co reports/tech_source_validation.json hop le.
- config/tech_sources_active.txt la seed production thuc te; config/tech_sources_catalog.txt chi la catalog goc 100 nguon.
- config/tech_tiers/** duoc sinh tu report validation, khong hardcode tay truoc.
- Chua chay validation live 100 nguon, nen chua sinh report/active/tier thuc te trong repo.

### File da thay doi
- config/tech_sources_catalog.txt
- scripts/tech_common.py
- scripts/validate_tech_sources.py
- scripts/run_tech_intel_pipeline.py
- sql/gdelt_tech_pulse.sql
- scripts/run_tech_gdelt.py
- scripts/build_tech_publication.py
- scripts/validate_tech_publication.py
- scripts/test_tech_pipeline.py
- tech/index.html
- landing_page.html
- .github/workflows/pages.yml
- .github/workflows/tech-radar.yml
- .github/workflows/tech-profile-refresh.yml
- HANDOFF.md

### Verify / Test
- .\.venv\Scripts\python.exe py-compile pass cho cac script tech moi.
- .\.venv\Scripts\python.exe scripts\test_tech_pipeline.py -> pass.
- Chua chay validation live / crawl tech live / GDELT tech live / publication tech tren data thuc.

### Dang do / Viec tiep theo
- Chay Phase 0 live: .\.venv\Scripts\python.exe scripts\validate_tech_sources.py
- Sau khi co active sources thuc, chay run_tech_intel_pipeline.py, run_tech_gdelt.py --dry-run, build_tech_publication.py, validate_tech_publication.py.

## [2026-06-23 18:40] — [Codex]

### Đã làm
- Điều tra nguyên nhân web không cập nhật và đối chiếu live site, GitHub Actions, cùng preflight Gemini.
- Xác nhận `content.json` public hiện vẫn dừng ở `generatedAt=2026-06-18T09:15:55.577804+00:00`.
- Xác nhận workflow `Tin Việt Nam 48h digest` các run gần đây bị `cancelled` đúng mốc 6 giờ vì job `build-digest` bị quay loop tới timeout.
- Chạy preflight bằng `.venv\Scripts\python.exe` và xác nhận lỗi thực tế là `Gemini HTTP 400 | status=INVALID_ARGUMENT | API Key not found. Please pass a valid API key.`
- Vá code để lỗi Gemini báo rõ nguyên nhân và để digest loop dừng sớm khi gặp lỗi cấu hình fatal thay vì retry vô hạn tới hết 6 giờ.

### Quyết định quan trọng
- Nguyên nhân hiện tại **không phải** do Pages deploy; Pages vẫn chạy. Nút nghẽn nằm ở bước digest không tạo được bản mới.
- Dấu hiệu hiện tại cũng **không phải** 429/quota trước tiên; request Gemini nhỏ nhất đã fail với `API_KEY_INVALID`.
- Giữ `GEMINI_MODEL=gemini-3.1-flash-lite` tạm thời vì model vẫn tồn tại theo docs hiện tại; ưu tiên xử lý key/secret trước.

### File đã thay đổi
- `summarize_news_gemini.py`
- `scripts/run_digest_loop.py`
- `scripts/test_gemini_digest_preflight.py`
- `HANDOFF.md`

### Đang dở / Việc tiếp theo
- Cập nhật `GEMINI_API_KEY` hợp lệ trong local `.env` và trong GitHub Actions secret `GEMINI_API_KEY`.
- Chạy lại `.\.venv\Scripts\python.exe scripts\test_gemini_digest_preflight.py` để xác nhận ping + mini chunk pass.
- Sau khi key hợp lệ, chạy lại workflow daily hoặc local digest để xác minh job không còn treo 6 giờ.

## [2026-06-18 05:59] — [Codex]

### Đã làm
- Cập nhật `AGENTS.md` để ghi rõ workflow bắt buộc cho mọi session.
- Thêm mục "Must Read First" yêu cầu đọc `CLAUDE.md` và `HANDOFF.md` trước khi sửa code.

### Quyết định quan trọng
- Dùng `AGENTS.md` làm file hướng dẫn agent ở mức repo.
- Giữ `CLAUDE.md` là working guide chi tiết và `HANDOFF.md` là nguồn context phiên gần nhất.

### File đã thay đổi
- `AGENTS.md`
- `HANDOFF.md`

### Đang dở / Việc tiếp theo
- Nếu cần, có thể rút gọn thêm `AGENTS.md` để ưu tiên phần rule lên đầu và giảm phần mô tả lặp với `CLAUDE.md`.

---

## Lịch sử sessions

<!-- Các session cũ chuyển xuống đây -->

## [2026-07-01 10:35] - [Codex]

### Da lam
- Bootstrap `pip` trong `.venv` va cai xong `leon_web_intel/requirements.txt` de mo duong chay validation live.
- Kick off `.\.venv\Scripts\python.exe scripts\validate_tech_sources.py` cho Phase 0 tren catalog 100 nguon.
- Xac nhan run live khong crash ngay sau timeout shell; no van tiep tuc o background `python` PID `23308`.

### Quyet dinh quan trong
- Khong commit DuckDB validation cache dang chay (`reports/tech_validation.duckdb*`).
- Chua chot so PASS/SOFT_PASS/BLOCKED vi `reports/tech_source_validation.json` va cac file active/disabled/tier chua duoc flush ra.
- Van giu gate Phase 0: production tech chua duoc xem la san sang cho toi khi report validation hop le ton tai.

### File da thay doi
- `HANDOFF.md`
- `.ai/CURSOR_WORKLOG.md`

### Verify / Test
- `.\.venv\Scripts\python.exe -m ensurepip --upgrade` -> pass
- `.\.venv\Scripts\python.exe -m pip install -r leon_web_intel\requirements.txt` -> pass
- `.\.venv\Scripts\python.exe scripts\validate_tech_sources.py` -> dang chay nen, chua co output cuoi

### Dang do / Viec tiep theo
- Theo doi PID `23308` den khi xong va doc:
  - `reports/tech_source_validation.json`
  - `reports/tech_source_validation.md`
  - `config/tech_sources_active.txt`
  - `config/tech_disabled_sources.txt`
  - `config/tech_tiers/**`
- Sau khi co report cuoi, append lai thong ke PASS / SOFT_PASS / blocked-paywall-captcha / sample extracts / URL can Leon review.
