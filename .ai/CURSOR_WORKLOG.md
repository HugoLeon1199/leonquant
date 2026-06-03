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
