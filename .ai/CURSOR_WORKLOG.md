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

## 2026-07-01 - Tech wrapper + 72h gate update

- Da them entrypoints `tech/validate_sources.py`, `tech/crawl.py`, `tech/gdelt.py`, `tech/publication.py`, `tech/validate_publication.py`, `tech/test_pipeline.py`.
- Da chuyen Tech artifact space sang `tech/config`, `tech/data`, `tech/reports`, `tech/web` qua `LEON_TECH_BASE_DIR`.
- Smoke live `tech/validate_sources.py --limit 1` pass; full `tech/validate_sources.py --force-refresh` dang chay background PID `46404` va chua flush full report.
- `tech/crawl.py` co 72h publish gate, `sql/gdelt_tech_pulse.sql` da len 72h, `tech/index.html` fetch `./data/publication.json`.
- `tech-radar.yml` va `tech-profile-refresh.yml` da chuyen sang entrypoints Tech moi.
- PASS: smoke validation / offline tech pipeline tests.
- FULL Phase 0 / crawl / GDELT / publication / GitHub Actions: dang cho live result.

## [2026-07-01 15:40] - Live Tech run update

- Validation live da hoan tat.
- Crawl live da hoan tat.
- Publication da build thanh cong tu crawl that + GDELT empty placeholder.
- GDELT live dry-run bi chan boi thieu ADC/BigQuery credentials trong runtime hien tai.

### Tong so
- Catalog: 100
- Active: 7
- Disabled: 93
- PASS_RSS: 2
- PASS_SITEMAP: 5
- SOFT_PASS: 3
- blocked/paywall/captcha: CAPTCHA 25, ARTICLE_EXTRACTION_FAILED 36, DEAD_URL 22, JS_ONLY 6, PAYWALL 1
- bai mau extract thanh cong: 465 samples tu 93 sources
- Crawl articles: 27 today, 76 all, 24 clean
- GDELT events: 0
- Publication stories: 24

### Test
- `python tech/validate_sources.py --force-refresh` -> pass
- `python tech/crawl.py` -> pass
- `python tech/publication.py` -> pass
- `python tech/validate_publication.py` -> pass
- `python scripts/test_tech_pipeline.py` -> pass

### GDELT / bytes
- Dry-run bytes: unavailable
- Ly do: `DefaultCredentialsError` do khong co ADC hop le trong runtime hien tai

### URL can Leon kiem tra lai
- `https://techcrunch.com/category/artificial-intelligence/`
- `https://www.theverge.com/ai-artificial-intelligence`
- `https://arstechnica.com/ai/`
- `https://www.wired.com/tag/artificial-intelligence/`
- `https://www.technologyreview.com/topic/artificial-intelligence/`
- `https://venturebeat.com/category/ai/`
- `https://spectrum.ieee.org/artificial-intelligence`
- `https://www.techrepublic.com/topic/artificial-intelligence/`

### Remaining
- Can ADC BigQuery hop le neu muon chay GDELT live that va cap nhat publication co event_count > 0.
- Neu push, chi stage file Tech + worklog; giu scratch/unrelated changes ngoai scope.

## 2026-07-03 - Technology & AI 72h live run

- Tech72h generated_at=2026-07-03T02:57:23.038385+00:00
- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.
- Format: AI Frontier Radar 72h.
- Schedule: once every 3 days; data window: latest 72 hours.
- Active sources: 7 / 100.
- Clean web articles: 24.
- Event candidates: 0; GDELT ran_successfully=False.
- Query estimate: 0 bytes; processed: 0 bytes; cap: 2,000,000,000 bytes.
- Published stories: 24; must_read=25; full_link_radar=58.
- Section counts: local_ai=7, automation=16, open_source=3, knowledge=4, founder_ideas=10.
- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.

## 2026-07-05 - Technology & AI 72h live run

- Tech72h generated_at=2026-07-05T04:39:38.612239+00:00
- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.
- Format: AI Frontier Radar 72h.
- Schedule: once every 3 days; data window: latest 72 hours.
- Active sources: 7 / 100.
- Clean web articles: 10.
- Candidate live: 10; noise bi loai: 0; bai qua han 72h bi loai khoi section chinh: 0.
- Event candidates: 0; GDELT ran_successfully=False.
- Query estimate: 0 bytes; processed: 0 bytes; cap: 2,000,000,000 bytes.
- Published stories: 10; must_read=0; full_link_radar=10.
- Must Read theo source type: {}.
- Must Read theo category: {}.
- Gemini curator: success=0; fallback=10.
- Section counts: local_ai=0, automation=0, open_source=0, knowledge=4, founder_ideas=10.
- /tech/ render check: knowledge=True; founder_ideas=True.
- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.

## 2026-07-10 - Technology & AI input coverage hardening

- Tech72h generated_at=2026-07-10T03:11:35.967630+00:00
- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.
- Local rebuild note: publication/matrix regenerated with `LEON_TECH_OFFLINE_TEST=1`; API/GitHub/HF/OpenRouter acquisition ran live locally, arXiv live returned HTTP 429, Gemini curator was not called.
- Added `tech/config/source_profiles.json` with explicit source profile fields: lane, method, url, priority, enabled, extract_mode, expected_fields, fallback.
- Added `tech/acquire_api_sources.py` for API-first acquisition: Hugging Face model metadata, GitHub releases/repo metadata, arXiv Atom fixtures/API, OpenRouter model list.
- Candidate contract now keeps `content_quality` and `raw_source_method`; metadata-only candidates are retained.
- Coverage matrix now separates `active_url_sources`, `active_watchlist_entities`, `active_api_sources`, `active_rss_sources`, `active_sitemap_sources`, and `metadata_only_sources`.
- Active sources: 7 / 100.
- Clean web articles: 10.
- Candidate live: 134; noise bi loai: 0; bai qua han 72h bi loai khoi section chinh: 20.
- Event candidates: 40; GDELT ran_successfully=True; raw=120; ai_filtered=40; rejected_non_ai=80.
- Query estimate: 1,057,267,222 bytes; processed: 1,057,267,222 bytes; bytes_status=known; cap: 2,000,000,000 bytes.
- Published stories: 10; must_read=20; full_link_radar=134.
- Must Read theo source type: {'official': 20}.
- Must Read theo category: {'model': 14, 'tool': 2, 'automation': 3, 'opensource': 1}.
- Frontier Watchlist entities: 26; candidates_from_watchlist=99; GLM-5.2 detected=yes.
- Data coverage: active_url_sources=7; active_api_sources=15; active_rss_sources=3; active_sitemap_sources=1; active_watchlist_entities=26; metadata_only_sources=19.
- API candidates: total=46; by_method={'hf_api': 14, 'github_api': 24, 'arxiv_api': 0, 'api': 8}; notes=["hf_api unavailable: No module named 'huggingface_hub'", 'arxiv_api: HTTP Error 429: Unknown Error'].
- candidates_by_method={'manual_signal': 51, 'github_api': 24, 'hf_api': 14, 'api': 8, 'gdelt': 27, 'html': 10}; content_quality_mix={'metadata_only': 91, 'summary_only': 33, 'full_text': 10}; remaining CAPTCHA/paywall/JS-only sources=1.
- Source mix main candidates: official=87, independent=0, community=0.
- Pages workflow includes Tech Radar: yes.
- Gemini curator: success=0; fallback=87; ai_main=0; fallback_main=87.
- Section counts: local_ai=0, automation=12, open_source=6, knowledge=3, founder_ideas=10.
- /tech/ render check: knowledge=True; founder_ideas=True.
- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.

## 2026-07-05 - Technology & AI 72h live run

- Tech72h generated_at=2026-07-05T05:22:31.926546+00:00
- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.
- Format: AI Frontier Radar 72h.
- Schedule: once every 3 days; data window: latest 72 hours.
- Active sources: 7 / 100.
- Clean web articles: 10.
- Candidate live: 94; noise bi loai: 0; bai qua han 72h bi loai khoi section chinh: 0.
- Event candidates: 119; GDELT ran_successfully=True.
- Query estimate: 0 bytes; processed: 0 bytes; cap: 2,000,000,000 bytes.
- Published stories: 10; must_read=0; full_link_radar=94.
- Must Read theo source type: {}.
- Must Read theo category: {}.
- Gemini curator: success=0; fallback=10.
- Section counts: local_ai=0, automation=0, open_source=0, knowledge=4, founder_ideas=10.
- /tech/ render check: knowledge=True; founder_ideas=True.
- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.

