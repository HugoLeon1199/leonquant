# Tech Source Coverage Matrix

- generated_at_utc: 2026-07-12T04:44:25.922142+00:00
- active_url_sources: 7
- active_watchlist_entities: 26
- active_api_sources: 15
- active_rss_sources: 3
- active_sitemap_sources: 1
- metadata_only_sources: 19
- watchlist_checked: 26
- watchlist_hit_count: 115
- candidates_by_method: {'manual_signal': 51, 'hf_api': 27, 'github_api': 30, 'api': 8, 'html': 14, 'arxiv_api': 10, 'gdelt': 28}
- content_quality_mix: {'metadata_only': 104, 'summary_only': 50, 'full_text': 14}
- needs_manual_source_strategy_count: 1

| lane | configured_url_sources | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 2 | 26 | 0 | 1 | 1 | 115 | method:api=8, method:github_api=29, method:hf_api=27, method:manual_signal=51, quality:metadata_only=104, quality:summary_only=11 | low active URL crawl count; watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0 | 0 | 0 | 0 | 45 | method:arxiv_api=10, method:gdelt=28, method:github_api=1, method:html=6, quality:full_text=6, quality:summary_only=39 | low active URL crawl count | add RSS/API/direct metadata strategy |
| china_ai | 1 | 26 | 0 | 1 | 0 | 65 | method:gdelt=1, method:github_api=20, method:hf_api=15, method:manual_signal=29, quality:metadata_only=59, quality:summary_only=6 | - | monitor |
| model_hubs | 0 | 26 | 4 | 0 | 0 | 45 | method:api=8, method:hf_api=27, method:manual_signal=10, quality:metadata_only=45 | - | monitor |
| github_releases | 0 | 26 | 6 | 0 | 0 | 42 | method:github_api=30, method:manual_signal=12, quality:metadata_only=30, quality:summary_only=12 | - | monitor |
| image_video_ai | 0 | 26 | 0 | 0 | 0 | 43 | method:api=8, method:arxiv_api=5, method:gdelt=8, method:hf_api=10, method:html=1, method:manual_signal=11, quality:full_text=1, quality:metadata_only=29, quality:summary_only=13 | - | monitor |
| automation_agents | 0 | 26 | 4 | 0 | 0 | 41 | method:arxiv_api=1, method:gdelt=12, method:github_api=10, method:hf_api=2, method:html=4, method:manual_signal=12, quality:full_text=4, quality:metadata_only=17, quality:summary_only=20 | - | monitor |
| chips_infra | 0 | 0 | 0 | 0 | 0 | 7 | method:arxiv_api=1, method:gdelt=5, method:html=1, quality:full_text=1, quality:summary_only=6 | - | monitor |
| business_funding | 0 | 0 | 0 | 0 | 0 | 0 | - | - | monitor |
| policy_risk | 0 | 0 | 0 | 0 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0 | 1 | 0 | 0 | 10 | method:arxiv_api=10, quality:summary_only=10 | - | monitor |
| community_forums | 1 | 0 | 0 | 1 | 0 | 8 | method:html=8, quality:full_text=8 | - | monitor |
| gdelt | 0 | 0 | 0 | 0 | 0 | 28 | method:gdelt=28, quality:summary_only=28 | - | monitor |

## Needs Manual Source Strategy

- TechCrunch AI: CAPTCHA/paywall in validation; needs RSS-only/manual strategy (https://techcrunch.com/category/artificial-intelligence/)
