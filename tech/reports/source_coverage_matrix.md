# Tech Source Coverage Matrix

- generated_at_utc: 2026-07-14T20:34:59.755443+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 15
- active_rss_sources: 63
- active_sitemap_sources: 1
- metadata_only_sources: 19
- watchlist_checked: 26
- watchlist_hit_count: 98
- candidates_by_method: {'github_api': 30, 'hf_api': 27, 'api': 8, 'html': 489, 'arxiv_api': 10, 'gdelt': 36}
- content_quality_mix: {'summary_only': 58, 'metadata_only': 53, 'full_text': 489}
- real_candidate_count: 600
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 75
- official_org_candidate_count: 28
- weak_metadata_match_count: 9
- needs_manual_source_strategy_count: 1

| lane | configured_url_sources | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 2 | 26 | 0 | 1 | 1 | 73 | method:api=8, method:github_api=28, method:hf_api=27, method:html=10, quality:full_text=10, quality:metadata_only=53, quality:summary_only=10 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0 | 0 | 0 | 0 | 527 | method:arxiv_api=10, method:gdelt=36, method:github_api=2, method:html=479, quality:full_text=479, quality:summary_only=48 | - | monitor |
| china_ai | 1 | 26 | 0 | 1 | 0 | 43 | method:gdelt=4, method:github_api=20, method:hf_api=15, method:html=4, quality:full_text=4, quality:metadata_only=30, quality:summary_only=9 | - | monitor |
| model_hubs | 0 | 26 | 4 | 0 | 0 | 35 | method:api=8, method:hf_api=27, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 26 | 6 | 0 | 0 | 30 | method:github_api=30, quality:metadata_only=18, quality:summary_only=12 | - | monitor |
| image_video_ai | 0 | 26 | 0 | 0 | 0 | 154 | method:api=8, method:arxiv_api=5, method:gdelt=4, method:hf_api=10, method:html=127, quality:full_text=127, quality:metadata_only=18, quality:summary_only=9 | - | monitor |
| automation_agents | 0 | 26 | 4 | 0 | 0 | 95 | method:arxiv_api=1, method:gdelt=19, method:github_api=10, method:hf_api=2, method:html=63, quality:full_text=63, quality:metadata_only=5, quality:summary_only=27 | - | monitor |
| chips_infra | 0 | 0 | 0 | 0 | 0 | 21 | method:gdelt=4, method:html=17, quality:full_text=17, quality:summary_only=4 | - | monitor |
| business_funding | 0 | 0 | 0 | 0 | 0 | 9 | method:gdelt=1, method:html=8, quality:full_text=8, quality:summary_only=1 | - | monitor |
| policy_risk | 0 | 0 | 0 | 0 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0 | 1 | 0 | 0 | 11 | method:arxiv_api=9, method:html=2, quality:full_text=2, quality:summary_only=9 | - | monitor |
| community_forums | 1 | 0 | 0 | 1 | 0 | 0 | - | - | monitor |
| gdelt | 0 | 0 | 0 | 0 | 0 | 30 | method:gdelt=30, quality:summary_only=30 | - | monitor |

## Needs Manual Source Strategy

- TechCrunch AI: CAPTCHA/paywall in validation; needs RSS-only/manual strategy (https://techcrunch.com/category/artificial-intelligence/)