## 2026-07-05 - Technology & AI 72h live run

- Tech72h generated_at=2026-07-05T05:25:49.429275+00:00
- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.
- Format: AI Frontier Radar 72h.
- Schedule: once every 3 days; data window: latest 72 hours.
- Active sources: 7 / 100.
- Clean web articles: 10.
- Candidate live: 94; noise bi loai: 0; bai qua han 72h bi loai khoi section chinh: 0.
- Event candidates: 119; GDELT ran_successfully=True.
- Query estimate: 0 bytes; processed: 0 bytes; cap: 2,000,000,000 bytes.
- Published stories: 10; must_read=0; full_link_radar=94.
- Must Read theo source type: {}.
- Must Read theo category: {}.
- Gemini curator: success=0; fallback=10.
- Section counts: local_ai=0, automation=0, open_source=0, knowledge=4, founder_ideas=10.
- /tech/ render check: knowledge=True; founder_ideas=True.
- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.

## 2026-07-05 - Technology & AI 72h live run

- Tech72h generated_at=2026-07-05T05:31:05.807570+00:00
- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.
- Format: AI Frontier Radar 72h.
- Schedule: once every 3 days; data window: latest 72 hours.
- Active sources: 7 / 100.
- Clean web articles: 10.
- Candidate live: 94; noise bi loai: 1; bai qua han 72h bi loai khoi section chinh: 0.
- Event candidates: 119; GDELT ran_successfully=True.
- Query estimate: 0 bytes; processed: 0 bytes; cap: 2,000,000,000 bytes.
- Published stories: 10; must_read=0; full_link_radar=94.
- Must Read theo source type: {}.
- Must Read theo category: {}.
- Gemini curator: success=5; fallback=5.
- Section counts: local_ai=1, automation=1, open_source=0, knowledge=1, founder_ideas=4.
- /tech/ render check: knowledge=True; founder_ideas=True.
- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.

## 2026-07-05 - Technology & AI 72h live run

- Tech72h generated_at=2026-07-05T06:21:11.627937+00:00
- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.
- Format: AI Frontier Radar 72h.
- Schedule: once every 3 days; data window: latest 72 hours.
- Active sources: 7 / 100.
- Clean web articles: 10.
- Candidate live: 37; noise bi loai: 3; bai qua han 72h bi loai khoi section chinh: 0.
- Event candidates: 40; GDELT ran_successfully=True; raw=120; ai_filtered=40; rejected_non_ai=80.
- Query estimate: 1,057,267,222 bytes; processed: unknown bytes; bytes_status=known; cap: 2,000,000,000 bytes.
- Published stories: 10; must_read=6; full_link_radar=37.
- Must Read theo source type: {'community': 5, 'independent': 1}.
- Must Read theo category: {'local_ai': 1, 'tool': 1, 'opensource': 1, 'business': 2, 'knowledge': 1}.
- Gemini curator: success=10; fallback=0; ai_main=7; fallback_main=0.
- Section counts: local_ai=1, automation=0, open_source=1, knowledge=2, founder_ideas=6.
- /tech/ render check: knowledge=True; founder_ideas=True.
- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.

## 2026-07-05 - Technology & AI 72h live run

- Tech72h generated_at=2026-07-05T06:24:34.693189+00:00
- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.
- Format: AI Frontier Radar 72h.
- Schedule: once every 3 days; data window: latest 72 hours.
- Active sources: 7 / 100.
- Clean web articles: 10.
- Candidate live: 37; noise bi loai: 3; bai qua han 72h bi loai khoi section chinh: 0.
- Event candidates: 40; GDELT ran_successfully=True; raw=120; ai_filtered=40; rejected_non_ai=80.
- Query estimate: 1,057,267,222 bytes; processed: 1,057,267,222 bytes; bytes_status=known; cap: 2,000,000,000 bytes.
- Published stories: 10; must_read=6; full_link_radar=37.
- Must Read theo source type: {'community': 5, 'independent': 1}.
- Must Read theo category: {'model': 1, 'local_ai': 1, 'tool': 1, 'opensource': 1, 'business': 1, 'agent': 1}.
- Gemini curator: success=10; fallback=0; ai_main=7; fallback_main=0.
- Section counts: local_ai=1, automation=2, open_source=1, knowledge=3, founder_ideas=6.
- /tech/ render check: knowledge=True; founder_ideas=True.
- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.

## 2026-07-06 - Tech Frontier Watchlist and Must Read source-quality fix

- Scope: standalone `tech/` + Pages workflow trigger only; Tin48h, Invest and World LIVE logic unchanged.
- Added `tech/config/frontier_watchlist.json` with 11 China/frontier AI entities: Zhipu/Z.ai, Qwen/Alibaba, Kimi/Moonshot, MiniMax, DeepSeek, Doubao/ByteDance, Hunyuan/Tencent, StepFun, InternLM, SenseTime, Baichuan.
- Added official/direct source metadata for Zhipu/GLM: Z.ai blog, Z.ai docs, BigModel docs/release notes, Hugging Face `zai-org`, GitHub `zai-org`.
- Added watchlist acquisition before curator: candidates can carry `matched_entity`, `matched_alias`, `source_type`, `signal_type`, `trend_status`, and watchlist evidence.
- GLM-5.2 fixture detected: yes. Fixture expects Z.ai/Zhipu/GLM-5.2 to appear as a candidate, category `model` or `local_ai`, matched_entity `Zhipu/Z.ai`, main section inclusion, and Must Read consideration when official/independent.
- Current local artifact data still has GLM-5.2 detected: no, because existing 72h crawl/GDELT artifact does not include GLM/Zhipu/Z.ai signal.
- Temp rebuild from current local data after source-quality fix: watchlist entities=11; candidates_from_watchlist=3; Must Read source type `{'community': 1, 'independent': 1}`; main candidates official=0, independent=1, community=8.
- Must Read ranking now prefers official/independent and does not fill above 50% community when non-community candidates exist; importance=1 requires `evidence=exploratory`.
- Validator now fails Must Read community share >50% when any non-community main candidate exists, and requires `stats.must_read_quality_warning` if such an artifact is produced.
- Pages workflow includes Tech Radar: yes (`.github/workflows/pages.yml` workflow_run now includes `Tech Radar`).
- Tests: `python -m py_compile ...` pass; `python scripts/test_tech_pipeline.py` pass; temp `tech/publication.py` + `tech/validate_publication.py --input <temp>` pass. Existing committed `tech/data/publication.json` was not regenerated locally because local run is offline/fallback and current data lacks GLM-5.2.

## 2026-07-08 - AI Frontier Radar cluster/lane hardening

- Scope: standalone `tech/`, Tech workflow, Tech GDELT SQL/Python filter, Tech frontend only. Tin48h, Invest and World LIVE logic unchanged.
- Goal: move AI Frontier Radar 72h toward an objective signal radar: what happened, what changed, why it matters, affected ecosystem, evidence links, and neutral possible applications.
- Data refresh split: `.github/workflows/tech-radar.yml` now runs crawl + GDELT acquisition on every scheduled/manual Tech run; only `tech/data/publication.json` / `tech/web/publication.json` are gated by 72h publish age. When publish is skipped, builder writes temp publication only to refresh rolling/status/matrix artifacts.
- `tech/crawl.py` no longer skips by publication age by default; `--respect-publish-gate` is now opt-in.
- Expanded `tech/config/frontier_watchlist.json` to 26 entities: China AI, Flux/BFL, ComfyUI, Runway, Kling, Veo, Sora, HunyuanVideo, OpenRouter, Replicate, fal.ai, MCP, LangGraph, LlamaIndex, Cursor, Claude Code, OpenHands.
- Candidate contract now includes `source_lane`, `matched_entity`, `matched_alias`, `published_at`, `discovered_at`, `time_verified`, `evidence`, `url`, `title`.
- Added lanes beyond normal_web/GDELT: `frontier_watchlist`, `model_hub`, `github_release`, `huggingface_model`, `image_video_workflow`, `community`.
- Added rolling 7-day candidate artifact: `tech/data/candidates_rolling.json`.
- Added watchlist run artifact: `tech/data/watchlist_status.json`.
- Added coverage report: `tech/reports/source_coverage_matrix.md`.
- Added `top_signal_clusters` to publication and made `/tech/` prefer Top Signal Clusters over article-level Must Read; legacy Must Read remains for backward compatibility.
- Full Link Radar is compact and includes `title`, `url`, `source`, `category`, `cluster_id`, `one_line_reason`, `source_lane`, `published_at`, while keeping old fields for compatibility.
- GDELT hardening: expanded SQL/Python entity keywords for GLM/Z.ai/Zhipu, Flux, ComfyUI, video AI, OpenRouter/Replicate/fal.ai, MCP/LangGraph/LlamaIndex/Cursor/Claude Code/OpenHands; previous-event reuse now marks `reused_previous_events`, `fresh_event_count`, and `previous_events_age_hours`.
- Validator now checks watchlist/status presence, checked entities, top clusters, lane counts, model_hub/image_video candidates, compact Full Radar, GDELT reuse labeling, and over-personalized clusters.

