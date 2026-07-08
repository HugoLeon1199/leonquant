# HANDOFF.md — Đồng bộ context giữa Claude và Codex

> File này được cập nhật sau mỗi session làm việc, bất kể dùng Claude hay Codex.
> **Luôn đọc file này trước khi bắt đầu làm việc.**

---

## Session mới nhất

<!-- Cập nhật block này sau mỗi session -->

## [2026-07-08 18:25] - [Codex]

### Da lam
- Doc `CLAUDE.md`, `HANDOFF.md`, va `.ai/CURSOR_WORKLOG.md` truoc khi sua.
- Giu scope hep trong standalone `tech/`, Tech workflow, Tech GDELT SQL/Python filter, va `tech/index.html`; khong dung Tin48h/Invest/World.
- Mo rong `tech/config/frontier_watchlist.json` len 26 entity gom China AI, Flux/BFL, ComfyUI, Runway/Kling/Veo/Sora, HunyuanVideo, OpenRouter/Replicate/fal.ai, MCP/LangGraph/LlamaIndex, Cursor/Claude Code/OpenHands.
- Them candidate lanes va contract moi: `source_lane`, `matched_entity`, `matched_alias`, `published_at`, `discovered_at`, `time_verified`, `evidence`, `url`, `title`.
- Them artifact moi: `tech/data/candidates_rolling.json`, `tech/data/watchlist_status.json`, `tech/reports/source_coverage_matrix.md`.
- Tach acquisition khoi publish gate: Tech workflow crawl + GDELT moi run; publication JSON chinh chi update khi gate 72h pass/manual. Khi chua publish, build temp de refresh rolling/status/matrix.
- Sua `tech/crawl.py` de crawl mac dinh khong bi gate 72h; `--respect-publish-gate` la opt-in.
- Them `top_signal_clusters` va UI `/tech/` uu tien Top Signal Clusters; Must Read cu giu backward-compatible.
- Compact Full Link Radar them `cluster_id`, `one_line_reason`, `source_lane`, `published_at`.
- GDELT hardening: mo rong keyword/entity va danh dau reuse event cu bang `reused_previous_events`, `fresh_event_count`, `previous_events_age_hours`.
- Validator them check watchlist/status, top clusters, source lanes, model_hub/image_video candidates, Full Radar compact, GDELT reuse label, va muc do ca nhan hoa quanh Leon.
- Them fixture tests cho GLM-5.2, Flux/BFL, ComfyUI, GitHub release, Hugging Face model card, OpenRouter, MCP/LangGraph/LlamaIndex, Cursor/Claude Code/OpenHands.
- Cap nhat `.ai/CURSOR_WORKLOG.md` voi so lieu that.

### Ket qua / Test
- `.\.venv\Scripts\python.exe -m py_compile tech\crawl.py scripts\build_tech_publication.py scripts\validate_tech_publication.py scripts\run_tech_gdelt.py scripts\test_tech_pipeline.py scripts\tech_common.py` -> pass.
- `.\.venv\Scripts\python.exe scripts\test_tech_pipeline.py` -> pass.
- `LEON_TECH_OFFLINE_TEST=1` + `.\.venv\Scripts\python.exe tech\publication.py` -> pass.
- `.\.venv\Scripts\python.exe tech\validate_publication.py` -> pass.

### Trang thai hien tai
- Local artifact generated_at_utc=`2026-07-08T18:20:21.311015+00:00`.
- Active sources: 7.
- Candidates by lane: `github_release=12`, `frontier_watchlist=21`, `huggingface_model=6`, `model_hub=4`, `image_video_workflow=8`, `gdelt=27`, `normal_web=1`, `community=9`.
- Watchlist checked/hit: `26 / 55`.
- GDELT fresh/reused: `fresh_event_count=40`, `reused_previous_events=False`.
- Top signal clusters: 10; Full Link Radar: 88; Must Read: 20, source mix `official=20`.
- Local rebuild dung offline curator mode, nen production Actions/Gemini can chay lai de co editorial copy that.

