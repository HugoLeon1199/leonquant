# Tech Source Coverage Matrix

- generated_at_utc: 2026-09-16T17:40:50.461714+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 106
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'rss': 28, 'metadata': 4, 'html': 499, 'gdelt': 33}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 87, 'full_text': 499}
- real_candidate_count: 646
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 77
- official_org_candidate_count: 64
- weak_metadata_match_count: 13
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.4828, 'metadata_only': 0.5172}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 106 | method:api=6, method:changelog_snapshot=4, method:github_api=32, method:hf_api=27, method:html=11, method:metadata=4, method:rss=22, quality:full_text=11, quality:metadata_only=58, quality:summary_only=37 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 537 | method:api=2, method:changelog_snapshot=1, method:gdelt=33, method:github_api=10, method:html=488, method:rss=3, quality:full_text=488, quality:metadata_only=2, quality:summary_only=47 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 45 | method:api=2, method:github_api=23, method:hf_api=16, method:html=4, quality:full_text=4, quality:metadata_only=33, quality:summary_only=8 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 37 | method:api=8, method:hf_api=27, method:html=2, quality:full_text=2, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 173 | method:api=6, method:changelog_snapshot=5, method:gdelt=2, method:github_api=1, method:hf_api=10, method:html=135, method:metadata=4, method:rss=10, quality:full_text=135, quality:metadata_only=21, quality:summary_only=17 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 99 | method:gdelt=22, method:github_api=12, method:hf_api=1, method:html=59, method:rss=5, quality:full_text=59, quality:metadata_only=4, quality:summary_only=36 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 18 | method:gdelt=4, method:html=14, quality:full_text=14, quality:summary_only=4 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 13 | method:html=13, quality:full_text=13 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 31 | method:gdelt=31, quality:summary_only=31 | - | monitor |
