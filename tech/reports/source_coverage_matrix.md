# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-16T17:32:13.295690+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 98
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'rss': 29, 'html': 426, 'gdelt': 39}
- content_quality_mix: {'summary_only': 94, 'metadata_only': 60, 'full_text': 426}
- real_candidate_count: 580
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 77
- official_org_candidate_count: 65
- weak_metadata_match_count: 12
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.4828, 'metadata_only': 0.5172}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 101 | method:api=8, method:changelog_snapshot=4, method:github_api=34, method:hf_api=27, method:html=1, method:metadata=4, method:rss=23, quality:full_text=1, quality:metadata_only=59, quality:summary_only=41 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 476 | method:changelog_snapshot=1, method:gdelt=39, method:github_api=8, method:html=425, method:rss=3, quality:full_text=425, quality:metadata_only=1, quality:summary_only=50 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 45 | method:gdelt=1, method:github_api=24, method:hf_api=15, method:html=4, method:rss=1, quality:full_text=4, quality:metadata_only=30, quality:summary_only=11 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 38 | method:api=8, method:gdelt=1, method:hf_api=27, method:html=1, method:rss=1, quality:full_text=1, quality:metadata_only=35, quality:summary_only=2 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 130 | method:api=8, method:changelog_snapshot=5, method:gdelt=3, method:github_api=1, method:hf_api=9, method:html=89, method:metadata=4, method:rss=11, quality:full_text=89, quality:metadata_only=22, quality:summary_only=19 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 105 | method:gdelt=30, method:github_api=13, method:hf_api=3, method:html=53, method:rss=6, quality:full_text=53, quality:metadata_only=6, quality:summary_only=46 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 19 | method:gdelt=3, method:html=13, method:rss=3, quality:full_text=13, quality:summary_only=6 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 12 | method:gdelt=1, method:html=11, quality:full_text=11, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 5 | method:html=5, quality:full_text=5 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 36 | method:gdelt=36, quality:summary_only=36 | - | monitor |