### File da thay doi
- `.github/workflows/tech-radar.yml`
- `scripts/build_tech_publication.py`
- `scripts/run_tech_gdelt.py`
- `scripts/tech_common.py`
- `scripts/test_tech_pipeline.py`
- `scripts/validate_tech_publication.py`
- `sql/gdelt_tech_pulse.sql`
- `tech/crawl.py`
- `tech/index.html`
- `tech/config/frontier_watchlist.json`
- `tech/data/candidates_rolling.json`
- `tech/data/watchlist_status.json`
- `tech/data/publication.json`
- `tech/web/publication.json`
- `tech/reports/source_coverage_matrix.md`
- `.ai/CURSOR_WORKLOG.md`
- `HANDOFF.md`

### Dang do / Viec tiep theo
- Chay manual dispatch `Tech Radar` tren GitHub Actions de rebuild production bang secrets/GDELT/Gemini that.
- Source coverage van yeu (`7 / 100` active); nen tiep tuc recover official/independent sources neu muon radar bot phu thuoc vao watchlist synthetic lanes hon.

## [2026-07-08 00:00] - [Codex]

### Da lam
- Doc `CLAUDE.md` va `HANDOFF.md` truoc khi kiem tra repo.
- Xac nhan co `tech/config/frontier_watchlist.json`.
- Doc nhanh file watchlist va doi chieu usage: builder Tech load/apply watchlist trong `scripts/build_tech_publication.py`, validator/test/workflow cung co check/stage file nay.

### Ket qua / Test
- Khong chay test vi session chi kiem tra file/cau hinh.

### File da thay doi
- `HANDOFF.md`

### Dang do / Viec tiep theo
- Neu can sua watchlist, nen tiep tuc trong scope Tech Radar va chay `.\.venv\Scripts\python.exe scripts\test_tech_pipeline.py` sau khi sua.

## [2026-07-06 18:05] - [Codex]

### Da lam
- Doc `.ai/CURSOR_WORKLOG.md`, `CLAUDE.md`, `HANDOFF.md` truoc khi sua.
- Them `Tech Radar` vao `.github/workflows/pages.yml` `workflow_run` de Tech workflow success se kich Pages deploy.
- Tao `tech/config/frontier_watchlist.json` voi 11 entity China/frontier AI va alias bat buoc, gom Z.ai/Zhipu/BigModel/GLM/ChatGLM/GLM-5/GLM-5.2.
- Them nguon truc tiep cho Zhipu/GLM qua Z.ai blog/docs, BigModel docs/release notes, Hugging Face `zai-org`, GitHub `zai-org`.
- Noi watchlist acquisition vao `scripts/build_tech_publication.py`: candidate match alias co `matched_entity`, `matched_alias`, `trend_status`, evidence, source_type/signal metadata va stats.
- Sua Must Read ranking de uu tien official/independent, khong fill >50% community khi co non-community candidate, va chan importance=1 tru khi `evidence=exploratory`.
- Cap nhat validator de fail community share >50% khi co non-community, fail importance=1 thieu exploratory, va check watchlist count.
- Them GLM-5.2 fixture trong `scripts/test_tech_pipeline.py`.
- Cap nhat `tech/update_worklog.py` va `.ai/CURSOR_WORKLOG.md` voi watchlist/page/test/source-mix fields.

### Ket qua / Test
- `.\.venv\Scripts\python.exe -m py_compile scripts\build_tech_publication.py scripts\validate_tech_publication.py scripts\test_tech_pipeline.py tech\update_worklog.py` -> pass.
- `.\.venv\Scripts\python.exe scripts\test_tech_pipeline.py` -> pass.
- Temp rebuild bang `LEON_TECH_OFFLINE_TEST=1` + `tech\publication.py --output <temp>` va `tech\validate_publication.py --input <temp>` -> pass.

### Trang thai hien tai
- Fixture GLM-5.2 detected: yes.
- Current local 72h artifact data GLM-5.2 detected: no, vi crawl/GDELT hien co chua co GLM/Zhipu/Z.ai signal.
- Temp rebuild tu data hien tai co watchlist entities=11, candidates_from_watchlist=3, Must Read source type `community=1`, `independent=1`; main candidates official=0, independent=1, community=8.
- Khong regenerate `tech/data/publication.json` local vi local dang offline/fallback va du lieu hien tai chua co GLM-5.2; de Actions/Gemini/GDELT run that sinh artifact moi.