### Local artifact stats
- generated_at_utc: `2026-07-08T18:20:21.311015+00:00`
- active sources: 7
- candidates by lane: `github_release=12`, `frontier_watchlist=21`, `huggingface_model=6`, `model_hub=4`, `image_video_workflow=8`, `gdelt=27`, `normal_web=1`, `community=9`
- watchlist checked/hit: `26 / 55`
- GDELT fresh/reused: `fresh_event_count=40`, `reused_previous_events=False`
- top_signal_clusters: 10
- full_link_radar: 88
- must_read: 20, source mix `official=20`

### Tests
- `.\.venv\Scripts\python.exe -m py_compile tech\crawl.py scripts\build_tech_publication.py scripts\validate_tech_publication.py scripts\run_tech_gdelt.py scripts\test_tech_pipeline.py scripts\tech_common.py` -> pass
- `.\.venv\Scripts\python.exe scripts\test_tech_pipeline.py` -> pass
- `.\.venv\Scripts\python.exe tech\publication.py` with `LEON_TECH_OFFLINE_TEST=1` -> pass
- `.\.venv\Scripts\python.exe tech\validate_publication.py` -> pass

### Remaining risks
- Local rebuild used offline curator mode; production Actions should be run with real Gemini/GDELT credentials for editorial copy quality.
- Active sources remain low (`7 / 100`), so source coverage is structurally weak even though watchlist/hub lanes now prevent 72h gate from hiding hot signals.

## 2026-07-08 - Technology & AI 72h live run

- Tech72h generated_at=2026-07-08T18:37:32.827967+00:00
- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.
- Format: AI Frontier Radar 72h.
- Schedule: once every 3 days; data window: latest 72 hours.
- Active sources: 7 / 100.
- Clean web articles: 22.
- Candidate live: 109; noise bi loai: 3; bai qua han 72h bi loai khoi section chinh: 0.
- Event candidates: 50; GDELT ran_successfully=True; raw=120; ai_filtered=50; rejected_non_ai=70.
- Query estimate: 1,819,200,210 bytes; processed: 1,819,200,210 bytes; bytes_status=known; cap: 2,000,000,000 bytes.
- Published stories: 22; must_read=20; full_link_radar=109.
- Must Read theo source type: {'independent': 3, 'official': 17}.
- Must Read theo category: {'model': 12, 'local_ai': 1, 'tool': 2, 'automation': 2, 'opensource': 1, 'business': 1, 'mcp': 1}.
- Gemini curator: success=20; fallback=53; ai_main=18; fallback_main=52.
- Section counts: local_ai=4, automation=11, open_source=8, knowledge=4, founder_ideas=10.
- /tech/ render check: knowledge=True; founder_ideas=True.
- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.

## 2026-07-10 - Technology & AI 72h live run

- Tech72h generated_at=2026-07-10T03:26:04.845729+00:00
- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.
- Format: AI Frontier Radar 72h.
- Schedule: once every 3 days; data window: latest 72 hours.
- Active sources: 7 / 100.
- Clean web articles: 27.
- Candidate live: 190; noise bi loai: 0; bai qua han 72h bi loai khoi section chinh: 20.
- Event candidates: 52; GDELT ran_successfully=True; raw=120; ai_filtered=52; rejected_non_ai=68.
- Query estimate: 1,440,497,558 bytes; processed: 1,440,497,558 bytes; bytes_status=known; cap: 2,000,000,000 bytes.
- Published stories: 27; must_read=20; full_link_radar=150.
- Must Read theo source type: {'official': 19, 'independent': 1}.
- Must Read theo category: {'model': 10, 'local_ai': 1, 'tool': 2, 'automation': 3, 'opensource': 1, 'business': 1, 'knowledge': 1, 'industry': 1}.
- Frontier Watchlist entities: 26; candidates_from_watchlist=120; GLM-5.2 detected=yes.
- Data coverage: active_url_sources=7; active_api_sources=15; active_rss_sources=3; active_sitemap_sources=1; active_watchlist_entities=26; metadata_only_sources=19.
- API candidates: total=75; by_method={'hf_api': 27, 'github_api': 30, 'arxiv_api': 10, 'api': 8}; notes=[].
- candidates_by_method={'manual_signal': 51, 'github_api': 30, 'hf_api': 27, 'api': 8, 'arxiv_api': 10, 'html': 27, 'gdelt': 37}; content_quality_mix={'metadata_only': 104, 'summary_only': 59, 'full_text': 27}; remaining CAPTCHA/paywall/JS-only sources=1.
- Source mix main candidates: official=96, independent=4, community=0.
- Pages workflow includes Tech Radar: yes.
- Gemini curator: success=36; fallback=64; ai_main=36; fallback_main=64.
- Section counts: local_ai=2, automation=12, open_source=7, knowledge=4, founder_ideas=10.
- /tech/ render check: knowledge=True; founder_ideas=True.
- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.

## 2026-07-10 - Technology & AI 72h live run

- Tech72h generated_at=2026-07-10T07:12:55.275915+00:00
- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.
- Format: AI Frontier Radar 72h.
- Schedule: once every 3 days; data window: latest 72 hours.
- Active sources: 7 / 100.
- Clean web articles: 27.
- Candidate live: 113; noise bi loai: 3; bai qua han 72h bi loai khoi section chinh: 10.
- Event candidates: 52; GDELT ran_successfully=True; raw=120; ai_filtered=52; rejected_non_ai=68.
- Query estimate: 1,440,497,558 bytes; processed: 1,440,497,558 bytes; bytes_status=known; cap: 2,000,000,000 bytes.
- Published stories: 27; must_read=19; full_link_radar=113.
- Must Read theo source type: {'official': 8, 'independent': 6, 'community': 5}.
- Must Read theo category: {'model': 5, 'local_ai': 3, 'tool': 5, 'automation': 3, 'opensource': 3}.
- Frontier Watchlist entities: 26; candidates_from_watchlist=52; GLM-5.2 detected=yes.
- Data coverage: active_url_sources=7; active_api_sources=15; active_rss_sources=3; active_sitemap_sources=1; active_watchlist_entities=26; metadata_only_sources=19.
- API candidates: total=49; by_method={'hf_api': 14, 'github_api': 24, 'arxiv_api': 3, 'api': 8}; notes=["hf_api unavailable: No module named 'huggingface_hub'"].
- Input quality: real_candidate_count=113; manual_signal_count=0; weak_metadata_match_count=3; official_org_candidate_count=23.
- candidates_by_method={'github_api': 24, 'hf_api': 14, 'api': 8, 'arxiv_api': 3, 'html': 27, 'gdelt': 37}; content_quality_mix={'summary_only': 46, 'metadata_only': 40, 'full_text': 27}; remaining CAPTCHA/paywall/JS-only sources=1.
- Source mix main candidates: official=30, independent=13, community=13.
- Pages workflow includes Tech Radar: yes.
- Gemini curator: success=0; fallback=59; ai_main=0; fallback_main=56.
- Section counts: local_ai=7, automation=11, open_source=5, knowledge=4, founder_ideas=10.
- /tech/ render check: knowledge=True; founder_ideas=True.
- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.

