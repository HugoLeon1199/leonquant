# Cursor worklog — GDELT World Pulse (`leon.py`)

**Date:** 2026-05-24  
**Scope:** Event-centric SQL + 12-sector GKG + Vietnamese Gemini copy (no UI changes).

## Changes in `leon.py`

| Area | Detail |
|------|--------|
| SQL | `TopEvents` (300) from `events_partitioned` → `eventmentions_partitioned` by `GLOBALEVENTID` → `gkg_partitioned` on `SOURCEURL` only (sector/entities, not URLs) |
| Filters | 24h, `NumArticles >= 40`, `ABS(AvgTone) >= 4`, http URLs, social hosts excluded |
| Sectors | 12-group `CASE` on `V2Themes` (priority order: Y tế → Pháp lý → Năng lượng → … → Xã hội → Khác) |
| Sources | `SourceURLs` from EventMentions only; empty → fallback `[Link_Bai_Bao]`; `expand_event_sources()` no cross-event/sector expansion |
| Output fields | Kept `Doi_Tuong_Chinh`, `Nhom_Nganh`, `Diem_Cam_Xuc`, … + `GlobalEventID`, `Actor2Name`, `SourceURLs`, `source_count`, `V2Themes`, … |
| Gemini | JSON prompt (biên tập viên quốc tế); no AI/GDELT/crawler/pipeline in public `title`/`summary` |
| Sentiment | `tone <= -8` → Tiêu cực mạnh; `-8..-4` → Tiêu cực; `-4..4` → Trung tính; `4..8` → Tích cực; `>= 8` → Tích cực mạnh |
| Schema | `event-centric-v3` — URL pass-through từ EventMentions, không dedupe syndication |

**Not modified:** `landing_page.html`, navigation, footer, 48h digest (`content.json`, `leon_web_intel/`).

## Tests (2026-05-24)

```bash
python leon.py --dry-run   # ~0.3724 GB estimated (< 500 MB cap)
python leon.py             # 35 BQ rows → 20 hot events; wrote market_pulse.json + web/market_pulse.json
```

| Check | Result |
|-------|--------|
| `global_event_id` on each event | OK (20/20) |
| `sources` = string URLs per event | OK |
| Cross-event URL mix (e.g. Ukraine + Ebola) | OK — none found |
| Ebola → Y tế | OK |
| Crime/court/police → Pháp lý | OK |
| Oil/Ukraine infra → Năng lượng | OK (GKG oil/energy themes) |
| Public text mentions GDELT/AI/crawler | OK — 0 hits |

**BigQuery bytes processed (live):** 372,434,776 (~0.372 GB)

## How to run

```bash
pip install google-cloud-bigquery pandas google-generativeai requests beautifulsoup4
# .env: GEMINI_API_KEY, GOOGLE_APPLICATION_CREDENTIALS
python leon.py --dry-run
python leon.py
# Skip Gemini: python leon.py --no-gemini
```

Output: `market_pulse.json`, mirrored to `web/market_pulse.json`.

## 2026-06-03 — World LIVE deepen prompt (`gemini_world_deepen_events`)

- **File:** `leon.py` (~L1523), function `gemini_world_deepen_events()` only.
- **Change:** Replaced Gemini deepen prompt — professional tone, no system/AI/GDELT leakage, no invented macro/market impact when sources omit it.
- **Unchanged:** Scrape/deep-read logic, batch parsing, summary length targets (5–20 câu / 100–500 từ in prompt; no code clamp).
- **Verify:** `python leon.py --channel world` → `market_pulse.json`; grep forbidden phrases (hệ thống, GDELT, thuật toán, AI tổng hợp).

## 2026-06-03 — World curate: any sector if true global/regional impact

- **`gemini_world_dedupe_and_curate` prompt:** No hard ban on sports/entertainment; keep World Cup–scale events; still drop local crime/scandal (e.g. sexual assault arrest). Gemini classifies from title/summary.

## 2026-06-03 — World curate: include positive global-impact stories

- Curate prompt: positive/neutral developments (deals, ceasefire, recovery) equal weight; do not bias toward conflict-only feed; brief includes `sentiment_label` for Gemini.

## 2026-05-24 — Invest GDELT filter: English regex + `market_relevance_score`

| Area | Detail |
|------|--------|
| `leon.py` | Replaced flat `INVEST_ECONOMY_KEYWORDS` (incl. Vietnamese) with `INVEST_GDELT_REGEX` dict; `filter_invest_keyword_candidates()` uses `invest_market_relevance_score() >= 2` |
| `sql/gdelt_invest_pulse.sql` | Aligned signal regex (word boundaries for FED/OIL/BOND/AI); added `market_relevance_score`; `WHERE market_relevance_score >= 2` (not `primary_sector != 'Khác'`); `affected_assets` only from commodity flags + theme |
| Note | Vietnamese reserved for editorial layer only — not in GDELT/BQ filter |

**Verify:**

```bash
python -c "from leon import filter_invest_keyword_candidates, invest_market_relevance_score, _invest_signal_flags, _invest_text_blob; ev={'title':'Fed raises rates','gkg_organizations':''}; b=_invest_text_blob(ev); f=_invest_signal_flags(b); print(invest_market_relevance_score(f,b))"
python leon.py --channel invest --dry-run
python scripts/build_invest_world_from_pulse.py --no-gemini
```

## 2026-06-03 — Invest channel only (isolated from world LIVE)

**Scope:** `--channel invest`, `INVEST_*`, `filter_invest_keyword_candidates`, `invest_market_relevance_score`, `gemini_invest_semantic_judge`, `gemini_invest_world_topics`, `sql/gdelt_invest_pulse.sql`, `invest_pulse.json` / `invest_world_pulse.json`. **Not modified:** world `GDELT_MACRO_QUERY`, world dedupe prompts, Vietnam 48h, `landing_page.html`, invest hooks removed from `main()` world branch.

| Area | Detail |
|------|--------|
| SQL | Core `NumArticles>=40` + `|AvgTone|>=4`; supplement `NumArticles>=70` (neutral tone OK); dedupe; `LIMIT 120` TopEvents → mentions by `GLOBALEVENTID` → GKG on `SOURCEURL` only; `market_relevance_score >= 2`; 24h only |
| `leon.py` | `run_invest_channel_pipeline` / `run_invest_pipeline_from_events`; semantic judge max 60 **before** enrich; `export_invest_desk_payload` → `invest_pulse.json` + `web/invest_world_pulse.json`; `INVEST_MAX_BYTES_BILLED=600M`; public `_sanitize_invest_public_text` strips GDELT/keyword/AI/crawler/pipeline |
| World | No second invest BQ merge / `export_invest_world_pulse` on `--channel world` |