### File da thay doi
- `.github/workflows/pages.yml`
- `.github/workflows/tech-radar.yml`
- `scripts/build_tech_publication.py`
- `scripts/tech_common.py`
- `scripts/test_tech_pipeline.py`
- `scripts/validate_tech_publication.py`
- `tech/config/frontier_watchlist.json`
- `tech/update_worklog.py`
- `.ai/CURSOR_WORKLOG.md`
- `HANDOFF.md`

### Dang do / Viec tiep theo
- Chay manual dispatch `Tech Radar` tren GitHub Actions neu muon lay artifact production moi ngay, dung secrets/GDELT/Gemini that.
- Sau run that, doi chieu `stats.glm_5_2_detected`, `watchlist_candidate_count`, `must_read_by_source_type`, va Pages auto deploy.

## [2026-07-06 17:14] - [Codex]

### Da lam
- Kiem tra web public hien tai cho `leonquant.com` va GitHub Pages mirror.
- Xac nhan `https://leonquant.com/`, `/content.json`, `/tech/`, `/tech/data/publication.json`, `market_pulse.json`, `invest_world_pulse.json`, va `invest_vn_brief.json` deu tra HTTP 200.
- Doi chieu workflow GitHub Actions gan nhat: daily digest, LIVE pulse, Tech Radar, Pages deploy.
- Chay validator remote `content.json` bang `validate_content.py --content-input` va pass.

### Ket qua chinh
- Web chinh dang moi: `content.json generatedAt=2026-07-05T23:08:25.247281+00:00`, `briefMode=newsroom-brief`, `frontPage=3`, `sectorDeepBriefs=4`, `digestSectors=4`.
- Daily workflow `Tin Viet Nam 48h digest` run `28757461680` da success luc `2026-07-05T23:09:03Z`.
- LIVE pulse public: `market_pulse.json generated_at_utc=2026-07-06T01:33:01.009694+00:00`, `total_events=5`; workflow `LIVE pulse 12h` run `28762133732` success.
- Invest world public: `invest_world_pulse.json generated_at_utc=2026-07-05T22:46:49.739374+00:00`, `topics=2`, `events=4`.
- Invest VN public: `invest_vn_brief.json generated_at_utc=2026-07-05T23:08:55.592051+00:00`.
- Tech public artifact van la ban `generated_at_utc=2026-07-05T06:24:34.693189+00:00`, schema `ai-frontier-radar-72h-v1`, `must_read_count=6`, `full_link_radar_count=37`, `gemini_success_count=10`.

### Quyet dinh / Ghi chu
- Khong sua code trong session nay.
- Hai run Tech Radar ngay `2026-07-06` success nhung skip crawl/GDELT/build do gate 72h: run moi nhat ghi `Tech publish age 29.3h < 72h, skipping tech refresh.`
- Pages deploy gan nhat success run `28762223635` luc `2026-07-06T01:33:59Z`; co hai Pages run failure truoc do nhung public web hien tai van tra 200 va artifact main dang dung.
- Validator Tech chay truc tiep tren remote JSON bang local validator bi fail cross-check URL vi validator doi input crawl/GDELT local tuong ung, khong phai bang chung artifact public hong.

### File da thay doi
- `HANDOFF.md`

### Dang do / Viec tiep theo
- Neu muon Tech refresh ngay, chay manual dispatch `Tech Radar` de bypass gate 72h.
- Neu muon soi UI bang mat/screenshot, mo browser check visual cho `/` va `/tech/`.

## [2026-07-05 08:50] - [Codex]

