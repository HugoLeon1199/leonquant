# Tech Source Coverage Matrix

- generated_at_utc: 2026-08-03T10:54:40.025660+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 101
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'changelog_snapshot': 5, 'api': 8, 'metadata': 4, 'html': 405, 'rss': 30, 'arxiv_api': 10, 'gdelt': 14}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 80, 'full_text': 405}
- real_candidate_count: 545
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 87
- official_org_candidate_count: 66
- weak_metadata_match_count: 14
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5238, 'metadata_only': 0.4762}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 98 | method:api=4, method:changelog_snapshot=4, method:github_api=35, method:hf_api=27, method:metadata=4, method:rss=24, quality:metadata_only=56, quality:summary_only=42 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 444 | method:api=4, method:arxiv_api=10, method:changelog_snapshot=1, method:gdelt=14, method:github_api=7, method:html=405, method:rss=3, quality:full_text=405, quality:metadata_only=4, quality:summary_only=35 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 49 | method:api=3, method:gdelt=1, method:github_api=23, method:hf_api=16, method:html=5, method:rss=1, quality:full_text=5, quality:metadata_only=34, quality:summary_only=10 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 37 | method:api=7, method:hf_api=27, method:html=3, quality:full_text=3, quality:metadata_only=34 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 171 | method:api=5, method:arxiv_api=2, method:changelog_snapshot=5, method:gdelt=2, method:github_api=3, method:hf_api=11, method:html=124, method:metadata=4, method:rss=15, quality:full_text=124, quality:metadata_only=21, quality:summary_only=26 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 71 | method:arxiv_api=4, method:gdelt=8, method:github_api=13, method:html=40, method:rss=6, quality:full_text=40, quality:metadata_only=3, quality:summary_only=28 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 7 | method:html=5, method:rss=2, quality:full_text=5, quality:metadata_only=1, quality:summary_only=1 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 7 | method:gdelt=1, method:html=5, method:rss=1, quality:full_text=5, quality:summary_only=2 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 10 | method:arxiv_api=10, quality:summary_only=10 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 13 | method:gdelt=13, quality:summary_only=13 | - | monitor |
