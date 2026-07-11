# Tech Source Coverage Matrix

- generated_at_utc: 2026-07-11T14:35:15.253515+00:00
- active_url_sources: 7
- active_watchlist_entities: 26
- active_api_sources: 15
- active_rss_sources: 3
- active_sitemap_sources: 1
- metadata_only_sources: 19
- watchlist_checked: 26
- watchlist_hit_count: 121
- candidates_by_method: {'manual_signal': 51, 'hf_api': 27, 'github_api': 30, 'api': 8, 'html': 24, 'arxiv_api': 10, 'gdelt': 38}
- content_quality_mix: {'metadata_only': 104, 'summary_only': 60, 'full_text': 24}
- needs_manual_source_strategy_count: 1

| lane | configured_url_sources | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 2 | 26 | 0 | 1 | 1 | 116 | method:api=8, method:github_api=30, method:hf_api=27, method:manual_signal=51, quality:metadata_only=104, quality:summary_only=12 | low active URL crawl count; watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0 | 0 | 0 | 0 | 58 | method:arxiv_api=10, method:gdelt=38, method:html=10, quality:full_text=10, quality:summary_only=48 | low active URL crawl count | add RSS/API/direct metadata strategy |
| china_ai | 1 | 26 | 0 | 1 | 0 | 67 | method:gdelt=2, method:github_api=20, method:hf_api=16, method:manual_signal=29, quality:metadata_only=60, quality:summary_only=7 | - | monitor |
| model_hubs | 0 | 26 | 4 | 0 | 0 | 45 | method:api=8, method:hf_api=27, method:manual_signal=10, quality:metadata_only=45 | - | monitor |
| github_releases | 0 | 26 | 6 | 0 | 0 | 42 | method:github_api=30, method:manual_signal=12, quality:metadata_only=30, quality:summary_only=12 | - | monitor |
| image_video_ai | 0 | 26 | 0 | 0 | 0 | 47 | method:api=8, method:arxiv_api=5, method:gdelt=9, method:hf_api=10, method:html=4, method:manual_signal=11, quality:full_text=4, quality:metadata_only=29, quality:summary_only=14 | - | monitor |
| automation_agents | 0 | 26 | 4 | 0 | 0 | 53 | method:arxiv_api=1, method:gdelt=20, method:github_api=10, method:hf_api=1, method:html=9, method:manual_signal=12, quality:full_text=9, quality:metadata_only=16, quality:summary_only=28 | - | monitor |
| chips_infra | 0 | 0 | 0 | 0 | 0 | 5 | method:arxiv_api=1, method:gdelt=4, quality:summary_only=5 | - | monitor |
| business_funding | 0 | 0 | 0 | 0 | 0 | 0 | - | - | monitor |
| policy_risk | 0 | 0 | 0 | 0 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0 | 1 | 0 | 0 | 10 | method:arxiv_api=10, quality:summary_only=10 | - | monitor |
| community_forums | 1 | 0 | 0 | 1 | 0 | 14 | method:html=14, quality:full_text=14 | - | monitor |
| gdelt | 0 | 0 | 0 | 0 | 0 | 38 | method:gdelt=38, quality:summary_only=38 | - | monitor |

## Needs Manual Source Strategy

- TechCrunch AI: CAPTCHA/paywall in validation; needs RSS-only/manual strategy (https://techcrunch.com/category/artificial-intelligence/)