**Verify (2026-06-03):**

```bash
python -m py_compile leon.py
python leon.py --channel invest --dry-run   # ~0.5395 GB estimated
python leon.py --channel invest           # 105 BQ rows → 105 candidates → 5 topics / 10 items
```

| Metric | Result |
|--------|--------|
| Dry-run bytes | ~539,500,000 bytes (~0.5395 GB) |
| BQ rows in | 105 |
| Keyword candidates | 105 (min score 1; SQL already `>= 2`) |
| Export items | 10 across 5 topics (EQUITY, COMMODITY, BANKS, TRADE, TECH) |
| Live bytes processed | ~540,016,640 (~0.539 GB) |

**Outputs:** `invest_pulse.json`, `invest_world_pulse.json`, `web/invest_pulse.json`, `web/invest_world_pulse.json`.

## 2026-06-03 — Invest tone pools (single-scan SQL)

**Scope:** invest only. **Not modified:** world LIVE SQL/prompts, Vietnam 48h, `landing_page.html`.

| Change | Detail |
|--------|--------|
| SQL | Gộp 2 CTE scan → `CandidateBaseEvents` (1× `events_partitioned` 24h): `core_extreme` (40+ & \|tone\|≥4), `high_coverage_neutral` (70+), `market_entity_neutral` (30+ + Actor/URL watchlist); pool cap 70/60/60; `TopEvents LIMIT 160`; final `LIMIT 160`; `market_relevance_score >= 2` giữ nguyên |
| Tone | `ABS(AvgTone)>=4` chỉ cho pool A + ranking; không còn hard gate toàn cục |
| `leon.py` | `sentiment_label_from_tone()` cho invest; `_invest_sort_key` +tone rank; Gemini judge/topics/enrich: strategic tech + generic actor context; `feed_label` public wording |
| Watchlist | Tesla/Bitcoin/Nvidia… chỉ boost SQL pool C, không auto-keep — Gemini/Python quyết định cuối |

**Verify (2026-06-03):**

```bash
python -m py_compile leon.py
python leon.py --channel invest --dry-run   # ~0.5568 GB (+~3% vs 0.5395)
python leon.py --channel invest           # 132 BQ → 132 candidates → judge 11 → 4 topics / 5 items
```

| Metric | Result |
|--------|--------|
| Dry-run bytes | ~556,800,000 bytes (~0.5568 GB) |
| BQ rows in | 132 (was 105) |
| Python candidates | 132 |
| After semantic judge | 11 (pool 60) |
| Export | 4 topics, 5 items |
| Live bytes | ~0.557 GB |

## 2026-06-04 — Invest recall-first: soft noise_hint, Gemini precision gate

**Scope:** invest only (`leon.py`, `sql/gdelt_invest_pulse.sql`). **Not modified:** world/live, Vietnam 48h, UI, world/live prompts.

| Principle | Implementation |
|-----------|----------------|
| SQL recall-oriented | 24h pools unchanged; `TopEvents LIMIT 180`, pool caps 75/65/65, final `LIMIT 200`, `market_relevance_score >= 2` only |
| Python = cheap layer | `prepare_invest_candidates()`: dedupe, drop social/invalid URLs only, `noise_hint` soft flags, sort, cap 220 — no editorial score/geo reject |
| Gemini = editor | `gemini_invest_semantic_judge`: up to 100 in → `judgments[].keep` + `investment_angle`; max 28 kept; strict anti-filler prompt |
| Topics export | `gemini_invest_world_topics`: no generic brief/summary; max 8×2 items; `_topic_item_from_event` adds `investment_angle`, `affected_assets`, `sentiment_label`, `source_count` |
| Anti-filler enrich | Invest scrape/batch fallback: no "Sự kiện thuộc nhóm…" / "Nhấp nguồn…" templates |

**Targets:** BQ in ~120–220 · judge input ≤100 · judged ~10–28 · export ~8–16 items if quality allows.

**Verify:**

```bash
python -m py_compile leon.py
python leon.py --channel invest --dry-run
python leon.py --channel invest
```

Log fields: `bq_bytes_billed`, `bq_rows`, `candidates`, `judge_input`, `judged`, `topics`, `items` (+ stats in JSON export).

## 2026-06-04 — Invest Gemini topics: editorial labels + full item fields

**Scope:** `gemini_invest_world_topics`, merge/sanitize, `_gemini_curate_invest_ids`, `gemini_invest_dedupe_and_curate`, minimal `landing_page.html` render (invest tab only).

| Change | Detail |
|--------|--------|
| Topics prompt | Vietnamese editorial topic names; required `investment_angle`, `affected_assets`, `sentiment_label`; anti-filler brief |
| Merge | `_merge_invest_topic_item()` preserves all public fields; skip items without `investment_angle` |
| Topic names | `_normalize_invest_topic_display_name()` maps MACRO/TRADE/… → Vietnamese labels |
| Public label | `feed_label` from JSON; UI sub-line no longer hardcodes GDELT |
| Frontend | `buildInvestWorldHtml` shows angle, assets, sentiment, source_count |

## 2026-06-04 — Invest editorial tighten (subtitle, topics, assets, source_count)

**Scope:** invest content/editorial only (`leon.py`, minimal `landing_page.html` feed fallback).

| Fix | Detail |
|-----|--------|
| Subtitle | Cách A: `INVEST_PUBLIC_FEED_LABEL` = `các diễn biến kinh tế - thị trường đáng chú ý`; UI prefix unchanged |
| Topics | `INVEST_EDITORIAL_TOPICS` whitelist; prompt + `_coerce_invest_editorial_topic` / `_invest_guess_editorial_topic` (Iran → địa chính trị, not China) |
| Assets | Prompt grounding rules; no over-specific ETF/Brent/Nasdaq without source support |
| Confidence | `confidence` high/medium/low on items; cautious wording when low `source_count` |
| source_count | `display_source_count = max(source_count, unique_domains(source_urls))`; URL dedupe by domain |
| Fallback | `_fallback_invest_topics` uses editorial guess across all allowed topics |

