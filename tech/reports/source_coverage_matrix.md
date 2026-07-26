# Tech Source Coverage Matrix

- generated_at_utc: 2026-07-26T09:28:21.448989+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 97
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'changelog_snapshot': 5, 'api': 8, 'metadata': 4, 'html': 342, 'rss': 30, 'arxiv_api': 10, 'gdelt': 24}
- content_quality_mix: {'metadata_only': 58, 'summary_only': 92, 'full_text': 342}
- real_candidate_count: 492
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 87
- official_org_candidate_count: 66
- weak_metadata_match_count: 13
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5397, 'metadata_only': 0.4603}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 101 | method:api=8, method:changelog_snapshot=4, method:github_api=34, method:hf_api=27, method:metadata=4, method:rss=24, quality:metadata_only=58, quality:summary_only=43 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 388 | method:arxiv_api=10, method:changelog_snapshot=1, method:gdelt=24, method:github_api=8, method:html=342, method:rss=3, quality:full_text=342, quality:summary_only=46 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 42 | method:gdelt=1, method:github_api=23, method:hf_api=15, method:html=2, method:rss=1, quality:full_text=2, quality:metadata_only=30, quality:summary_only=10 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 38 | method:api=8, method:hf_api=27, method:html=2, method:rss=1, quality:full_text=2, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 148 | method:api=8, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=2, method:github_api=3, method:hf_api=10, method:html=103, method:metadata=4, method:rss=12, quality:full_text=103, quality:metadata_only=23, quality:summary_only=22 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 72 | method:arxiv_api=4, method:gdelt=14, method:github_api=12, method:hf_api=2, method:html=35, method:rss=5, quality:full_text=35, quality:metadata_only=5, quality:summary_only=32 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 17 | method:gdelt=3, method:html=10, method:rss=4, quality:full_text=10, quality:summary_only=7 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 6 | method:html=5, method:rss=1, quality:full_text=5, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 12 | method:arxiv_api=9, method:html=1, method:rss=2, quality:full_text=1, quality:summary_only=11 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 23 | method:gdelt=23, quality:summary_only=23 | - | monitor |