### Da lam
- Sua chat luong module `tech/` ma khong dung vao Tin48h / Invest / World.
- Viet lai `scripts/build_tech_publication.py` de publication chi dung du lieu live tu `tech/data/news_for_ai_clean.json` va `tech/data/gdelt_pulse.json` neu co.
- Loai bo hoan toan validation samples khoi publication; validation sample khong con duoc dung lam tin.
- Sua `source_type` theo dung uu tien `community` truoc `official`.
- Them lop AI curator trong builder; local runtime hien tai doc duoc `GEMINI_API_KEY` tu `.env` nhung key tra ve `API_KEY_INVALID`, vi vay publication run that dang roi ve fallback sach cho Full Radar va khong auto day bai vao Must Read.
- Viet lai `tech/index.html` bang tieng Viet co dau, sua render Knowledge / Founder Ideas dung field schema that, va sua importance theo so 1-5.
- Cap nhat `scripts/validate_tech_publication.py`, `tech/test_pipeline.py`, `tech/update_worklog.py`.
- Chay refresh crawl Tech that de lay data 72h moi, sau do rebuild publication va cap nhat worklog.

### Quyet dinh quan trong
- Giu nguyen scope hep: chi sua `tech/**` va 2 script publication/validator.
- Khong ep bai fallback vao Must Read khi curator Gemini local that bai; chi giu trong Full Radar de tranh fill noi dung yeu.
- Validator moi siet cac rule chat luong duoc user neu: forum khong duoc tag official, bai qua han 72h khong duoc vao section chinh, public text phai co dau, support-noise khong duoc importance cao, Knowledge/Founder phai co du field.

### File da thay doi
- `scripts/build_tech_publication.py`
- `scripts/validate_tech_publication.py`
- `tech/common.py`
- `tech/index.html`
- `tech/test_pipeline.py`
- `tech/update_worklog.py`
- `tech/data/news_output_today.json`
- `tech/data/news_output_all.json`
- `tech/data/news_for_ai.json`
- `tech/data/news_for_ai_clean.json`
- `tech/data/publication.json`
- `tech/web/publication.json`
- `.ai/CURSOR_WORKLOG.md`
- `HANDOFF.md`

### Verify / Test
- `.\.venv\Scripts\python.exe tech\crawl.py --force` -> pass
- `.\.venv\Scripts\python.exe tech\publication.py` -> pass
- `.\.venv\Scripts\python.exe tech\validate_publication.py` -> pass
- `.\.venv\Scripts\python.exe tech\test_pipeline.py` -> pass
- `.\.venv\Scripts\python.exe tech\update_worklog.py` -> pass

### Trang thai hien tai
- Crawl 72h moi da cho ra `tech/data/news_for_ai_clean.json` voi 10 bai live.
- `tech/data/publication.json` / `tech/web/publication.json` da rebuild tren data moi.
- `sections.ai_knowledge` va `sections.founder_ideas_for_leon` da co du field de frontend render.
- Local Gemini curator hien tai khong thanh cong do `API_KEY_INVALID`, nen publication run nay co `gemini_success_count = 0`, `gemini_fallback_count = 10`, `must_read_count = 0`.

### Dang do / Viec tiep theo
- Can `GEMINI_API_KEY` hop le neu muon co Must Read va section chinh duoc curator that tay, thay vi fallback-only.
- Neu muon day web/push, stage dung nhom file Tech + worklog va bo qua cac thay doi unrelated dang co san trong repo.

## [2026-07-03 07:05] - [Codex]

### Da lam
- Sua hep module `tech/` de doi publication public sang `ai-frontier-radar-72h-v1`.
- Viet lai dashboard `tech/index.html` thanh `AI Frontier Radar 72h`, fetch truc tiep `./data/publication.json`, bo render kieu cu va sap xep lai cac khoi theo schema moi.
- Cap nhat `tech/common.py` de schema chung cua module Tech khop voi artifact moi.
- Viet lai `tech/test_pipeline.py` thanh bo test standalone cho schema 72h moi, frontend contract va forbidden public terms.
- Regenerate `tech/data/publication.json` va `tech/web/publication.json` bang publication builder moi.
- Cap nhat `tech/update_worklog.py` va append `.ai/CURSOR_WORKLOG.md` voi thong ke `must_read`, `full_link_radar` va cac section chinh.