## 2026-06-04 — Invest editorial v2: source quality, EU fiscal topic, cautious copy

**Scope:** `leon.py` invest Gemini/output only.

| Fix | Detail |
|-----|--------|
| Topics | Added `Chính sách tài khóa & Kinh tế châu Âu`, `Thương mại & Kiểm soát xuất khẩu`; Germany fiscal/health → EU topic not banks |
| Sources | `_invest_prioritize_source_urls` (premium first, iHeart/PR deprioritized); `source_count` = unique canonical domains |
| Prompt | Source-quality tier rules, grounding for angle/assets, confidence high/medium/low, style examples |
| Post-process | `_invest_temper_editorial_text` + `_coerce_invest_editorial_topic` overrides for mis-tags |

## 2026-06-04 — Digest 48h: adaptive editorial (no hard quotas)

**Scope:** `summarize_news_gemini.py`, `build_website_content.py`, `landing_page.html`, `scripts/embed_public_brief_into_html.mjs`. **Not touched:** invest world/VN, `leon.py`.

| Area | Change |
|------|--------|
| Philosophy | Số tin/sector **adaptive** theo chất lượng crawl — không fill, không cắt máy móc theo quota 6/7/12 |
| Soft hints | `DIGEST_SOFT_*` (8/15/8) — chỉ gợi ý trình bày trong prompt |
| Prompts | Tiêu chuẩn 3/5; `priority_tier` A/B/C; `summary_hint` + `reason_selected`; merge nhấn “không số lượng cố định”; overview 4–10 bullet; sector summary 80–250 từ; gom sub-cluster khi >15 tin |
| Post-merge | `normalize_digest_summary()` — sort tier/rank, dedupe bullets; parser cap 25/12 (không editorial cut) |
| Renderer | Hiển thị đủ items Gemini trả (không slice 7); ẩn sector code |
| Schema | Bỏ ép `needs_verification` / confidence bắt buộc; ưu tiên `priority_tier` |

**Regenerate:** `python summarize_news_gemini.py --mode digest` → `python build_website_content.py`.

## 2026-06-04 — Digest editorial style + normalize hygiene

| Area | Change |
|------|--------|
| Prompt | `_digest_editorial_style_block`, headline rewrite, sector routing, executive overview dedupe rules |
| Normalize | Semantic overview dedupe (`SequenceMatcher` + topic buckets); coerce `priority_tier`/`summary_hint`/`reason_selected` |
| Hygiene | Reroute AI policy→tech, exam→trends; drop soft entertainment; max 2× E10 toàn bài |
| Notable | `supplement_notable_from_sectors()` fallback 5–8 từ tier A/B khi merge trả <4 |

## 2026-06-04 — Public site rebuild (content.json + embedded HTML)

**Scope:** `build_website_content.py`, `landing_page.html`, `scripts/rebuild_public_site.ps1`, deploy `pages.yml`.

| Check | Result |
|-------|--------|
| Commands | `finalize_digest_summary` → `build_website_content.py --skip-images` → `embed_public_brief_into_html.mjs` (+ pulse/invest VN embed) |
| `content.json` | `briefMode=multisector-digest`, **4** `digestSectors`, **28** sub-topic `items`, `generatedAt` set; **~3 MB** (kèm `articleLinkIndex` 1725 bài) |
| Render chính | **Dual:** HTML nhúng sẵn (`data-embedded-brief="1"` trên `#brief`) + fetch `content.json` khi JS chạy; CI `pages.yml` embed lại vào `_site/index.html` |
| `?view=live` | Static Pages — cùng `index.html`; LIVE dùng `#pulse` + `data-embedded-pulse="1"`; ưu tiên embed trước khi fetch `market_pulse.json` (tránh trống khi JSON 503) |
| `?view=invest` | `#invest` + `data-embedded-invest-vn` trong repo; fetch `invest_world_pulse.json` / `invest_vn_brief.json` |
| Live 502/503 | `leonquant.com` fetch: digest HTML OK; `market_pulse.json` đôi khi **503** — nhúng pulse vào HTML giảm phụ thuộc fetch |
| Fake URLs | Không còn `coindesk.com/bitcoin-price-drop` / `cnbc.com/ai-stocks-rally` trong digest links sau finalize |
| Alphabet hint | `summaryHint` AI capex + `reasonSelected` hạ tầng AI (không VN-Index) |

**Local rebuild:** `powershell scripts/rebuild_public_site.ps1` — commit `landing_page.html`, `content.json`, `gemini_digest_summary.json`, push → Pages workflow.

## 2026-05-24 — Newsroom UI/copy polish (source match + Việt hóa)

**Scope:** `landing_page.html`, `scripts/newsroom_*`, `summarize_news_gemini.py` sanitize path, `build_website_content.py`, `embed_public_brief_into_html.mjs`, `pages.yml` — không đổi crawler/SQL/GDELT/invest-live.

| Area | Change |
|------|--------|
| Source match | `scripts/newsroom_source_match.py` — topic guards (crypto/AI, TP.HCM vs Cần Thơ); không fallback URL theo headline; ẩn link nếu không khớp |
| Copy | `scripts/newsroom_copy.py` — `soften_newsroom_text`, `soften_editor_note`; headline crypto ví dụ user |
| Publish sanitize | `scripts/sanitize_newsroom_content_json.py` — CI + local re-filter `content.json` links/titles trước embed |
| UI | Labels Việt: Bản tin 48h, Điểm nóng, Hồ sơ chính, Theo dõi tiếp, Nguồn đại diện, Bài quét; nav Tin 48h / Kinh tế đầu tư / Thế giới LIVE; bỏ tagline EN |
| Source UX | `story-source-line` gọn; Source Desk `<details>` collapsed; anchor = tiêu đề bài/domain |
| Test | `scripts/test_newsroom_digest.py` — match reject + soften editor |
| Verify | `python scripts/sanitize_newsroom_content_json.py content.json` → `node scripts/embed_public_brief_into_html.mjs landing_page.html content.json` |

**Known:** Front page #02/#03 có thể không có link nếu crawl không có bài khớp chặt (đúng yêu cầu — không gắn sai).

## 2026-06-05 — Tin 48h newsroom brief (schema + renderer)

