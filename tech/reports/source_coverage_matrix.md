# Tech Source Coverage Matrix

- generated_at_utc: 2026-07-12T10:06:37.890394+00:00
- active_url_sources: 7
- active_watchlist_entities: 26
- active_api_sources: 15
- active_rss_sources: 3
- active_sitemap_sources: 1
- metadata_only_sources: 19
- watchlist_checked: 26
- watchlist_hit_count: 63
- candidates_by_method: {'github_api': 30, 'hf_api': 27, 'api': 8, 'arxiv_api': 10, 'html': 3}
- content_quality_mix: {'metadata_only': 53, 'summary_only': 22, 'full_text': 3}
- real_candidate_count: 78
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 75
- official_org_candidate_count: 27
- weak_metadata_match_count: 7
- needs_manual_source_strategy_count: 1

| lane | configured_url_sources | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 2 | 26 | 0 | 1 | 1 | 65 | method:api=8, method:github_api=29, method:hf_api=27, method:html=1, quality:full_text=1, quality:metadata_only=53, quality:summary_only=11 | low active URL crawl count; watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0 | 0 | 0 | 0 | 13 | method:arxiv_api=10, method:github_api=1, method:html=2, quality:full_text=2, quality:summary_only=11 | low active URL crawl count | add RSS/API/direct metadata strategy |
| china_ai | 1 | 26 | 0 | 1 | 0 | 36 | method:github_api=20, method:hf_api=15, method:html=1, quality:full_text=1, quality:metadata_only=30, quality:summary_only=5 | - | monitor |
| model_hubs | 0 | 26 | 4 | 0 | 0 | 35 | method:api=8, method:hf_api=27, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 26 | 6 | 0 | 0 | 31 | method:github_api=30, method:html=1, quality:full_text=1, quality:metadata_only=18, quality:summary_only=12 | - | monitor |
| image_video_ai | 0 | 26 | 0 | 0 | 0 | 23 | method:api=8, method:arxiv_api=5, method:hf_api=10, quality:metadata_only=18, quality:summary_only=5 | - | monitor |
| automation_agents | 0 | 26 | 4 | 0 | 0 | 15 | method:arxiv_api=1, method:github_api=10, method:hf_api=2, method:html=2, quality:full_text=2, quality:metadata_only=5, quality:summary_only=8 | - | monitor |
| chips_infra | 0 | 0 | 0 | 0 | 0 | 1 | method:arxiv_api=1, quality:summary_only=1 | - | monitor |
| business_funding | 0 | 0 | 0 | 0 | 0 | 0 | - | - | monitor |
| policy_risk | 0 | 0 | 0 | 0 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0 | 1 | 0 | 0 | 10 | method:arxiv_api=10, quality:summary_only=10 | - | monitor |
| community_forums | 1 | 0 | 0 | 1 | 0 | 0 | - | - | monitor |
| gdelt | 0 | 0 | 0 | 0 | 0 | 0 | - | - | monitor |

## Needs Manual Source Strategy

- TechCrunch AI: CAPTCHA/paywall in validation; needs RSS-only/manual strategy (https://techcrunch.com/category/artificial-intelligence/)