### Quyet dinh quan trong
- Giu nguyen pham vi: chi sua `tech/**` va 2 script publication/validator; khong dung vao Tin48h / Invest / World / pages cu.
- Builder smoke test duoc tach khoi artifact-final validation: build tu du lieu toi gian co the it hon 30 radar links, nhung artifact public cuoi van phai dat validator 72h.
- `tech/data/gdelt_pulse.json` van chua co trong workspace hien tai, nen lan sua nay khong tuyen bo DONE cho GDELT live.

### File da thay doi
- `scripts/build_tech_publication.py`
- `scripts/validate_tech_publication.py`
- `tech/common.py`
- `tech/index.html`
- `tech/test_pipeline.py`
- `tech/update_worklog.py`
- `tech/data/publication.json`
- `tech/web/publication.json`
- `.ai/CURSOR_WORKLOG.md`
- `HANDOFF.md`

### Verify / Test
- `.\.venv\Scripts\python.exe tech\publication.py` -> pass
- `.\.venv\Scripts\python.exe tech\validate_publication.py` -> pass
- `.\.venv\Scripts\python.exe tech\test_pipeline.py` -> pass
- `.\.venv\Scripts\python.exe tech\update_worklog.py` -> pass

### Trang thai hien tai
- `tech/data/publication.json` da la `ai-frontier-radar-72h-v1`
- `window_hours = 72`
- `tech/web/publication.json` da dong bo schema moi
- Frontend `/tech/` da doc dung `tech/data/publication.json` va hien thi label `AI Frontier Radar 72h`

### Dang do / Viec tiep theo
- Can chay GDELT that de tao `tech/data/gdelt_pulse.json` neu muon chot workflow/publication day du theo tieu chi production.
- Neu can push, chi stage cac file Tech o tren va bo qua cac thay doi unrelated dang co san trong repo.

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

## [2026-07-01 14:45] - [Codex]

### Da lam
- Them lop wrapper Tech trong `tech/` de chay bang `python tech/...` ma van re-use cac script o `scripts/`.
- Chuyen artifact Tech sang `tech/config`, `tech/data`, `tech/reports`, `tech/web` thong qua `LEON_TECH_BASE_DIR`.
- Smoke live `python tech/validate_sources.py --limit 1` da pass va ghi dung vao `tech/reports/source_validation.json`.

### Quyet dinh quan trong
- Gi? full Phase 0 validation la job live dang chay rieng; khong ep commit report partial.
- Tech crawl/export/publication/GDELT/validate/test se chay qua `tech/` entrypoints, khong co tac dong den Tin48h / Invest / World / Pages cu.

### File da thay doi
- `tech/_bootstrap.py`
- `tech/validate_sources.py`
- `tech/crawl.py`
- `tech/gdelt.py`
- `tech/publication.py`
- `tech/validate_publication.py`
- `tech/test_pipeline.py`
- `scripts/tech_common.py`
- `scripts/validate_tech_sources.py`
- `scripts/run_tech_intel_pipeline.py`
- `scripts/run_tech_gdelt.py`
- `scripts/build_tech_publication.py`
- `sql/gdelt_tech_pulse.sql`
- `.github/workflows/tech-radar.yml`
- `.github/workflows/tech-profile-refresh.yml`
- `.github/workflows/pages.yml`
- `tech/index.html`
- `tech/config/tech_sources_catalog.txt`
- `HANDOFF.md`

### Verify / Test
- `.\.venv\Scripts\python.exe -m py_compile ...` cho bo script tech moi -> pass.
- `.\.venv\Scripts\python.exe tech\test_pipeline.py` -> pass.
- `.\.venv\Scripts\python.exe tech\validate_sources.py --limit 1` -> pass va sinh output tech standalone.
- Full `.\.venv\Scripts\python.exe tech\validate_sources.py --force-refresh` -> dang chay nen PID `46404`, chua flush report cuoi.

### Dang do / Viec tiep theo
- Cho PID `46404` xong hoac chuyen sang batch/limit neu can cat thoi gian.
- Khi co report full, cap nhat tong PASS / SOFT_PASS / blocked-paywall-captcha / sample extracts / URL can review.

## [2026-07-01 15:40] - [Codex]