**Scope:** `summarize_news_gemini.py`, `build_website_content.py`, `landing_page.html`, `validate_content.py`, `scripts/embed_public_brief_into_html.mjs`, `scripts/test_newsroom_digest.py`, `pages.yml`.

| Area | Change |
|------|--------|
| Gemini merge | Output `newsroom-brief-v1`: `editor_note`, `front_page`, `sector_deep_briefs` + `story_dossiers`, `watchlist_24_72h`, `source_desk` |
| Normalize | `normalize_newsroom_brief`, `validate_newsroom_brief`, URL whitelist trên dossier/front/desk |
| Web | `briefMode=newsroom-brief`, `build_newsroom_web_extras` → `content.json` |
| UI | Renderer tạm: Lời biên tập, Front page, Sector deep + dossier cards, Watchlist, Source desk (không redesign lớn) |
| Legacy | `multisector-digest` vẫn hiển thị nếu `content.json` cũ |
| Test | `python scripts/test_newsroom_digest.py` (không gọi Gemini) |

**Deploy:** Lần digest CI/API tiếp theo tạo JSON newsroom; rebuild Pages để embed HTML mới.

## 2026-06-04 — HTTPS leonquant.com (`NET::ERR_CERT_COMMON_NAME_INVALID`)

**Root cause:** TLS trên `leonquant.com` trả cert `CN=*.github.io` (SAN không có `leonquant.com`) — custom domain chưa đăng ký trên GitHub Pages dù DNS apex/www trỏ đúng IP GitHub.

**Fix (repo):** `pages.yml` — bước `PUT /repos/.../pages` với `cname=leonquant.com`, `https_enforced=true`, `build_type=workflow`; log `https_certificate.state`. README mục *Custom domain* (DNS + Settings + Cloudflare).

**Sau push:** chạy workflow *Deploy GitHub Pages*; đợi `cert_state=approved` rồi thử lại https://leonquant.com.

## 2026-06-04 — Digest polish v4 — URL whitelist + recompute hint after rewrite/dedupe

**Scope:** `summarize_news_gemini.py` only (48h digest normalize).

| Area | Change |
|------|--------|
| URL whitelist | `DigestUrlIndex` từ `news_for_ai_clean.json` / enriched payload; `_sanitize_sub_topic_urls` / `_sanitize_notable_url` sau merge |
| Fabricated URLs | Không trong `allowed_urls` → match domain+headline hoặc drop + `WARN digest URL` |
| Copy | `_recompute_digest_subtopic_copy` sau Việt hóa headline, dedupe, merge cluster — không giữ hint/reason stream khác |
| Alphabet | `_infer_alphabet_digest_copy` — hint/reason AI capex, không VN-Index |
| Bitcoin finance | `_merge_bitcoin_finance_rows` — gom BTC+AI vs BTC 70k khi trùng góc |
| Pipeline | `finalize_digest_summary(..., input_articles=)`; `validate_digest_url_whitelist` |

**Regenerate:** `python summarize_news_gemini.py --mode digest` → `python build_website_content.py`.

## 2026-06-04 — Digest polish v3 (hint fallback, headline dedupe, low-value filter)

| Area | Change |
|------|--------|
| summary_hint | Sector fallback câu đủ (không `headline[:80]`); `_infer_tech_summary_hint` theo từng luồng AI |
| Dedupe | `_dedupe_sub_topics_by_headline` sau Việt hóa — merge URL tối đa 3 |
| Filter | `_is_low_value_digest_item` (IMF calendar archive, metadata) |

## 2026-06-04 — Digest 48h polish v2 (generic ban + VI headline + Iran/E10 cluster)

| Area | Change |
|------|--------|
| Generic | Mở rộng `_GENERIC_COPY_FRAGMENTS`; `_ensure_specific_digest_copy` + `validate_digest_public_polish` |
| Headline | Template Alphabet/Trump/Qeshm; `_english_headline_vietnamese_stub` thay fallback EN thô |
| Cluster | Iran 2 cụm (Qeshm / Tehran); E10 global `_consolidate_e10_globally` (policy + consumer) |
| Validation | `_enforce_digest_public_polish` cuối `normalize_digest_summary` |

## 2026-06-04 — Digest 48h content polish (normalize)

| Area | Change |
|------|--------|
| Copy | Cấm generic `summary_hint`/`reason_selected`; `_infer_*` theo luồng/headline; WARN nếu còn generic |
| Headline | `_vietnamese_public_headline` + template EN→VI; validation cảnh báo headline còn tiếng Anh |
| Cluster | Gom Mỹ-Iran (2 cụm), E10 trong sector; routing Blue Origin/NASA → `tech` |
| Prompt | `_digest_content_polish_block()` — sub-cluster, tiếng Việt, copy cụ thể |

## 2026-06-04 — Digest adaptive: coverage sanity + source metadata

| Area | Change |
|------|--------|
| Coverage | `_digest_coverage_sanity_block()` in merge — giữ đủ luồng A/B, không co 1–3 tin khi partials giàu; sanity <4 sub_topics warns only |
| Payload | `compact_for_gemini(digest)` gửi `source`, `published_at`, `category`, `region` |
| URLs | Prompt `source_urls` 1–3; `build_website_content` render tối đa 3 link/sub_topic |
| Sub-cluster | `_digest_subcluster_block()` + merge anti-compression wording |

## 2026-06-04 — Newsroom publication UI (`landing_page.html`)

| Area | Detail |
|------|--------|
| Scope | UI only: `landing_page.html` (CSS + JS), `assets/`, `.github/workflows/pages.yml`, `scripts/newsroom_brief_render.mjs`, `scripts/embed_public_brief_into_html.mjs` |
| Layout | Issue Header (48H BRIEF + stat pills), TOC chips (sticky desktop), editor note card, front page lead/secondary/compact, sector icons + thesis card, structured dossier blocks, watchlist panel, collapsible Source Desk (`<details>`) |
| Brand | `assets/leonquant-icon.svg`, `assets/favicon.svg` (SVG in `<head>`); fallback `LQ` mark on `img` error |
| Brief modes | `newsroom-brief` → publication layout; `multisector-digest` → legacy layout unchanged |
| Deploy | `pages.yml` copies `assets/` → `_site/assets/` |
| Tests | `python scripts/test_newsroom_digest.py`; `powershell scripts/rebuild_public_site.ps1` (embed OK) |
| Responsive | Checked CSS breakpoints ~390px / 768px / 1280px (compact padding, horizontal TOC scroll, no overflow-x on `.newsroom-report`) |
| Not changed | Crawler, Gemini pipeline, SQL/GDELT, invest/live logic |

