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