### Da lam
- Chay live Phase 0 validation xong va lay report that trong `tech/reports/source_validation.json` / `.md`.
- Chay live crawl Tech xong sau khi bootstrap profile DB tu `tech/crawl.py`; output da co `news_output_today.json`, `news_output_all.json`, `news_for_ai.json`, `news_for_ai_clean.json`.
- Thu GDELT dry-run va xac nhan bi chan boi thieu ADC/credentials BigQuery trong runtime hien tai.
- Chay publication smoke voi crawl that + GDELT empty placeholder de kiem tra builder/validator, sau do chay publication ra artifact thuc `tech/data/publication.json` va `tech/web/publication.json`.
- Fix publication builder de overview khong lap domain va validate pass.

### Quyet dinh quan trong
- Khong gia mao GDELT: runtime hien tai khong co ADC hop le nen GDELT live van blocked.
- Publication dang co crawl stories that, GDELT event_count = 0, nen co the dung nhu artifact tam cho website/validation.

### File da thay doi
- `scripts/build_tech_publication.py`
- `tech/crawl.py`
- `tech/data/publication.json`
- `tech/web/publication.json`
- `HANDOFF.md`
- `.ai/CURSOR_WORKLOG.md`

### Verify / Test
- `.\.venv\Scripts\python.exe tech\validate_sources.py --force-refresh` -> pass
- `.\.venv\Scripts\python.exe tech\crawl.py` -> pass
- `.\.venv\Scripts\python.exe tech\gdelt.py --dry-run` -> fail do `DefaultCredentialsError` (missing ADC)
- `.\.venv\Scripts\python.exe tech\publication.py --gdelt-input <temp empty json>` -> pass
- `.\.venv\Scripts\python.exe tech\validate_publication.py` -> pass
- `.\.venv\Scripts\python.exe scripts\test_tech_pipeline.py` -> pass

### So lieu chot
- Catalog: 100
- Active: 7
- Disabled: 93
- Status counts: CAPTCHA 25, ARTICLE_EXTRACTION_FAILED 36, DEAD_URL 22, JS_ONLY 6, PASS_SITEMAP 5, PASS_RSS 2, SOFT_PASS 3, PAYWALL 1
- Article sample extracts thanh cong: 465 samples tu 93 sources
- Crawl output: 27 today / 76 all / 24 clean
- Publication: 24 stories / 0 GDELT events
- URL can Leon kiem tra lai: `https://techcrunch.com/category/artificial-intelligence/`, `https://www.theverge.com/ai-artificial-intelligence`, `https://arstechnica.com/ai/`, `https://www.wired.com/tag/artificial-intelligence/`, `https://www.technologyreview.com/topic/artificial-intelligence/`, `https://venturebeat.com/category/ai/`, `https://spectrum.ieee.org/artificial-intelligence`, `https://www.techrepublic.com/topic/artificial-intelligence/`

### Dang do / Viec tiep theo
- Co ADC BigQuery hop le thi chay lai `tech\gdelt.py` va regenerate publication de co GDELT thuc.
- Neu muon push, stage chi cac file Tech va worklog; bo qua scratch/unrelated changes o repo root.

## [2026-07-02 00:30] - [Codex]

### Da lam
- Review hep module Tech publication / validator / frontend / workflow ma khong sua Tin48h, Invest, World hay pages cu.
- Doi publication sang schema `tech-newsroom-72h-v1`, them `window_hours = 72`, va doi copy public sang huong 72 gio.
- Viet lai fallback publication de summary va `why_it_matters` la ban tom tat ngan gon bang tieng Viet kieu deterministic, khong cat 600 ky tu raw text.
- Xoa ngon ngu noi bo khoi text public: khong con nhac pipeline, crawler, GDELT, Gemini, BigQuery trong cac field hien thi.
- Cap nhat `/tech/` de fetch truc tiep `./data/publication.json`, doi heading thanh `Cong nghe & AI 72h`, va bo render `source_desk` theo dang story thô.
- Cap nhat `scripts/run_tech_gdelt.py` va `.github/workflows/tech-radar.yml` de workflow bat buoc dung `GCP_SA_JSON` + `GOOGLE_CLOUD_PROJECT`, ghi `estimated_bytes` / `processed_bytes`, va co the luu worklog khi GDELT chay that.

