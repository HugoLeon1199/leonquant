# Tech Source Coverage Matrix

- generated_at_utc: 2026-09-26T22:01:17.295855+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 87
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'html': 293, 'rss': 30, 'gdelt': 32}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 88, 'full_text': 293}
- real_candidate_count: 441
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 77
- official_org_candidate_count: 66
- weak_metadata_match_count: 16
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.4828, 'metadata_only': 0.5172}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 96 | method:api=3, method:changelog_snapshot=4, method:github_api=34, method:hf_api=27, method:metadata=4, method:rss=24, quality:metadata_only=55, quality:summary_only=41 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 342 | method:api=5, method:changelog_snapshot=1, method:gdelt=32, method:github_api=8, method:html=293, method:rss=3, quality:full_text=293, quality:metadata_only=5, quality:summary_only=44 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 51 | method:api=5, method:gdelt=1, method:github_api=25, method:hf_api=17, method:html=1, method:rss=2, quality:full_text=1, quality:metadata_only=37, quality:summary_only=13 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 37 | method:api=8, method:hf_api=27, method:html=1, method:rss=1, quality:full_text=1, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 111 | method:api=3, method:changelog_snapshot=5, method:github_api=1, method:hf_api=10, method:html=78, method:metadata=4, method:rss=10, quality:full_text=78, quality:metadata_only=18, quality:summary_only=15 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 82 | method:gdelt=28, method:github_api=12, method:html=40, method:rss=2, quality:full_text=40, quality:metadata_only=3, quality:summary_only=39 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 7 | method:gdelt=1, method:html=4, method:rss=2, quality:full_text=4, quality:summary_only=3 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 6 | method:html=6, quality:full_text=6 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 5 | method:gdelt=1, method:rss=4, quality:summary_only=5 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 31 | method:gdelt=31, quality:summary_only=31 | - | monitor |
