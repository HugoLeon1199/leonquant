# Tech Source Coverage Matrix

- generated_at_utc: 2026-09-17T22:15:36.969763+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 105
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'rss': 27, 'html': 549, 'gdelt': 35}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 88, 'full_text': 549}
- real_candidate_count: 697
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 77
- official_org_candidate_count: 63
- weak_metadata_match_count: 15
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.4828, 'metadata_only': 0.5172}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 104 | method:api=6, method:changelog_snapshot=4, method:github_api=32, method:hf_api=27, method:html=10, method:metadata=4, method:rss=21, quality:full_text=10, quality:metadata_only=58, quality:summary_only=36 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 590 | method:api=2, method:changelog_snapshot=1, method:gdelt=35, method:github_api=10, method:html=539, method:rss=3, quality:full_text=539, quality:metadata_only=2, quality:summary_only=49 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 46 | method:api=2, method:gdelt=4, method:github_api=23, method:hf_api=15, method:html=2, quality:full_text=2, quality:metadata_only=32, quality:summary_only=12 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 35 | method:api=8, method:hf_api=27, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 167 | method:api=6, method:changelog_snapshot=5, method:gdelt=3, method:github_api=1, method:hf_api=10, method:html=131, method:metadata=4, method:rss=7, quality:full_text=131, quality:metadata_only=21, quality:summary_only=15 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 122 | method:gdelt=18, method:github_api=12, method:hf_api=2, method:html=82, method:rss=8, quality:full_text=82, quality:metadata_only=5, quality:summary_only=35 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 17 | method:gdelt=2, method:html=15, quality:full_text=15, quality:summary_only=2 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 8 | method:gdelt=1, method:html=7, quality:full_text=7, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 4 | method:html=2, method:rss=2, quality:full_text=2, quality:summary_only=2 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 31 | method:gdelt=31, quality:summary_only=31 | - | monitor |
