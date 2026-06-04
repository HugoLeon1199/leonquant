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
