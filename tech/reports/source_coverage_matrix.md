# Tech Source Coverage Matrix

- generated_at_utc: 2026-07-10T03:11:35.956505+00:00
- active_url_sources: 7
- active_watchlist_entities: 26
- active_api_sources: 15
- active_rss_sources: 3
- active_sitemap_sources: 1
- metadata_only_sources: 19
- watchlist_checked: 26
- watchlist_hit_count: 99
- candidates_by_method: {'manual_signal': 51, 'github_api': 24, 'hf_api': 14, 'api': 8, 'gdelt': 27, 'html': 10}
- content_quality_mix: {'metadata_only': 91, 'summary_only': 33, 'full_text': 10}
- needs_manual_source_strategy_count: 1

| lane | configured_url_sources | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 2 | 26 | 0 | 1 | 1 | 97 | method:api=8, method:github_api=24, method:hf_api=14, method:manual_signal=51, quality:metadata_only=91, quality:summary_only=6 | low active URL crawl count; watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0 | 0 | 0 | 0 | 28 | method:gdelt=27, method:html=1, quality:full_text=1, quality:summary_only=27 | low active URL crawl count | add RSS/API/direct metadata strategy |
| china_ai | 1 | 26 | 0 | 1 | 0 | 58 | method:gdelt=3, method:github_api=18, method:hf_api=8, method:manual_signal=29, quality:metadata_only=52, quality:summary_only=6 | - | monitor |
| model_hubs | 0 | 26 | 4 | 0 | 0 | 32 | method:api=8, method:hf_api=14, method:manual_signal=10, quality:metadata_only=32 | - | monitor |
| github_releases | 0 | 26 | 6 | 0 | 0 | 36 | method:github_api=24, method:manual_signal=12, quality:metadata_only=30, quality:summary_only=6 | - | monitor |
| image_video_ai | 0 | 26 | 0 | 0 | 0 | 30 | method:api=8, method:gdelt=5, method:hf_api=5, method:html=1, method:manual_signal=11, quality:full_text=1, quality:metadata_only=24, quality:summary_only=5 | - | monitor |
| automation_agents | 0 | 26 | 4 | 0 | 0 | 36 | method:gdelt=11, method:github_api=6, method:hf_api=1, method:html=6, method:manual_signal=12, quality:full_text=6, quality:metadata_only=16, quality:summary_only=14 | - | monitor |
| chips_infra | 0 | 0 | 0 | 0 | 0 | 6 | method:gdelt=6, quality:summary_only=6 | - | monitor |
| business_funding | 0 | 0 | 0 | 0 | 0 | 0 | - | - | monitor |
| policy_risk | 0 | 0 | 0 | 0 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0 | 1 | 0 | 0 | 0 | - | - | monitor |
| community_forums | 1 | 0 | 0 | 1 | 0 | 9 | method:html=9, quality:full_text=9 | - | monitor |
| gdelt | 0 | 0 | 0 | 0 | 0 | 27 | method:gdelt=27, quality:summary_only=27 | - | monitor |

## Needs Manual Source Strategy

- TechCrunch AI: CAPTCHA/paywall in validation; needs RSS-only/manual strategy (https://techcrunch.com/category/artificial-intelligence/)
