# Tech Source Coverage Matrix

- generated_at_utc: 2026-07-30T20:38:53.091177+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 102
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'changelog_snapshot': 5, 'api': 8, 'metadata': 4, 'rss': 25, 'html': 503, 'arxiv_api': 8, 'gdelt': 36}
- content_quality_mix: {'summary_only': 95, 'metadata_only': 60, 'full_text': 503}
- real_candidate_count: 658
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 85
- official_org_candidate_count: 60
- weak_metadata_match_count: 14
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5161, 'metadata_only': 0.4839}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 103 | method:api=7, method:changelog_snapshot=4, method:github_api=33, method:hf_api=27, method:html=9, method:metadata=4, method:rss=19, quality:full_text=9, quality:metadata_only=59, quality:summary_only=35 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 552 | method:api=1, method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=36, method:github_api=9, method:html=494, method:rss=3, quality:full_text=494, quality:metadata_only=1, quality:summary_only=57 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 43 | method:api=1, method:gdelt=1, method:github_api=22, method:hf_api=15, method:html=4, quality:full_text=4, quality:metadata_only=31, quality:summary_only=8 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 35 | method:api=8, method:hf_api=27, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 162 | method:api=7, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=2, method:github_api=3, method:hf_api=10, method:html=116, method:metadata=4, method:rss=14, quality:full_text=116, quality:metadata_only=22, quality:summary_only=24 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 127 | method:arxiv_api=4, method:gdelt=25, method:github_api=12, method:hf_api=2, method:html=80, method:rss=4, quality:full_text=80, quality:metadata_only=5, quality:summary_only=42 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 23 | method:arxiv_api=1, method:gdelt=4, method:html=16, method:rss=2, quality:full_text=16, quality:metadata_only=1, quality:summary_only=6 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 10 | method:html=9, method:rss=1, quality:full_text=9, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 12 | method:arxiv_api=7, method:html=4, method:rss=1, quality:full_text=4, quality:summary_only=8 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 35 | method:gdelt=35, quality:summary_only=35 | - | monitor |