## 2026-06-05 — Tin48h newsroom: executive briefing + ngành con

| Area | Detail |
|------|--------|
| Gemini schema/prompt | `summarize_news_gemini.py`: mở rộng `newsroom-brief-v1` với `executive_briefing`, `subsector_briefs`, `sub_sector`; prompt newsroom nhấn mạnh Gemini quyết định most-mentioned/hottest/emerging/subsector, Python chỉ hygiene |
| Normalize | Thêm sanitize `executive_briefing`, sanitize `subsector_briefs`, preserve `sub_sector` trong dossier; merge/dedupe `subsector_briefs` theo sector code; giữ 4 sector top-level |
| Validate | Thêm warnings cho thiếu/ngắn/generic `executive_briefing.content`, subsector thiếu source khi claim dài, dossier thiếu `representative_sources` |
| Build mapping | `build_website_content.py`: map snake→camel cho frontend (`executiveBriefing`, `subsectorBriefs`, `subSector`) và giữ fields cũ |
| Renderer | `scripts/newsroom_brief_render.mjs` + `landing_page.html` inline JS/CSS: thêm section “Tổng quan 48h”, TOC chip, card tín hiệu, block “Phân ngành nổi bật”, chip `subSector` ở dossier, reading time tính cả executive/subsector |
| Guardrails | Không thêm hard-code phân ngành con bằng regex để thay Gemini; URL public vẫn đi qua sanitize whitelist |
| Test ran | `python -m py_compile summarize_news_gemini.py build_website_content.py`; `python scripts/test_newsroom_digest.py`; `python build_website_content.py --skip-images --skip-notable-images`; `node scripts/embed_public_brief_into_html.mjs landing_page.html content.json` |
| Runtime limit | `python summarize_news_gemini.py --mode digest` bị Gemini HTTP 429 (rate limit) nên dừng run; build local dùng payload sẵn có, vì vậy `executive_briefing.content` đang bị warn trống ở sample hiện tại |

## 2026-06-05 — Tin48h Gemini prompts: briefing prose + anti rule-leak

| Area | Detail |
|------|--------|
| Scope | **Prompt only** (+ minimal excerpt passthrough in sanitize); không đổi layout/UI/crawler/GDELT/live/invest |
| `summarize_news_gemini.py` | Thêm blocks: `_digest_executive_briefing_writing_block`, `_digest_sector_narrative_block`, `_digest_anti_rule_leak_block`, `_digest_source_excerpt_rules_block`, `_digest_newsroom_prose_example_block` (mẫu văn user) |
| Tổng quan 48h | `executive_briefing.sections` = đoạn văn briefing (gợi ý 500–10.000 chữ); cấm outline nhãn + 1 câu |
| Từng ngành | `sector_thesis` = bài 4+ đoạn có mạch (mở → tin liên kết → tác động); cấm chuỗi headline/dossier rời |
| Anti leak | Cấm cụm rule/prompt (“chỉ nên xuất hiện”, “theo rule”, …); validate warn nếu `sector_thesis` lộ rule |
| Nguồn | Schema `representative_sources[].excerpt` 2–9 câu; `newsroom_source_match.sanitize_representative_sources` giữ `excerpt` |
| Merge prompt | Gắn mẫu văn + `editor_note` để trống; minimum executive ≥500 chữ khi pools ≥80 |
| Tests | `python scripts/test_newsroom_digest.py` — thêm `test_merge_prompt_briefing_quality_guidance`, `test_sanitize_preserves_source_excerpt` |
| Apply | Chạy `--merge-only` (hoặc full digest loop) để Gemini sinh bản mới theo prompt |

## 2026-06-06 — Invest channel: longer summaries (prompt + deepen)

**Scope:** `leon.py`, `scripts/build_invest_vn_brief.py` — không đổi UI/crawler SQL.

| Vấn đề | Nguyên nhân | Fix |
|--------|-------------|-----|
| Tin thế giới invest quá ngắn vs LIVE | Invest enrich yêu cầu 1-2 câu; topics prompt 2-4 câu; cắt 320-360 ký tự | Enrich 4-8 câu; topics 5-10 câu (120-320 từ); cap 1200 ký tự |
| Thiếu chi tiết từ nguồn | Invest không chạy deep-read như LIVE | Thêm `gemini_invest_deepen_events()` sau enrich (120-400 từ) |
| Topics rút gọn lại | Gemini topics ghi đè summary ngắn | `_invest_pick_public_summary()` giữ bản dài hơn từ deepen |
| VN invest brief | Prompt lead/theme hơi cạn | Lead 3-5 câu; why_hot 2-3; developments 4-8; lens 2-3 |

**Regenerate:** `python leon.py --channel invest` → rebuild `invest_world_pulse.json`; CI `build_invest_vn_brief.py` cho block VN.

## 2026-06-06 — Invest: không giới hạn câu/từ/ký tự (full Gemini output)

**Scope:** `leon.py`, `scripts/build_invest_vn_brief.py`, `landing_page.html` (bỏ line-clamp lens).

| Layer | Thay đổi |
|-------|----------|
| `leon.py` enrich/deepen/topics | Prompt: tóm tắt đầy đủ, không cap; topics không viết lại summary; `_invest_resolve_public_summary()` ưu tiên deepen; `_clamp_invest_brief(max_len=None)` |
| Deep-read block | `_deepen_event_block`: truyền full summary vào prompt (bỏ `[:500]`) |
| `build_invest_vn_brief.py` | Bỏ `_clip` trên lead/why_hot/developments/lens/issue; input pack không cắt digest; prompt không giới hạn câu/từ |
| UI | `.invest-vn-lens`: bỏ `-webkit-line-clamp: 2` |

**Regenerate:** `python leon.py --channel invest` + `python scripts/build_invest_vn_brief.py` để JSON mới có bài dài hơn.

## 2026-06-06 — Tab navigation polish (segmented nav + LIVE filters)

**Scope:** `landing_page.html` + `.ai/CURSOR_WORKLOG.md` only. **Not modified:** crawler, Gemini, content JSON, layout lớn ngoài header nav.