## 2026-07-12 - Technology & AI 72h live run

- Tech72h generated_at=2026-07-12T10:06:32.000966+00:00
- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.
- Format: AI Frontier Radar 72h.
- Schedule: once every 3 days; data window: latest 72 hours.
- Active sources: 7 / 100.
- Clean web articles: 17.
- Candidate live: 114; noise bi loai: 3; bai qua han 72h bi loai khoi section chinh: 17.
- Event candidates: 38; GDELT ran_successfully=True; raw=120; ai_filtered=38; rejected_non_ai=82.
- Query estimate: 1,152,060,049 bytes; processed: 1,152,060,049 bytes; bytes_status=known; cap: 2,000,000,000 bytes.
- Published stories: 17; must_read=14; full_link_radar=114.
- Must Read theo source type: {'independent': 6, 'official': 3, 'community': 5}.
- Must Read theo category: {'model': 2, 'local_ai': 2, 'tool': 1, 'automation': 3, 'opensource': 1, 'knowledge': 1, 'industry': 2, 'agent': 2}.
- Frontier Watchlist entities: 26; candidates_from_watchlist=63; GLM-5.2 detected=yes.
- Data coverage: active_url_sources=7; active_api_sources=15; active_rss_sources=3; active_sitemap_sources=1; active_watchlist_entities=26; metadata_only_sources=19.
- API candidates: total=75; by_method={'hf_api': 27, 'github_api': 30, 'arxiv_api': 10, 'api': 8}; notes=[].
- Input quality: real_candidate_count=114; manual_signal_count=0; weak_metadata_match_count=7; official_org_candidate_count=27.
- candidates_by_method={'github_api': 30, 'hf_api': 27, 'api': 8, 'html': 17, 'arxiv_api': 10, 'gdelt': 22}; content_quality_mix={'metadata_only': 53, 'summary_only': 44, 'full_text': 17}; remaining CAPTCHA/paywall/JS-only sources=1.
- Source mix main candidates: official=4, independent=16, community=8.
- Pages workflow includes Tech Radar: yes.
- Gemini curator: success=18; fallback=13; ai_main=16; fallback_main=12.
- Section counts: local_ai=3, automation=10, open_source=1, knowledge=4, founder_ideas=10.
- /tech/ render check: knowledge=True; founder_ideas=True.
- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.

## 2026-07-18 - Tech Radar input/source-health hardening

- Scope: input/acquisition/report/validator only; no editorial, publication artifact, or UI changes.
- Kept the existing 63 active RSS feeds as Tier 2 discovery in `tech/config/sources_active.txt`; no bulk deletion.
- Added unified `tech/config/source_profiles.json` v2 with Tier 0 primary sources for OpenAI, Anthropic, Google AI, DeepMind, Gemini developer changelog, Meta AI/Llama, Mistral, Microsoft Research, Azure AI, AWS ML/Bedrock, Apple ML, NVIDIA, AMD, Intel, Arm, NIST AI, EU AI Office, and CISA.
- Added source health artifact `tech/data/source_registry.json` with `entity`, `lane`, `priority`, `source_type`, `method`, `last_checked_at`, `last_success_at`, `latest_item_at`, `status`, `error`, and `fallback_used`.
- Acquisition priority now supports RSS/Atom, API/GitHub/HF/arXiv, sitemap/metadata/changelog snapshot, then metadata fallback; official source health is not disabled just because article/full-text extraction fails.
- Added minimum GitHub/API coverage for `transformers`, `diffusers`, `pytorch`, `llama.cpp`, `ollama`, `vLLM`, `SGLang`, `ComfyUI`, `LangGraph`, `LlamaIndex`, MCP, and OpenHands.
- Research acquisition now splits arXiv across `cs.AI`, `cs.CL`, `cs.LG`, `cs.CV`, and `cs.RO` instead of one global 10-result query; OpenReview ICLR/NeurIPS/ICML endpoints are configured and health-checked as P1 research sources.
- GitHub releases remain distinct from repo metadata: real release rows use `evidence=github_release`, while repo update fallback rows stay `metadata_only` and are not eligible for Must Read/main/top clusters.
- Coverage matrix now reports P0 configured/checked/success/failed/zero_hit, coverage by lane, `missing_critical_entities`, `verified_timestamp_ratio`, full_text/summary/metadata ratio, and primary/independent/community source counts.
- Validator now fails if `source_registry.json` is missing/stale, P0 is not fully checked, all P0 methods fail, or any critical entity is missing; it does not fail merely because a lane has zero news.

### Live acquisition run

- Command: `.venv\Scripts\python.exe tech\acquire_api_sources.py --hf-limit 1 --github-releases 1 --arxiv-results 10` with local `GITHUB_TOKEN` from `gh auth token`.
- API candidates: total=101; by_method `{'hf_api': 14, 'github_api': 30, 'arxiv_api': 8, 'api': 8}`.
- Source registry: source_count=109; P0 configured/checked/success/fail/zero_hit=`31/31/31/0/0`; missing_critical_entities=`[]`.
- Registry quality: verified_timestamp_ratio=`1.0`; content_quality_ratio=`{'full_text': 0.0, 'summary_only': 0.5248, 'metadata_only': 0.4752}`; primary/independent/community source counts=`27/63/19`.
- Lane health: official_ai_labs `11/11/11/0/0`; github_releases `8/8/8/0/0`; automation_agents `4/4/4/0/0`; chips_infra `4/4/4/0/0`; policy_risk `3/3/3/0/0`; model_hubs P0 `1/1/1/0/0`.
- Candidate coverage after temp build: real_candidate_count=498; manual_signal_count=0; candidates_by_method includes `github_api=30`, `hf_api=14`, `rss=33`, `html=377`, `gdelt=20`, `arxiv_api=8`, `api=8`.
- Watchlist checked/hits: 26/71.
- Remaining gaps: OpenReview ICLR/NeurIPS/ICML are configured/checked but still zero-hit in local acquisition; local HF used REST fallback because `huggingface_hub` is not installed in `.venv`, while Actions installs it.
- Verification: `py_compile` pass; `python scripts/test_tech_pipeline.py` pass; temp build `tech/publication.py --output .tmp_tech_publication.json --web-output .tmp_tech_publication_web.json` plus `tech/validate_publication.py --input .tmp_tech_publication.json` pass. Temp publication files were removed; committed/public `tech/data/publication.json`, `tech/web/publication.json`, and UI were not changed.
## 2026-07-12 - Tech direct-feed source expansion

- Scope: input/acquisition only; no UI/editorial changes.
- Replaced the legacy page/category catalog (7 production-ready) with 84 live-probed direct RSS/Atom endpoints across North America, Europe, Asia-Pacific, MENA, Africa, and Latin America.
- Direct-feed validation requires at least 3 of 5 entries with URL, title, published date, and feed content >=180 characters. HTTP 200 or headline-only feeds do not pass.
- Live report: catalog=84, PASS_RSS=63, SOFT_PASS=5, ARTICLE_EXTRACTION_FAILED=14, DEAD_URL=2; 63 active unique domains.
- Profiler detects feeds by parsed body, including endpoints without rss/feed in the URL, and skips unnecessary sitemap/HTML/JS/paywall probes.
- RSS spider/pipeline carries feed title, published time, and summary; blocked/short article extraction can persist a real feed summary with `:feed_summary_fallback` provenance.
- Full one-URL-per-source Scrapy smoke: 59/63 active source ids wrote content; 4 failed in this run (`canaltech_com_br`, `tech_eu`, `theregister_com`, `uktech_news`).
- Tests: `python scripts/test_tech_pipeline.py` pass; `python tech/validate_publication.py` pass.

## 2026-07-12 - Technology & AI 72h live run

