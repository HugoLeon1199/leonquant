# Tech Source Coverage Matrix

- generated_at_utc: 2026-09-22T17:42:00.972333+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 100
- candidates_by_method: {'github_api': 42, 'hf_api': 26, 'api': 8, 'changelog_snapshot': 5, 'rss': 27, 'metadata': 4, 'html': 470, 'gdelt': 26}
- content_quality_mix: {'summary_only': 79, 'metadata_only': 59, 'full_text': 470}
- real_candidate_count: 608
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 76
- official_org_candidate_count: 63
- weak_metadata_match_count: 15
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.487, 'metadata_only': 0.513}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 104 | method:api=6, method:changelog_snapshot=4, method:github_api=34, method:hf_api=26, method:html=9, method:metadata=4, method:rss=21, quality:full_text=9, quality:metadata_only=57, quality:summary_only=38 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 501 | method:api=2, method:changelog_snapshot=1, method:gdelt=26, method:github_api=8, method:html=461, method:rss=3, quality:full_text=461, quality:metadata_only=2, quality:summary_only=38 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 50 | method:api=2, method:gdelt=3, method:github_api=24, method:hf_api=16, method:html=4, method:rss=1, quality:full_text=4, quality:metadata_only=33, quality:summary_only=13 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 35 | method:api=8, method:hf_api=26, method:rss=1, quality:metadata_only=34, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 139 | method:api=6, method:changelog_snapshot=5, method:gdelt=2, method:github_api=1, method:hf_api=10, method:html=101, method:metadata=4, method:rss=10, quality:full_text=101, quality:metadata_only=21, quality:summary_only=17 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 88 | method:gdelt=19, method:github_api=12, method:html=55, method:rss=2, quality:full_text=55, quality:metadata_only=3, quality:summary_only=30 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 15 | method:html=15, quality:full_text=15 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 11 | method:html=11, quality:full_text=11 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 5 | method:html=3, method:rss=2, quality:full_text=3, quality:summary_only=2 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 23 | method:gdelt=23, quality:summary_only=23 | - | monitor |