| Mục | Chi tiết |
|-----|----------|
| Segmented nav | `.nav-segment` + `.nav-tab` thay pill `.nav-hub`; labels: Bản tin 48h / Kinh tế đầu tư / Thế giới LIVE |
| Active màu vai trò | Digest: slate/cyan nhẹ; Invest: gold/amber; LIVE: cyan/blue + dot đỏ chỉ trên badge khi active |
| Active state | Background nhẹ, border, accent line `::after`; hover/focus transition ~18ms; không gradient game-like |
| Mobile | Sticky hero nav (≤640px); label rút: Tin48h / Đầu tư / LIVE ●; touch min 44px; scroll ngang mượt |
| LIVE filter chips | Filter thật client-side: Tất cả, Đa nguồn, Một nguồn, Kinh tế, Công nghệ, Địa chính trị (theo `source_count` + `sector`) |
| Typography | Be Vietnam Pro; nav `.82–.85rem`; active 700 / inactive 600 |

**Verify:** Desktop 1280px + mobile 390px — không overflow ngang; tab active rõ; LIVE dot chỉ pulse khi tab LIVE active.

## 2026-06-06 — UI review cuối 3 tab (nav + spacing + LIVE motion)

**Scope:** `landing_page.html` + rebuild embed từ `content.json` / `market_pulse.json` / `invest_vn_brief.json`. **Not modified:** crawler, Gemini prompts, nội dung JSON.

| Tab | Review / fix |
|-----|----------------|
| **Tin48h** | Embed đã đúng layout newsroom: Bản tin 48h → Tổng quan 48h → Đi sâu theo từng ngành → Tin đáng chú ý; không TOC/stat pill/Lời biên tập |
| **Kinh tế đầu tư** | Line-height 1.76–1.78; mobile spacing 36–40px → 28–32px; link nguồn min-height 44px |
| **Thế giới LIVE** | Tắt ticker/LIVE blink animation trên mobile; badge sector max-width; multi/solo contrast giữ nguyên |
| **Nav** | Segmented control (commit trước); `overflow-x: clip` tránh scroll ngang |

**Rebuild:** `node scripts/embed_public_brief_into_html.mjs landing_page.html content.json` (+ pulse/invest VN nếu có JSON).

## 2026-06-06 — Fix giờ đăng link (publishedAt từ DuckDB extracted_at)

**Nguyên nhân:** `news_for_ai_clean.json` chỉ có ngày (`2026-05-23`); `_enrich_articles_from_intel_db` bỏ qua vì coi là “đã có published_at” → web hiển thị giờ cũ/sai (00:07 +7).

**Fix:** `build_website_content.py` — enrich cả link thiếu giờ; dùng `extracted_at` từ DuckDB; `_link_published_at()` cho sector links. JS `enrichLinkPublishedAt` nâng date-only lên ISO có giờ. Rebuild `content.json` + embed HTML.

## 2026-06-06 — Tin48h Gemini prompt: adaptive length + entity clarity (`summarize_news_gemini.py`)

**Scope:** Prompt-only patch for Tin48h digest (`summarize_news_gemini.py`). **No** UI/layout, tabs/navigation, crawler, invest/live/VN logic, or JSON schema changes.

| Change | Detail |
|--------|--------|
| Adaptive length | Replaced hard hints (500–10.000 chữ, 2–9 câu, 100–500 từ, 3–5+ ý, ≥500 chữ merge) with editorial adaptive wording — deeper for hot stories, concise for minor ones; no sentence/word quotas |
| Entity clarity | New block: first-mention rules for people, orgs, indices, abbreviations, events, big tech, tickers; bad/good examples (Trump, FPT, World Cup, Fed) |
| Who–What–Why | Each important paragraph must clarify subject, event, and why it matters |
| Natural writing | Full context on first mention only; avoid glossary tone and parenthesis overload |
| Unchanged | No hallucination, fake URLs, generic copy, topic repetition, AI/prompt leakage; Gemini = editor, Python = hygiene/render |

**Verify:** `python -m py_compile summarize_news_gemini.py` · `python scripts/test_newsroom_digest.py`

## 2026-06-06 — Tin48h main editorial quality (prompt + Python hygiene)

**Scope:** Tin48h prompt + main briefing content quality only. **No** tab/UI/navigation changes; archive link text and full `articleLinkIndex` archive unchanged.

| Area | Detail |
|------|--------|
| Prompt | Adaptive length (no word/sentence quotas); entity clarity + Who–What–Why; main 48h freshness; source quality rules; story-cluster dedupe guidance (Fed/Warsh, SpaceX, Iran) |
| Python | `scripts/newsroom_main_quality.py` — filter PAGE NOT FOUND/nan/category/spam URLs from main output; story-cluster dedupe on front page/dossiers/notable; freshness sort; wired in `normalize_newsroom_brief` + `build_website_content` notable/links |
| Archive | `articleLinkIndex` still lists all crawled articles; render string “Bản tin được tổng hợp từ … bài, bấm vào xem chi tiết” unchanged |
| Unchanged | Tabs, invest/live/VN, crawler, JSON schema shape, no hallucination / fake URL rules |

**Verify:** `python -m py_compile summarize_news_gemini.py build_website_content.py` · `python scripts/test_newsroom_digest.py`

## 2026-06-06 — Tin48h sector-depth prompt + rendering preservation

**Scope:** Sector-depth prompt + `build_newsroom_web_extras` data preservation only. **No** tabs/navigation, archive link label, invest/live, crawler, or page redesign.

| Area | Detail |
|------|--------|
| Prompt (`sector_thesis`) | No fixed word/sentence quotas; depth scales with hot-story density; required layers when data exists (thesis, main clusters, Who–What–Why, impact, watch 24–72h); synthesize-not-list; absorb all quality dossiers/subsectors; bad/good examples (shallow “điểm sáng thu hút vốn” vs deep AI infra narrative) |
| Validation | Warn on shallow/generic `sector_thesis`; missing concrete entities; `sector_thesis` not reflecting main dossier clusters when multiple rich dossiers exist |
| Render fix | `build_newsroom_web_extras()` was building `subsector_out` / `dossiers_out` then writing empty arrays — now **preserves** `subsectorBriefs` and `storyDossiers` in `content.json` (UI can stay compact; structured data no longer discarded) |
| Unchanged | Archive `articleLinkIndex` + label “Bản tin được tổng hợp từ … bài, bấm vào xem chi tiết”; tabs; invest/live; crawler |