### Quyet dinh quan trong
- Khong noi long gate GDELT: local van chua co ADC hop le, nen khong duoc coi la DONE.
- Validator chi soi cac field public hien thi, khong soi `id` hay URL raw; tuy vay `link.title` van bi sanitize de tranh lo tu cam tren frontend.

### File da thay doi
- `scripts/tech_common.py`
- `scripts/build_tech_publication.py`
- `scripts/validate_tech_publication.py`
- `scripts/run_tech_gdelt.py`
- `scripts/test_tech_pipeline.py`
- `tech/index.html`
- `tech/update_worklog.py`
- `.github/workflows/tech-radar.yml`
- `tech/data/publication.json`
- `tech/web/publication.json`
- `HANDOFF.md`

### Verify / Test
- `.\.venv\Scripts\python.exe -m py_compile scripts\build_tech_publication.py scripts\validate_tech_publication.py scripts\run_tech_gdelt.py scripts\test_tech_pipeline.py tech\update_worklog.py tech\publication.py tech\validate_publication.py tech\test_pipeline.py` -> pass
- `.\.venv\Scripts\python.exe tech\publication.py --gdelt-input <temp empty 72h json>` -> pass
- `.\.venv\Scripts\python.exe tech\validate_publication.py` -> pass
- `.\.venv\Scripts\python.exe scripts\test_tech_pipeline.py` -> pass

### Trang thai hien tai
- `tech/data/publication.json` da la schema `tech-newsroom-72h-v1`
- `window_hours = 72`
- `gdelt_event_count = 0` trong publication local hien tai vi local chua chay GDELT that
- Workflow Tech da duoc cap nhat de fail ro rang neu thieu credential GCP

### Dang do / Viec tiep theo
- Can mot lan chay GDELT that bang secret/Actions de co `tech/data/gdelt_pulse.json` hop le voi `ran_successfully=true` va bytes that.
- Chua the danh dau DONE theo tieu chi cua user cho toi khi co GDELT run that va `/tech/` duoc xem lai tren Pages sau artifact moi.

## [2026-07-05 09:38] - [Codex]

### Da lam
- Day va chay that workflow Tech tren GitHub Actions thay vi local de dung secrets repo.
- Fix `.github/workflows/tech-radar.yml` de manual dispatch khong bi gate 72h chan, va chi ghi `key=value` hop le vao `$GITHUB_OUTPUT`.
- Fix workflow de truyen `GEMINI_API_KEY` va `GEMINI_MODEL` vao buoc publication; GitHub secret da duoc xac nhan hoat dong.
- Them log loi Gemini an toan trong `scripts/build_tech_publication.py` de thay ro curator success/fallback tren Actions.
- Fix quota Must Read de khong vuot ti le community 30%.
- Trigger Pages deploy thu cong sau khi workflow Tech commit artifact moi; `/tech/data/publication.json` public tra ve HTTP 200 voi schema 72h.

### Ket qua GitHub Actions
- Tech Radar run `28730744748` -> success.
- Deploy GitHub Pages run `28730812798` -> success.
- Artifact commit moi nhat tren `origin/main`: `9f64380 Update standalone tech radar artifacts.`
- GDELT dry-run log: `estimated_bytes=1043157439`.
- GDELT output: `ran_successfully=true`, `event_count=119`.
- Gemini curator log: `success=5`, `fallback=5`, `failed=0`.
- Validator: `OK: AI Frontier Radar 72h valid.`
- Test pipeline: `OK: AI Frontier Radar 72h tests passed`.

### So lieu artifact public
- `tech/data/publication.json`: `schema_version=ai-frontier-radar-72h-v1`, `window_hours=72`.
- Section items: 102, gom `full_link_radar=94`, `founder_ideas_for_leon=4`, `ai_knowledge=1`, va cac section chinh khac.
- `must_read=0` do quota chat luong hien tai khong cho lap bang nguon community/forum qua nhieu.
- Public smoke: `https://hugoleon1199.github.io/leonquant/tech/data/publication.json` -> HTTP 200, schema 72h.

