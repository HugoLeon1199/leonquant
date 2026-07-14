# Tech Source Coverage Matrix

- generated_at_utc: 2026-07-14T09:20:38.693984+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 15
- active_rss_sources: 63
- active_sitemap_sources: 1
- metadata_only_sources: 19
- watchlist_checked: 26
- watchlist_hit_count: 96
- candidates_by_method: {'github_api': 30, 'hf_api': 27, 'api': 8, 'html': 538, 'arxiv_api': 10, 'gdelt': 25}
- content_quality_mix: {'metadata_only': 53, 'summary_only': 47, 'full_text': 538}
- real_candidate_count: 638
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 75
- official_org_candidate_count: 29
- weak_metadata_match_count: 7
- needs_manual_source_strategy_count: 1

| lane | configured_url_sources | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 2 | 26 | 0 | 1 | 1 | 73 | method:api=8, method:github_api=28, method:hf_api=27, method:html=10, quality:full_text=10, quality:metadata_only=53, quality:summary_only=10 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0 | 0 | 0 | 0 | 565 | method:arxiv_api=10, method:gdelt=25, method:github_api=2, method:html=528, quality:full_text=528, quality:summary_only=37 | - | monitor |
| china_ai | 1 | 26 | 0 | 1 | 0 | 40 | method:gdelt=1, method:github_api=20, method:hf_api=16, method:html=3, quality:full_text=3, quality:metadata_only=31, quality:summary_only=6 | - | monitor |
| model_hubs | 0 | 26 | 4 | 0 | 0 | 35 | method:api=8, method:hf_api=27, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 26 | 6 | 0 | 0 | 30 | method:github_api=30, quality:metadata_only=18, quality:summary_only=12 | - | monitor |
| image_video_ai | 0 | 26 | 0 | 0 | 0 | 135 | method:api=8, method:arxiv_api=5, method:gdelt=2, method:hf_api=10, method:html=110, quality:full_text=110, quality:metadata_only=18, quality:summary_only=7 | - | monitor |
| automation_agents | 0 | 26 | 4 | 0 | 0 | 92 | method:arxiv_api=1, method:gdelt=18, method:github_api=10, method:hf_api=1, method:html=62, quality:full_text=62, quality:metadata_only=4, quality:summary_only=26 | - | monitor |
| chips_infra | 0 | 0 | 0 | 0 | 0 | 14 | method:gdelt=1, method:html=13, quality:full_text=13, quality:summary_only=1 | - | monitor |
| business_funding | 0 | 0 | 0 | 0 | 0 | 15 | method:gdelt=1, method:html=14, quality:full_text=14, quality:summary_only=1 | - | monitor |
| policy_risk | 0 | 0 | 0 | 0 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0 | 1 | 0 | 0 | 12 | method:arxiv_api=9, method:html=3, quality:full_text=3, quality:summary_only=9 | - | monitor |
| community_forums | 1 | 0 | 0 | 1 | 0 | 0 | - | - | monitor |
| gdelt | 0 | 0 | 0 | 0 | 0 | 22 | method:gdelt=22, quality:summary_only=22 | - | monitor |

## Needs Manual Source Strategy

- TechCrunch AI: CAPTCHA/paywall in validation; needs RSS-only/manual strategy (https://techcrunch.com/category/artificial-intelligence/)