**Verify:** `python -m py_compile summarize_news_gemini.py build_website_content.py` · `python scripts/test_newsroom_digest.py` · `python build_website_content.py --skip-images --skip-notable-images` · `node scripts/embed_public_brief_into_html.mjs landing_page.html content.json`

**Apply new prose:** re-run Gemini digest/merge — existing `gemini_digest_summary.json` still has short sector theses until regenerated.

## 2026-06-06 — CI digest commit fix (daily.yml)

**Issue:** `build-digest` Gemini/build succeeded but push failed — export updates tracked `news_for_ai.json` while commit step only staged `news_for_ai_clean.json`; dirty tree blocked `git pull --rebase` (hidden by `|| true`), then `git push` failed.

**Fix:** Stage `news_for_ai.json`; match `invest-world` pattern (exit 0 if no staged diff; rebase without swallowing errors). **No re-run triggered** in this patch.

## 2026-06-06 — Kinh tế đầu tư: presentation + editorial prompt

**Scope:** `landing_page.html` (invest tab CSS/JS only), `leon.py` (invest Gemini prompts), `scripts/build_invest_vn_brief.py`, `scripts/embed_public_invest_vn_into_html.mjs`, `.ai/CURSOR_WORKLOG.md`.

| Change | Detail |
|--------|--------|
| Quick index | Internal anchor chips: Đọc nhanh · Biến số toàn cầu · Việt Nam & thị trường trong nước · Đang theo dõi · Nguồn (not a new nav tab) |
| Quick read | Client-side strip “Đọc nhanh cho nhà đầu tư” from `worldData`/`vnData` only — global/VN highlights, assets, 24–72h watch |
| Hierarchy | Labeled memo fields (Sự kiện, Tác động, Tài sản, Độ phủ nguồn, Nguồn / Chủ đề, Diễn biến, Góc đầu tư…) |
| Wording | Display: “Biến số toàn cầu”, “Việt Nam & thị trường trong nước”, “Độ phủ nguồn” (nav tab label unchanged) |
| Colors | Amber/gold accent, slate text, cyan source links, subtle badges — no dashboard/crypto styling |
| Prompts | `INVEST_EDITORIAL_LENGTH_RULE` + entity clarity + Who/What/Why/Watch in invest enrich/deepen/topics/VN brief; removed “ĐÚNG 1 câu” on `investment_angle` |
| Unchanged | Tin48h tab, World LIVE, top nav tabs, archive, crawler, overall site redesign |

**Validation:** `python -m py_compile leon.py scripts/build_invest_vn_brief.py`; `node scripts/embed_public_invest_vn_into_html.mjs landing_page.html invest_vn_brief.json`

## 2026-06-06 — Kinh tế đầu tư: section numbering 01/02/03 + prompt (invest only)

**Scope:** `landing_page.html` (invest CSS/JS), `leon.py` (invest prompts), `scripts/build_invest_vn_brief.py`, `scripts/embed_public_invest_vn_into_html.mjs`, `.ai/CURSOR_WORKLOG.md`.

| Change | Detail |
|--------|--------|
| Numbering | Section headers **01 / 02 / 03** (was Roman I / II / III): Biến số toàn cầu · Việt Nam & thị trường trong nước · Đang theo dõi |
| Visual | Two-digit number subtle (tabular, muted); title prominent; amber/gold + slate + cyan links unchanged |
| Prompts | `INVEST_EDITORIAL_LENGTH_RULE` — no fixed sentence/word/character cap; entity clarity (Trump/FPT/Fed examples); judge prompts drop “một câu investment_angle” |
| No quick index | Confirmed — no chip TOC / anchor index added |
| No quick-read | Confirmed — no “Đọc nhanh cho nhà đầu tư” block added |
| Unchanged | Tin48h tab, World LIVE, top nav, Tin48h archive, crawler, data pipelines unrelated to invest |

**Validation:** `python -m py_compile leon.py scripts/build_invest_vn_brief.py` · `node scripts/embed_public_invest_vn_into_html.mjs landing_page.html invest_vn_brief.json`

## 2026-06-06 — Kinh tế đầu tư: now_watch under Vietnam section (structure only)

**Scope:** `landing_page.html` (invest VN renderer + CSS), `scripts/embed_public_invest_vn_into_html.mjs`, `.ai/CURSOR_WORKLOG.md`.

| Change | Detail |
|--------|--------|
| Structure | `now_watch` stays in JSON; rendered **inside** section **02 Việt Nam & thị trường trong nước** |
| Label | Subsection **“Theo dõi tiếp”** (no section number); removed standalone **03 Đang theo dõi** |
| Filter | Skip watch items without valid source link or with weak/stale content (>21d vs digest) |
| Main sections | **01** Biến số toàn cầu · **02** Việt Nam & thị trường trong nước only |
| No quick index / quick-read | Confirmed unchanged |
| Prompts | No sentence/word/character cap in invest prompts (unchanged this patch) |
| Unchanged | Tin48h tab, World LIVE, top nav, crawler, data generation outside invest |

**Validation:** `python -m py_compile leon.py scripts/build_invest_vn_brief.py` · `node scripts/embed_public_invest_vn_into_html.mjs landing_page.html invest_vn_brief.json`

## 2026-06-06 — Kinh tế đầu tư: Gemini prompt professionalism (invest only)

**Scope:** `leon.py` (invest editorial constants + all invest Gemini prompts), `scripts/build_invest_vn_brief.py`, `.ai/CURSOR_WORKLOG.md`.

| Change | Detail |
|--------|--------|
| Memo structure | Fact / Context / Transmission / Implication / Watch / Uncertainty — cover in prose, no mechanical labels |
| Specificity | Entity detail rule — expand vague phrases when source has names/agencies/numbers |
| Transmission | investment_angle / investor_lens must name impact channel when possible |
| Caution | Separate fact from implication; no buy/sell; cautious wording |
| Relevance | Do not force weak investment angles |
| Legal / market / policy | Domain-specific fields when source supports |
| Length | No fixed sentence/word/character cap — completeness by importance |
| Unchanged | Tin48h, World LIVE, UI/layout, nav, crawler, data schema |

**Validation:** `python -m py_compile leon.py scripts/build_invest_vn_brief.py`

## 2026-06-06 — Standalone news API quality tests (input eval only)