### File da thay doi / commit
- `.github/workflows/tech-radar.yml`
- `scripts/build_tech_publication.py`
- `scripts/test_tech_pipeline.py`
- `tech/data/gdelt_pulse.json`
- `tech/data/publication.json`
- `tech/web/gdelt_pulse.json`
- `tech/web/publication.json`
- `.ai/CURSOR_WORKLOG.md`
- `HANDOFF.md`

### Dang do / Viec tiep theo
- Neu Leon muon Must Read luon co 10-20 bai, can them nguon official/independent active tot hon hoac noi quy tac community; hien tai builder dung dung nguyen tac "khong fill noi dung yeu".
- `tech/data/gdelt_pulse.json` ghi `estimated_bytes=0` / `processed_bytes=0` trong artifact du workflow dry-run log da co `1043157439`; can tinh rieng neu muon field bytes trong JSON phan anh dry-run/run job.

## [2026-07-05 10:29] - [Codex]

### Da lam
- Sua hep AI Frontier Radar 72h, khong sua Tin48h/Invest/World.
- P0.1: `pick_must_read()` khong con tra rong khi co main candidate; Must Read co san 5/10, domain cap 3, community fallback toi da 5 khi thieu non-community va gan `evidence=community-only`.
- P0.2: candidate Gemini fail co fallback tieng Viet, `curation_status=fallback`, importance fallback cap 3; item AI curated co `curation_status=ai`.
- P0.3: GDELT tech loc lai event bang signal AI manh, bo theme dump trong summary, them `raw_event_count`, `ai_filtered_event_count`, `rejected_non_ai_count`, `signal_keywords`, va bytes status dung.
- P1: them metadata main item `signal_type`, `confidence`, `evidence`, `time_to_apply`, `leon_fit`.
- Validator da fail neu Must Read rong khi co candidate, summary noi "0 bai dang doc", GDELT co theme dump/event thieu signal, hoac main item thieu metadata.

### Ket qua GitHub Actions
- Tech Radar run `28731893603` -> success.
- Artifact commit moi nhat tren `origin/main`: `5becf5c Update standalone tech radar artifacts.`
- GDELT dry-run estimated bytes: `1,057,267,222`.
- GDELT processed bytes: `1,057,267,222`.
- GDELT clean: raw `120`, ai_filtered `40`, rejected_non_ai `80`, theme_dump=false.
- Gemini curator: success `10`, fallback `0`, ai_main `7`, fallback_main `0`.
- Validator: `OK: AI Frontier Radar 72h valid.`
- Test pipeline: `OK: AI Frontier Radar 72h tests passed`.

### So lieu artifact public
- Schema: `ai-frontier-radar-72h-v1`; `window_hours=72`.
- Must Read: `6`; source domains: `4` (`discuss.huggingface.co`, `discuss.pytorch.org`, `forum.langchain.com`, `qbitai.com`).
- Must Read source type: community `5`, independent `1`.
- Must Read category: model `1`, local_ai `1`, tool `1`, opensource `1`, business `1`, agent `1`.
- Executive summary khong con "0 bai dang doc".
- Knowledge: `3` item, moi item co link; Founder Ideas: `6` item, moi item co `based_on`.
- Full Link Radar: `37`.

### File da thay doi / commit
- `.github/workflows/tech-radar.yml`
- `scripts/build_tech_publication.py`
- `scripts/run_tech_gdelt.py`
- `scripts/tech_common.py`
- `scripts/test_tech_pipeline.py`
- `scripts/validate_tech_publication.py`
- `tech/update_worklog.py`
- `.ai/CURSOR_WORKLOG.md` (cap nhat boi Actions)
- `tech/data/gdelt_pulse.json`, `tech/web/gdelt_pulse.json`, `tech/data/publication.json`, `tech/web/publication.json` (artifact boi Actions)

### Dang do / Viec tiep theo
- Source coverage van la `7 / 100`; Must Read dat nguong hien tai nhung con lech ve community vi active sources official/independent qua it.
- Neu muon giam community share ve <=30% trong thuc te, can chay Phase 0/source recovery them cho official/company, GitHub/Hugging Face, China AI va tool/automation sources.
