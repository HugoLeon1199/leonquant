# Tech Source Coverage Matrix

- generated_at_utc: 2026-07-10T05:11:43.456200+00:00
- active_url_sources: 7
- active_watchlist_entities: 26
- active_api_sources: 15
- active_rss_sources: 3
- active_sitemap_sources: 1
- metadata_only_sources: 19
- watchlist_checked: 26
- watchlist_hit_count: 120
- candidates_by_method: {'manual_signal': 51, 'hf_api': 27, 'github_api': 30, 'api': 8, 'arxiv_api': 10, 'html': 27, 'gdelt': 38}
- content_quality_mix: {'metadata_only': 104, 'summary_only': 60, 'full_text': 27}
- needs_manual_source_strategy_count: 1

| lane | configured_url_sources | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 2 | 26 | 0 | 1 | 1 | 117 | method:api=8, method:github_api=30, method:hf_api=27, method:html=1, method:manual_signal=51, quality:full_text=1, quality:metadata_only=104, quality:summary_only=12 | low active URL crawl count; watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0 | 0 | 0 | 0 | 58 | method:arxiv_api=10, method:gdelt=38, method:html=10, quality:full_text=10, quality:summary_only=48 | low active URL crawl count | add RSS/API/direct metadata strategy |
| china_ai | 1 | 26 | 0 | 1 | 0 | 69 | method:gdelt=3, method:github_api=20, method:hf_api=15, method:html=2, method:manual_signal=29, quality:full_text=2, quality:metadata_only=59, quality:summary_only=8 | - | monitor |
| model_hubs | 0 | 26 | 4 | 0 | 0 | 45 | method:api=8, method:hf_api=27, method:manual_signal=10, quality:metadata_only=45 | - | monitor |
| github_releases | 0 | 26 | 6 | 0 | 0 | 42 | method:github_api=30, method:manual_signal=12, quality:metadata_only=30, quality:summary_only=12 | - | monitor |
| image_video_ai | 0 | 26 | 0 | 0 | 0 | 47 | method:api=8, method:arxiv_api=5, method:gdelt=7, method:hf_api=10, method:html=6, method:manual_signal=11, quality:full_text=6, quality:metadata_only=29, quality:summary_only=12 | - | monitor |
| automation_agents | 0 | 26 | 4 | 0 | 0 | 47 | method:arxiv_api=1, method:gdelt=17, method:github_api=10, method:hf_api=2, method:html=5, method:manual_signal=12, quality:full_text=5, quality:metadata_only=17, quality:summary_only=25 | - | monitor |
| chips_infra | 0 | 0 | 0 | 0 | 0 | 8 | method:arxiv_api=1, method:gdelt=6, method:html=1, quality:full_text=1, quality:summary_only=7 | - | monitor |
| business_funding | 0 | 0 | 0 | 0 | 0 | 0 | - | - | monitor |
| policy_risk | 0 | 0 | 0 | 0 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0 | 1 | 0 | 0 | 10 | method:arxiv_api=10, quality:summary_only=10 | - | monitor |
| community_forums | 1 | 0 | 0 | 1 | 0 | 16 | method:html=16, quality:full_text=16 | - | monitor |
| gdelt | 0 | 0 | 0 | 0 | 0 | 38 | method:gdelt=38, quality:summary_only=38 | - | monitor |

## Needs Manual Source Strategy

- TechCrunch AI: CAPTCHA/paywall in validation; needs RSS-only/manual strategy (https://techcrunch.com/category/artificial-intelligence/)