**Scope:** `api_tests/` — **not** integrated into web, Tin48h, invest, or LIVE pipeline.

| File | Purpose |
|------|---------|
| `api_tests/test_news_apis.py` | Fetch NewsData.io, GNews.io, WorldNews API; normalize schema; quality heuristics |
| `api_tests/README.md` | How to run + env vars |
| `api_tests/output/*` | Samples + `api_quality_report.md` / `.csv` (gitignored) |
| `.env.example` | Placeholders `NEWSDATA_API_KEY`, `GNEWS_API_KEY`, `WORLDNEWS_API_KEY` |

**Run:** `python api_tests/test_news_apis.py` from repo root (keys in `.env.example`; CI workflow `api-tests.yml`).

**Checks:** content length, truncation hints, 48h freshness, URL overlap vs `content.json`, cross-API duplicate URLs, quota/auth errors in report.

**Unchanged:** `content.json`, `landing_page.html`, crawl/Gemini digest, invest, LIVE.

**Validation:** `python -m py_compile api_tests/test_news_apis.py`

## 2026-06-06 — API cron 30m (1 request/run, accumulate URLs)

| File | Purpose |
|------|---------|
| `api_tests/cron_fetch.py` | Rotate worldnews → gnews → newsdata; 1 HTTP request/run |
| `api_tests/data/cron_accumulator.json` | Unique URLs + run log (tracked in git) |
| `api_tests/data/cron_summary.md` | Human-readable totals for daily check |
| `.github/workflows/api-cron-30m.yml` | Cron `*/30 * * * *` UTC, bot commit |

**Run:** `python api_tests/cron_fetch.py` · **Validation:** `python -m py_compile api_tests/cron_fetch.py`

## 2026-06-07 — Fix Tin48h link cũ (May / 21-day export)

**Nguyên nhân:** `news_for_ai_clean.json` còn cửa sổ **21 ngày** (1561 bài publish May) từ CI trước fix; `content.json` build từ export đó → link/ngày sai.

**Đã làm (local):**
- `prepare_digest_db.py`: purge 8541 bài publish ngoài today+yesterday; window rolling 48h (~479 fresh).
- Re-export `news_for_ai.json` / `news_for_ai_clean.json` → **456 bài**, window `recent_calendar_days: 2`, rolling 48h.
- `build_website_content.py`: luôn áp `filter_digest_fresh_articles` (kể cả thiếu `window.end_date`); bỏ URL Gemini ngoài pool 48h; backfill link front/dossier khi whitelist lọc hết URL cũ.
- Rebuild `content.json`: **456** `allArticles` / `articleLinkIndex`, **0** URL `/may/` hoặc `2026-05`, `publishedAt` trong 48h.

**Chưa:** Gemini digest vẫn summary cũ (source_urls May đã strip) — frontPage links có thể trống đến khi CI chạy lại Gemini trên export mới.

**Deploy:** push `news_for_ai*.json` + `content.json` + `data/digest_export_window.json` qua daily workflow.

## 2026-06-07 — Khôi phục link + nội dung Tin48h (sau lọc URL cũ)

**Lỗi:** Lọc URL May làm `representative_sources` rỗng → `enforce_newsroom_main_editorial_quality` xóa hết dossier; matcher headline không đọc `summary`; UI không render `frontPage` / `storyDossiers`.

**Fix:** Giữ dossier khi thiếu URL (gán link lại lúc build); `_score_headline_to_article` dùng summary; sector fallback links; render front page + dossier cards (`landing_page.html`, `newsroom_brief_render.mjs`).

**Kết quả local:** 21 dossier, 11+ link dossier, 6 link front, 8 link/sector, 456 archive links.

## 2026-07-01 - Standalone Tech & AI scaffold (Phase 0 gate + independent pipeline)

Scope: Them nhanh tech/ tach biet, khong sua logic/schema/output cua Tin 48h, invest, world LIVE.

- Phase 0 gate: config/tech_sources_catalog.txt + scripts/validate_tech_sources.py -> profile + discovery + sample extract + classify + sinh tech_sources_active.txt / tech_disabled_sources.txt / tech_tiers/** / report JSON+MD.
- Crawl tech: scripts/run_tech_intel_pipeline.py -> precheck validation report, DB rieng data/web_intel_tech.duckdb, output tech_news_output_today.json / tech_news_for_ai.json / tech_news_for_ai_clean.json.
- GDELT tech: sql/gdelt_tech_pulse.sql + scripts/run_tech_gdelt.py -> TopEvents truoc, EventMentions URL that, GKG sau TopEvents, dry-run, max bytes billed, retain output cu khi rong.
- Publication: scripts/build_tech_publication.py + scripts/validate_tech_publication.py -> schema tech-newsroom-v1, Python own grounding/count/freshness/dedupe.
- Web: tech/index.html standalone; landing_page.html chi them anchor /tech/; pages.yml append copy artifact tech.
- Workflows: .github/workflows/tech-radar.yml + .github/workflows/tech-profile-refresh.yml.
- Tests: scripts/test_tech_pipeline.py fixture/offline pass.

Validation status snapshot live:
- PASS: chua chay live
- SOFT_PASS: chua chay live
- blocked/paywall/captcha: chua chay live
- bai mau extract thanh cong: chua chay live
- URL can Leon kiem tra lai: se co sau khi chay scripts/validate_tech_sources.py

## 2026-07-01 - Validation live kick-off update

- Muc tieu: lay ket qua that cho Phase 0 truoc khi mo production tech.
- Moi truong: da bootstrap `pip` trong `.venv` va cai `leon_web_intel/requirements.txt` thanh cong.
- Lenh da chay: `.\.venv\Scripts\python.exe scripts\validate_tech_sources.py`
- Trang thai hien tai: run live van dang chay background voi PID `23308`; shell timeout nhung process chua dung.
- Report cuoi chua co: `reports/tech_source_validation.json`, `reports/tech_source_validation.md`, `config/tech_sources_active.txt`, `config/tech_disabled_sources.txt`, `config/tech_tiers/**`.
- PASS: chua chot
- SOFT_PASS: chua chot
- blocked/paywall/captcha: chua chot
- bai mau extract thanh cong: chua chot
- URL can Leon kiem tra lai: chua chot, doi report cuoi
- Luu y: khong commit `reports/tech_validation.duckdb*`; chi theo doi den khi run xong roi append ket qua that.