- Tech72h generated_at=2026-07-12T15:30:38.783224+00:00
- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.
- Format: AI Frontier Radar 72h.
- Schedule: once every 3 days; data window: latest 72 hours.
- Active sources: 63 / 84.
- Clean web articles: 377.
- Candidate live: 472; noise bi loai: 18; bai qua han 72h bi loai khoi section chinh: 17.
- Event candidates: 28; GDELT ran_successfully=True; raw=120; ai_filtered=28; rejected_non_ai=92.
- Query estimate: 1,251,321,846 bytes; processed: 1,251,321,846 bytes; bytes_status=known; cap: 2,000,000,000 bytes.
- Published stories: 377; must_read=20; full_link_radar=150.
- Must Read theo source type: {'independent': 18, 'official': 2}.
- Must Read theo category: {'model': 4, 'local_ai': 5, 'tool': 6, 'automation': 1, 'opensource': 1, 'business': 1, 'industry': 1, 'agent': 1}.
- Frontier Watchlist entities: 26; candidates_from_watchlist=81; GLM-5.2 detected=yes.
- Data coverage: active_url_sources=63; active_api_sources=15; active_rss_sources=63; active_sitemap_sources=1; active_watchlist_entities=26; metadata_only_sources=19.
- API candidates: total=75; by_method={'hf_api': 27, 'github_api': 30, 'arxiv_api': 10, 'api': 8}; notes=[].
- Input quality: real_candidate_count=472; manual_signal_count=0; weak_metadata_match_count=8; official_org_candidate_count=27.
- candidates_by_method={'github_api': 30, 'hf_api': 27, 'api': 8, 'html': 377, 'gdelt': 20, 'arxiv_api': 10}; content_quality_mix={'metadata_only': 53, 'summary_only': 42, 'full_text': 377}; remaining CAPTCHA/paywall/JS-only sources=1.
- Source mix main candidates: official=5, independent=77, community=0.
- Pages workflow includes Tech Radar: yes.
- Gemini curator: success=29; fallback=71; ai_main=19; fallback_main=63.
- Section counts: local_ai=12, automation=7, open_source=12, knowledge=4, founder_ideas=10.
- /tech/ render check: knowledge=True; founder_ideas=True.
- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.

## 2026-07-18 - Technology & AI 72h live run

