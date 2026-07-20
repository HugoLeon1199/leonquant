# Tech Source Coverage Matrix

- generated_at_utc: 2026-07-20T20:45:14.695850+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 115
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'rss': 27, 'html': 464, 'arxiv_api': 10, 'gdelt': 15}
- content_quality_mix: {'metadata_only': 59, 'summary_only': 79, 'full_text': 464}
- real_candidate_count: 602
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 87
- official_org_candidate_count: 63
- weak_metadata_match_count: 12
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5317, 'metadata_only': 0.4683}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 102 | method:api=6, method:changelog_snapshot=4, method:github_api=33, method:hf_api=27, method:html=7, method:metadata=4, method:rss=21, quality:full_text=7, quality:metadata_only=57, quality:summary_only=38 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 497 | method:api=2, method:arxiv_api=10, method:changelog_snapshot=1, method:gdelt=15, method:github_api=9, method:html=457, method:rss=3, quality:full_text=457, quality:metadata_only=2, quality:summary_only=38 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 58 | method:api=1, method:arxiv_api=1, method:gdelt=5, method:github_api=24, method:hf_api=15, method:html=12, quality:full_text=12, quality:metadata_only=31, quality:summary_only=15 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 44 | method:api=7, method:gdelt=2, method:hf_api=27, method:html=8, quality:full_text=8, quality:metadata_only=34, quality:summary_only=2 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 178 | method:api=7, method:arxiv_api=4, method:changelog_snapshot=5, method:gdelt=3, method:github_api=2, method:hf_api=10, method:html=125, method:metadata=4, method:rss=18, quality:full_text=125, quality:metadata_only=23, quality:summary_only=30 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 73 | method:arxiv_api=1, method:gdelt=4, method:github_api=11, method:hf_api=2, method:html=52, method:rss=3, quality:full_text=52, quality:metadata_only=5, quality:summary_only=16 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 16 | method:arxiv_api=2, method:gdelt=3, method:html=10, method:rss=1, quality:full_text=10, quality:summary_only=6 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 11 | method:html=11, quality:full_text=11 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 8 | method:arxiv_api=8, quality:summary_only=8 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 7 | method:gdelt=7, quality:summary_only=7 | - | monitor |
