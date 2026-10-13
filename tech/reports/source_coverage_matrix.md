# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-13T19:55:34.926782+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 109
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'rss': 27, 'changelog_snapshot': 5, 'metadata': 4, 'html': 545, 'gdelt': 35, 'arxiv_api': 10}
- content_quality_mix: {'metadata_only': 61, 'summary_only': 97, 'full_text': 545}
- real_candidate_count: 703
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 87
- official_org_candidate_count: 62
- weak_metadata_match_count: 16
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5159, 'metadata_only': 0.4841}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 106 | method:api=7, method:changelog_snapshot=4, method:github_api=34, method:hf_api=27, method:html=9, method:metadata=4, method:rss=21, quality:full_text=9, quality:metadata_only=60, quality:summary_only=37 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 594 | method:api=1, method:arxiv_api=10, method:changelog_snapshot=1, method:gdelt=35, method:github_api=8, method:html=536, method:rss=3, quality:full_text=536, quality:metadata_only=1, quality:summary_only=57 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 46 | method:api=1, method:gdelt=2, method:github_api=27, method:hf_api=15, method:html=1, quality:full_text=1, quality:metadata_only=31, quality:summary_only=14 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 39 | method:api=8, method:hf_api=27, method:html=4, quality:full_text=4, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 185 | method:api=7, method:arxiv_api=2, method:changelog_snapshot=5, method:gdelt=2, method:github_api=1, method:hf_api=9, method:html=145, method:metadata=4, method:rss=10, quality:full_text=145, quality:metadata_only=21, quality:summary_only=19 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 109 | method:arxiv_api=2, method:gdelt=25, method:github_api=9, method:hf_api=3, method:html=67, method:rss=3, quality:full_text=67, quality:metadata_only=6, quality:summary_only=36 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 23 | method:gdelt=3, method:html=16, method:rss=4, quality:full_text=16, quality:metadata_only=1, quality:summary_only=6 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 10 | method:html=10, quality:full_text=10 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 13 | method:arxiv_api=10, method:html=3, quality:full_text=3, quality:summary_only=10 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 33 | method:gdelt=33, quality:summary_only=33 | - | monitor |