- Tech72h generated_at=2026-07-18T14:35:34.585289+00:00
- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.
- Format: AI Frontier Radar 72h.
- Schedule: once every 3 days; data window: latest 72 hours.
- Active sources: 63 / 84.
- Clean web articles: 544.
- Candidate live: 698; noise bi loai: 12; bai qua han 72h bi loai khoi section chinh: 27.
- Event candidates: 50; GDELT ran_successfully=True; raw=120; ai_filtered=50; rejected_non_ai=70.
- Query estimate: 1,515,107,837 bytes; processed: 1,515,107,837 bytes; bytes_status=known; cap: 2,000,000,000 bytes.
- Published stories: 544; must_read=20; full_link_radar=150.
- Must Read theo source type: {'independent': 16, 'official': 4}.
- Must Read theo category: {'model': 4, 'local_ai': 1, 'tool': 9, 'automation': 1, 'opensource': 2, 'business': 1, 'knowledge': 1, 'industry': 1}.
- Frontier Watchlist entities: 26; candidates_from_watchlist=122; GLM-5.2 detected=yes.
- Data coverage: active_url_sources=63; active_api_sources=27; active_rss_sources=63; active_sitemap_sources=0; active_watchlist_entities=26; metadata_only_sources=46.
- Source registry P0: configured=31; checked=31; success=31; failed=0; zero_hit=0; missing_critical=[].
- Registry quality: verified_timestamp_ratio=1.0; content_quality_ratio={'full_text': 0.0, 'summary_only': 0.5242, 'metadata_only': 0.4758}; primary/independent/community=27/63/19.
- API candidates: total=124; by_method={'hf_api': 27, 'github_api': 42, 'arxiv_api': 8, 'api': 8}; notes=['profile AMD AI Blog: HTTP Error 404: Not Found', 'profile Intel AI Blog: HTTP Error 403: Forbidden', 'profile Arm AI Blog: The read operation timed out'].
- Input quality: real_candidate_count=698; manual_signal_count=0; weak_metadata_match_count=16; official_org_candidate_count=63.
- candidates_by_method={'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'html': 544, 'rss': 27, 'arxiv_api': 8, 'gdelt': 33}; content_quality_mix={'metadata_only': 59, 'summary_only': 95, 'full_text': 544}; remaining CAPTCHA/paywall/JS-only sources=0.
- Source mix main candidates: official=7, independent=81, community=0.
- Pages workflow includes Tech Radar: yes.
- Gemini curator: success=24; fallback=76; ai_main=22; fallback_main=66.
- Section counts: local_ai=12, automation=7, open_source=12, knowledge=4, founder_ideas=10.
- /tech/ render check: knowledge=True; founder_ideas=True.
- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.

## 2026-07-21 - Technology & AI 72h live run

- Tech72h generated_at=2026-07-21T15:21:53.724053+00:00
- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.
- Format: AI Frontier Radar 72h.
- Schedule: once every 3 days; data window: latest 72 hours.
- Active sources: 63 / 84.
- Clean web articles: 678.
- Candidate live: 818; noise bi loai: 17; bai qua han 72h bi loai khoi section chinh: 29.
- Event candidates: 34; GDELT ran_successfully=True; raw=120; ai_filtered=34; rejected_non_ai=86.
- Query estimate: 1,311,206,899 bytes; processed: 1,311,206,899 bytes; bytes_status=known; cap: 2,000,000,000 bytes.
- Published stories: 678; must_read=20; full_link_radar=150.
- Must Read theo source type: {'independent': 14, 'official': 6}.
- Must Read theo category: {'model': 1, 'local_ai': 1, 'tool': 9, 'automation': 1, 'opensource': 1, 'business': 2, 'industry': 3, 'agent': 2}.
- Frontier Watchlist entities: 26; candidates_from_watchlist=129; GLM-5.2 detected=yes.
- Data coverage: active_url_sources=63; active_api_sources=27; active_rss_sources=63; active_sitemap_sources=0; active_watchlist_entities=26; metadata_only_sources=46.
- Source registry P0: configured=31; checked=31; success=31; failed=0; zero_hit=0; missing_critical=[].
- Registry quality: verified_timestamp_ratio=1.0; content_quality_ratio={'full_text': 0.0, 'summary_only': 0.5124, 'metadata_only': 0.4876}; primary/independent/community=27/63/19.
- API candidates: total=121; by_method={'hf_api': 27, 'github_api': 42, 'arxiv_api': 7, 'api': 8}; notes=['profile AMD AI Blog: HTTP Error 404: Not Found', 'profile Intel AI Blog: HTTP Error 403: Forbidden', 'profile Arm AI Blog: The read operation timed out'].
- Input quality: real_candidate_count=818; manual_signal_count=0; weak_metadata_match_count=12; official_org_candidate_count=63.
- candidates_by_method={'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'rss': 24, 'metadata': 5, 'html': 675, 'arxiv_api': 7, 'gdelt': 25}; content_quality_mix={'summary_only': 84, 'metadata_only': 59, 'full_text': 675}; remaining CAPTCHA/paywall/JS-only sources=0.
- Source mix main candidates: official=8, independent=75, community=0.
- Pages workflow includes Tech Radar: yes.
- Gemini curator: success=31; fallback=69; ai_main=27; fallback_main=56.
- Section counts: local_ai=6, automation=10, open_source=12, knowledge=4, founder_ideas=10.
- /tech/ render check: knowledge=True; founder_ideas=True.
- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.

## 2026-07-24 - Technology & AI 72h live run

- Tech72h generated_at=2026-07-24T20:45:27.047776+00:00
- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.
- Format: AI Frontier Radar 72h.
- Schedule: once every 3 days; data window: latest 72 hours.
- Active sources: 63 / 84.
- Clean web articles: 469.
- Candidate live: 635; noise bi loai: 12; bai qua han 72h bi loai khoi section chinh: 30.
- Event candidates: 61; GDELT ran_successfully=True; raw=120; ai_filtered=61; rejected_non_ai=59.
- Query estimate: 1,879,464,669 bytes; processed: 1,879,464,669 bytes; bytes_status=known; cap: 2,000,000,000 bytes.
- Published stories: 469; must_read=20; full_link_radar=150.
- Must Read theo source type: {'independent': 15, 'official': 5}.
- Must Read theo category: {'model': 2, 'local_ai': 2, 'tool': 7, 'automation': 1, 'opensource': 1, 'business': 1, 'industry': 3, 'agent': 3}.
- Frontier Watchlist entities: 26; candidates_from_watchlist=111; GLM-5.2 detected=yes.
- Data coverage: active_url_sources=63; active_api_sources=27; active_rss_sources=63; active_sitemap_sources=0; active_watchlist_entities=26; metadata_only_sources=46.
- Source registry P0: configured=31; checked=31; success=31; failed=0; zero_hit=0; missing_critical=[].
- Registry quality: verified_timestamp_ratio=1.0; content_quality_ratio={'full_text': 0.0, 'summary_only': 0.5397, 'metadata_only': 0.4603}; primary/independent/community=27/63/19.
- API candidates: total=126; by_method={'hf_api': 27, 'github_api': 42, 'arxiv_api': 10, 'api': 8}; notes=['profile AMD AI Blog: HTTP Error 404: Not Found', 'profile Intel AI Blog: HTTP Error 403: Forbidden', 'profile Arm AI Blog: The read operation timed out'].
- Input quality: real_candidate_count=635; manual_signal_count=0; weak_metadata_match_count=12; official_org_candidate_count=63.
- candidates_by_method={'github_api': 42, 'hf_api': 27, 'changelog_snapshot': 5, 'api': 8, 'metadata': 4, 'rss': 27, 'html': 468, 'arxiv_api': 10, 'gdelt': 44}; content_quality_mix={'metadata_only': 58, 'summary_only': 109, 'full_text': 468}; remaining CAPTCHA/paywall/JS-only sources=0.
- Source mix main candidates: official=7, independent=81, community=0.
- Pages workflow includes Tech Radar: yes.
- Gemini curator: success=33; fallback=67; ai_main=29; fallback_main=59.
- Section counts: local_ai=11, automation=5, open_source=12, knowledge=4, founder_ideas=10.
- /tech/ render check: knowledge=True; founder_ideas=True.
- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.

## 2026-07-28 - Technology & AI 72h live run

- Tech72h generated_at=2026-07-28T04:34:06.574192+00:00
- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.
- Format: AI Frontier Radar 72h.
- Schedule: once every 3 days; data window: latest 72 hours.
- Active sources: 63 / 84.
- Clean web articles: 558.
- Candidate live: 693; noise bi loai: 9; bai qua han 72h bi loai khoi section chinh: 30.
- Event candidates: 32; GDELT ran_successfully=True; raw=120; ai_filtered=32; rejected_non_ai=88.
- Query estimate: 1,037,683,691 bytes; processed: 1,037,683,691 bytes; bytes_status=known; cap: 2,000,000,000 bytes.
- Published stories: 558; must_read=20; full_link_radar=150.
- Must Read theo source type: {'independent': 14, 'official': 6}.
- Must Read theo category: {'model': 5, 'local_ai': 1, 'tool': 7, 'automation': 1, 'opensource': 1, 'business': 1, 'knowledge': 1, 'industry': 1, 'mcp': 1, 'agent': 1}.
- Frontier Watchlist entities: 26; candidates_from_watchlist=114; GLM-5.2 detected=yes.
- Data coverage: active_url_sources=63; active_api_sources=27; active_rss_sources=63; active_sitemap_sources=0; active_watchlist_entities=26; metadata_only_sources=46.
- Source registry P0: configured=31; checked=31; success=31; failed=0; zero_hit=0; missing_critical=[].
- Registry quality: verified_timestamp_ratio=1.0; content_quality_ratio={'full_text': 0.0, 'summary_only': 0.5207, 'metadata_only': 0.4793}; primary/independent/community=27/63/19.
- API candidates: total=121; by_method={'hf_api': 27, 'github_api': 42, 'arxiv_api': 5, 'api': 8}; notes=['profile AMD AI Blog: HTTP Error 404: Not Found', 'profile Intel AI Blog: HTTP Error 403: Forbidden', 'profile Arm AI Blog: The read operation timed out'].
- Input quality: real_candidate_count=693; manual_signal_count=0; weak_metadata_match_count=12; official_org_candidate_count=63.
- candidates_by_method={'github_api': 42, 'hf_api': 27, 'changelog_snapshot': 5, 'api': 8, 'metadata': 4, 'html': 555, 'rss': 27, 'arxiv_api': 5, 'gdelt': 20}; content_quality_mix={'metadata_only': 58, 'summary_only': 80, 'full_text': 555}; remaining CAPTCHA/paywall/JS-only sources=0.
- Source mix main candidates: official=7, independent=84, community=0.
- Pages workflow includes Tech Radar: yes.
- Gemini curator: success=28; fallback=72; ai_main=25; fallback_main=66.
- Section counts: local_ai=12, automation=7, open_source=10, knowledge=4, founder_ideas=10.
- /tech/ render check: knowledge=True; founder_ideas=True.
- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.

## 2026-07-31 - Technology & AI 72h live run

- Tech72h generated_at=2026-07-31T04:48:14.912374+00:00
- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.
- Format: AI Frontier Radar 72h.
- Schedule: once every 3 days; data window: latest 72 hours.
- Active sources: 63 / 84.
- Clean web articles: 551.
- Candidate live: 696; noise bi loai: 14; bai qua han 72h bi loai khoi section chinh: 27.
- Event candidates: 50; GDELT ran_successfully=True; raw=120; ai_filtered=50; rejected_non_ai=70.
- Query estimate: 1,415,024,247 bytes; processed: 1,415,024,247 bytes; bytes_status=known; cap: 2,000,000,000 bytes.
- Published stories: 551; must_read=20; full_link_radar=150.
- Must Read theo source type: {'independent': 11, 'official': 9}.
- Must Read theo category: {'model': 1, 'local_ai': 1, 'tool': 10, 'automation': 4, 'opensource': 1, 'business': 1, 'industry': 1, 'mcp': 1}.
- Frontier Watchlist entities: 26; candidates_from_watchlist=94; GLM-5.2 detected=yes.
- Data coverage: active_url_sources=63; active_api_sources=27; active_rss_sources=63; active_sitemap_sources=0; active_watchlist_entities=26; metadata_only_sources=46.
- Source registry P0: configured=31; checked=31; success=31; failed=0; zero_hit=0; missing_critical=[].
- Registry quality: verified_timestamp_ratio=1.0; content_quality_ratio={'full_text': 0.0, 'summary_only': 0.5082, 'metadata_only': 0.4918}; primary/independent/community=27/63/19.
- API candidates: total=122; by_method={'hf_api': 27, 'github_api': 42, 'arxiv_api': 6, 'api': 8}; notes=['profile AMD AI Blog: HTTP Error 404: Not Found', 'profile Intel AI Blog: HTTP Error 403: Forbidden', 'profile Arm AI Blog: The read operation timed out'].
- Input quality: real_candidate_count=696; manual_signal_count=0; weak_metadata_match_count=13; official_org_candidate_count=61.
- candidates_by_method={'github_api': 42, 'hf_api': 27, 'changelog_snapshot': 5, 'api': 8, 'metadata': 4, 'rss': 25, 'html': 548, 'arxiv_api': 6, 'gdelt': 31}; content_quality_mix={'metadata_only': 60, 'summary_only': 88, 'full_text': 548}; remaining CAPTCHA/paywall/JS-only sources=0.
- Source mix main candidates: official=12, independent=74, community=0.
- Pages workflow includes Tech Radar: yes.
- Gemini curator: success=38; fallback=62; ai_main=30; fallback_main=56.
- Section counts: local_ai=6, automation=12, open_source=8, knowledge=4, founder_ideas=10.
- /tech/ render check: knowledge=True; founder_ideas=True.
- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.

## 2026-08-03 - Technology & AI 72h live run

- Tech72h generated_at=2026-08-03T04:52:17.540263+00:00
- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.
- Format: AI Frontier Radar 72h.
- Schedule: once every 3 days; data window: latest 72 hours.
- Active sources: 63 / 84.
- Clean web articles: 275.
- Candidate live: 418; noise bi loai: 16; bai qua han 72h bi loai khoi section chinh: 31.
- Event candidates: 23; GDELT ran_successfully=True; raw=120; ai_filtered=23; rejected_non_ai=97.
- Query estimate: 829,076,834 bytes; processed: 829,076,834 bytes; bytes_status=known; cap: 2,000,000,000 bytes.
- Published stories: 275; must_read=20; full_link_radar=150.
- Must Read theo source type: {'independent': 16, 'official': 4}.
- Must Read theo category: {'model': 1, 'local_ai': 1, 'tool': 13, 'automation': 1, 'opensource': 2, 'business': 1, 'industry': 1}.
- Frontier Watchlist entities: 26; candidates_from_watchlist=90; GLM-5.2 detected=yes.
- Data coverage: active_url_sources=63; active_api_sources=27; active_rss_sources=63; active_sitemap_sources=0; active_watchlist_entities=26; metadata_only_sources=46.
- Source registry P0: configured=31; checked=31; success=31; failed=0; zero_hit=0; missing_critical=[].
- Registry quality: verified_timestamp_ratio=1.0; content_quality_ratio={'full_text': 0.0, 'summary_only': 0.5238, 'metadata_only': 0.4762}; primary/independent/community=27/63/19.
- API candidates: total=126; by_method={'hf_api': 27, 'github_api': 42, 'arxiv_api': 10, 'api': 8}; notes=['profile AMD AI Blog: HTTP Error 404: Not Found', 'profile Intel AI Blog: HTTP Error 403: Forbidden', 'profile Arm AI Blog: The read operation timed out'].
- Input quality: real_candidate_count=418; manual_signal_count=0; weak_metadata_match_count=15; official_org_candidate_count=65.
- candidates_by_method={'github_api': 42, 'hf_api': 27, 'changelog_snapshot': 5, 'api': 8, 'metadata': 4, 'html': 275, 'rss': 30, 'arxiv_api': 10, 'gdelt': 17}; content_quality_mix={'summary_only': 83, 'metadata_only': 60, 'full_text': 275}; remaining CAPTCHA/paywall/JS-only sources=0.
- Source mix main candidates: official=5, independent=79, community=0.
- Pages workflow includes Tech Radar: yes.
- Gemini curator: success=29; fallback=71; ai_main=19; fallback_main=65.
- Section counts: local_ai=12, automation=3, open_source=8, knowledge=4, founder_ideas=10.
- /tech/ render check: knowledge=True; founder_ideas=True.
- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.

## 2026-08-06 - Technology & AI 72h live run

- Tech72h generated_at=2026-08-06T10:03:54.386879+00:00
- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.
- Format: AI Frontier Radar 72h.
- Schedule: once every 3 days; data window: latest 72 hours.
- Active sources: 63 / 84.
- Clean web articles: 575.
- Candidate live: 730; noise bi loai: 15; bai qua han 72h bi loai khoi section chinh: 29.
- Event candidates: 41; GDELT ran_successfully=True; raw=120; ai_filtered=41; rejected_non_ai=79.
- Query estimate: 1,499,178,018 bytes; processed: 1,499,178,018 bytes; bytes_status=known; cap: 2,000,000,000 bytes.
- Published stories: 575; must_read=20; full_link_radar=150.
- Must Read theo source type: {'independent': 17, 'official': 3}.
- Must Read theo category: {'model': 1, 'local_ai': 1, 'tool': 12, 'automation': 1, 'opensource': 1, 'business': 1, 'industry': 1, 'mcp': 1, 'agent': 1}.
- Frontier Watchlist entities: 26; candidates_from_watchlist=111; GLM-5.2 detected=yes.
- Data coverage: active_url_sources=63; active_api_sources=27; active_rss_sources=63; active_sitemap_sources=0; active_watchlist_entities=26; metadata_only_sources=46.
- Source registry P0: configured=31; checked=31; success=31; failed=0; zero_hit=0; missing_critical=[].
- Registry quality: verified_timestamp_ratio=1.0; content_quality_ratio={'full_text': 0.0, 'summary_only': 0.5161, 'metadata_only': 0.4839}; primary/independent/community=27/63/19.
- API candidates: total=124; by_method={'hf_api': 27, 'github_api': 42, 'arxiv_api': 8, 'api': 8}; notes=['profile AMD AI Blog: HTTP Error 404: Not Found', 'profile Intel AI Blog: HTTP Error 403: Forbidden', 'profile Arm AI Blog: The read operation timed out'].
- Input quality: real_candidate_count=730; manual_signal_count=0; weak_metadata_match_count=13; official_org_candidate_count=63.
- candidates_by_method={'github_api': 42, 'hf_api': 27, 'changelog_snapshot': 5, 'api': 8, 'metadata': 4, 'arxiv_api': 8, 'html': 575, 'rss': 27, 'gdelt': 34}; content_quality_mix={'metadata_only': 60, 'summary_only': 95, 'full_text': 575}; remaining CAPTCHA/paywall/JS-only sources=0.
- Source mix main candidates: official=5, independent=80, community=0.
- Pages workflow includes Tech Radar: yes.
- Gemini curator: success=34; fallback=66; ai_main=25; fallback_main=60.
- Section counts: local_ai=12, automation=7, open_source=12, knowledge=4, founder_ideas=10.
- /tech/ render check: knowledge=True; founder_ideas=True.
- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.

## 2026-08-09 - Technology & AI 72h live run

- Tech72h generated_at=2026-08-09T14:03:48.285220+00:00
- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.
- Format: AI Frontier Radar 72h.
- Schedule: once every 3 days; data window: latest 72 hours.
- Active sources: 63 / 84.
- Clean web articles: 361.
- Candidate live: 494; noise bi loai: 21; bai qua han 72h bi loai khoi section chinh: 28.
- Event candidates: 14; GDELT ran_successfully=True; raw=120; ai_filtered=14; rejected_non_ai=106.
- Query estimate: 1,189,195,389 bytes; processed: 1,189,195,389 bytes; bytes_status=known; cap: 2,000,000,000 bytes.
- Published stories: 361; must_read=20; full_link_radar=150.
- Must Read theo source type: {'independent': 15, 'official': 5}.
- Must Read theo category: {'model': 2, 'local_ai': 3, 'tool': 11, 'automation': 1, 'opensource': 1, 'business': 1, 'industry': 1}.
- Frontier Watchlist entities: 26; candidates_from_watchlist=88; GLM-5.2 detected=yes.
- Data coverage: active_url_sources=63; active_api_sources=27; active_rss_sources=63; active_sitemap_sources=0; active_watchlist_entities=26; metadata_only_sources=46.
- Source registry P0: configured=31; checked=31; success=31; failed=0; zero_hit=0; missing_critical=[].
- Registry quality: verified_timestamp_ratio=1.0; content_quality_ratio={'full_text': 0.0, 'summary_only': 0.5122, 'metadata_only': 0.4878}; primary/independent/community=27/63/19.
- API candidates: total=123; by_method={'hf_api': 27, 'github_api': 42, 'arxiv_api': 7, 'api': 8}; notes=['profile AMD AI Blog: HTTP Error 404: Not Found', 'profile Intel AI Blog: HTTP Error 403: Forbidden', 'profile Arm AI Blog: The read operation timed out'].
- Input quality: real_candidate_count=494; manual_signal_count=0; weak_metadata_match_count=12; official_org_candidate_count=66.
- candidates_by_method={'github_api': 42, 'hf_api': 27, 'changelog_snapshot': 5, 'api': 8, 'metadata': 4, 'html': 361, 'rss': 30, 'arxiv_api': 7, 'gdelt': 10}; content_quality_mix={'metadata_only': 60, 'summary_only': 73, 'full_text': 361}; remaining CAPTCHA/paywall/JS-only sources=0.
- Source mix main candidates: official=9, independent=70, community=0.
- Pages workflow includes Tech Radar: yes.
- Gemini curator: success=32; fallback=68; ai_main=20; fallback_main=59.
- Section counts: local_ai=12, automation=7, open_source=12, knowledge=4, founder_ideas=10.
- /tech/ render check: knowledge=True; founder_ideas=True.
- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.

## 2026-08-12 - Technology & AI 72h live run

- Tech72h generated_at=2026-08-12T14:36:27.447428+00:00
- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.
- Format: AI Frontier Radar 72h.
- Schedule: once every 3 days; data window: latest 72 hours.
- Active sources: 63 / 84.
- Clean web articles: 679.
- Candidate live: 828; noise bi loai: 18; bai qua han 72h bi loai khoi section chinh: 24.
- Event candidates: 49; GDELT ran_successfully=True; raw=120; ai_filtered=49; rejected_non_ai=71.
- Query estimate: 1,612,993,690 bytes; processed: 1,612,993,690 bytes; bytes_status=known; cap: 2,000,000,000 bytes.
- Published stories: 679; must_read=20; full_link_radar=150.
- Must Read theo source type: {'independent': 12, 'official': 8}.
- Must Read theo category: {'model': 1, 'local_ai': 1, 'tool': 12, 'automation': 2, 'opensource': 1, 'business': 1, 'industry': 1, 'agent': 1}.
- Frontier Watchlist entities: 26; candidates_from_watchlist=116; GLM-5.2 detected=yes.
- Data coverage: active_url_sources=63; active_api_sources=27; active_rss_sources=63; active_sitemap_sources=0; active_watchlist_entities=26; metadata_only_sources=46.
- Source registry P0: configured=31; checked=31; success=31; failed=0; zero_hit=0; missing_critical=[].
- Registry quality: verified_timestamp_ratio=1.0; content_quality_ratio={'full_text': 0.0, 'summary_only': 0.5203, 'metadata_only': 0.4797}; primary/independent/community=27/63/19.
- API candidates: total=123; by_method={'hf_api': 27, 'github_api': 42, 'arxiv_api': 7, 'api': 8}; notes=['profile AMD AI Blog: HTTP Error 404: Not Found', 'profile Intel AI Blog: HTTP Error 403: Forbidden', 'profile Arm AI Blog: The read operation timed out'].
- Input quality: real_candidate_count=828; manual_signal_count=0; weak_metadata_match_count=14; official_org_candidate_count=61.
- candidates_by_method={'github_api': 42, 'hf_api': 27, 'changelog_snapshot': 5, 'api': 8, 'metadata': 4, 'html': 676, 'rss': 26, 'arxiv_api': 7, 'gdelt': 33}; content_quality_mix={'metadata_only': 59, 'summary_only': 93, 'full_text': 676}; remaining CAPTCHA/paywall/JS-only sources=0.
- Source mix main candidates: official=12, independent=70, community=0.
- Pages workflow includes Tech Radar: yes.
- Gemini curator: success=33; fallback=67; ai_main=22; fallback_main=60.
- Section counts: local_ai=12, automation=9, open_source=12, knowledge=4, founder_ideas=10.
- /tech/ render check: knowledge=True; founder_ideas=True.
- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.

## 2026-08-15 - Technology & AI 72h live run

- Tech72h generated_at=2026-08-15T19:40:12.221293+00:00
- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.
- Format: AI Frontier Radar 72h.
- Schedule: once every 3 days; data window: latest 72 hours.
- Active sources: 63 / 84.
- Clean web articles: 270.
- Candidate live: 426; noise bi loai: 21; bai qua han 72h bi loai khoi section chinh: 30.
- Event candidates: 49; GDELT ran_successfully=True; raw=120; ai_filtered=49; rejected_non_ai=71.
- Query estimate: 1,589,153,776 bytes; processed: 1,589,153,776 bytes; bytes_status=known; cap: 2,000,000,000 bytes.
- Published stories: 270; must_read=20; full_link_radar=150.
- Must Read theo source type: {'independent': 18, 'official': 2}.
- Must Read theo category: {'model': 1, 'local_ai': 1, 'tool': 12, 'opensource': 1, 'business': 2, 'industry': 2, 'agent': 1}.
- Frontier Watchlist entities: 26; candidates_from_watchlist=99; GLM-5.2 detected=yes.
- Data coverage: active_url_sources=63; active_api_sources=27; active_rss_sources=63; active_sitemap_sources=0; active_watchlist_entities=26; metadata_only_sources=46.
- Source registry P0: configured=31; checked=31; success=31; failed=0; zero_hit=0; missing_critical=[].
- Registry quality: verified_timestamp_ratio=1.0; content_quality_ratio={'full_text': 0.0, 'summary_only': 0.5122, 'metadata_only': 0.4878}; primary/independent/community=27/63/19.
- API candidates: total=123; by_method={'hf_api': 27, 'github_api': 42, 'arxiv_api': 7, 'api': 8}; notes=['profile AMD AI Blog: HTTP Error 404: Not Found', 'profile Intel AI Blog: HTTP Error 403: Forbidden', 'profile Arm AI Blog: The read operation timed out'].
- Input quality: real_candidate_count=426; manual_signal_count=0; weak_metadata_match_count=13; official_org_candidate_count=66.
- candidates_by_method={'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'html': 270, 'rss': 30, 'arxiv_api': 7, 'gdelt': 33}; content_quality_mix={'metadata_only': 60, 'summary_only': 96, 'full_text': 270}; remaining CAPTCHA/paywall/JS-only sources=0.
- Source mix main candidates: official=4, independent=75, community=0.
- Pages workflow includes Tech Radar: yes.
- Gemini curator: success=32; fallback=68; ai_main=24; fallback_main=55.
- Section counts: local_ai=12, automation=4, open_source=2, knowledge=3, founder_ideas=10.
- /tech/ render check: knowledge=True; founder_ideas=True.
- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.

## 2026-08-18 - Technology & AI 72h live run

- Tech72h generated_at=2026-08-18T19:47:31.280024+00:00
- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.
- Format: AI Frontier Radar 72h.
- Schedule: once every 3 days; data window: latest 72 hours.
- Active sources: 63 / 84.
- Clean web articles: 519.
- Candidate live: 667; noise bi loai: 17; bai qua han 72h bi loai khoi section chinh: 29.
- Event candidates: 47; GDELT ran_successfully=True; raw=120; ai_filtered=47; rejected_non_ai=73.
- Query estimate: 1,472,943,648 bytes; processed: 1,472,943,648 bytes; bytes_status=known; cap: 2,000,000,000 bytes.
- Published stories: 519; must_read=20; full_link_radar=150.
- Must Read theo source type: {'independent': 14, 'official': 6}.
- Must Read theo category: {'model': 3, 'local_ai': 1, 'tool': 9, 'automation': 2, 'opensource': 1, 'business': 1, 'industry': 1, 'agent': 2}.
- Frontier Watchlist entities: 26; candidates_from_watchlist=98; GLM-5.2 detected=yes.
- Data coverage: active_url_sources=63; active_api_sources=27; active_rss_sources=63; active_sitemap_sources=0; active_watchlist_entities=26; metadata_only_sources=46.
- Source registry P0: configured=31; checked=31; success=31; failed=0; zero_hit=0; missing_critical=[].
- Registry quality: verified_timestamp_ratio=1.0; content_quality_ratio={'full_text': 0.0, 'summary_only': 0.5122, 'metadata_only': 0.4878}; primary/independent/community=27/63/19.
- API candidates: total=123; by_method={'hf_api': 27, 'github_api': 42, 'arxiv_api': 7, 'api': 8}; notes=['profile AMD AI Blog: HTTP Error 404: Not Found', 'profile Intel AI Blog: HTTP Error 403: Forbidden', 'profile Arm AI Blog: The read operation timed out'].
- Input quality: real_candidate_count=667; manual_signal_count=0; weak_metadata_match_count=15; official_org_candidate_count=62.
- candidates_by_method={'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'rss': 27, 'metadata': 4, 'arxiv_api': 7, 'html': 517, 'gdelt': 30}; content_quality_mix={'metadata_only': 60, 'summary_only': 90, 'full_text': 517}; remaining CAPTCHA/paywall/JS-only sources=0.
- Source mix main candidates: official=9, independent=74, community=0.
- Pages workflow includes Tech Radar: yes.
- Gemini curator: success=35; fallback=65; ai_main=25; fallback_main=58.
- Section counts: local_ai=8, automation=11, open_source=12, knowledge=4, founder_ideas=10.
- /tech/ render check: knowledge=True; founder_ideas=True.
- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.
