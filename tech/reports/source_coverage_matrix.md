# Tech Source Coverage Matrix

- generated_at_utc: 2026-07-18T09:21:47.030549+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 70
- candidates_by_method: {'github_api': 30, 'hf_api': 14, 'api': 8, 'changelog_snapshot': 5, 'metadata': 3, 'rss': 33, 'arxiv_api': 8, 'gdelt': 20, 'html': 377}
- content_quality_mix: {'metadata_only': 48, 'summary_only': 73, 'full_text': 377}
- real_candidate_count: 498
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 60
- official_org_candidate_count: 61
- weak_metadata_match_count: 8
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5248, 'metadata_only': 0.4752}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 80 | method:api=6, method:changelog_snapshot=4, method:github_api=25, method:hf_api=14, method:html=1, method:metadata=3, method:rss=27, quality:full_text=1, quality:metadata_only=46, quality:summary_only=33 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 415 | method:api=2, method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=20, method:github_api=5, method:html=376, method:rss=3, quality:full_text=376, quality:metadata_only=2, quality:summary_only=37 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 34 | method:api=1, method:gdelt=1, method:github_api=19, method:hf_api=8, method:html=5, quality:full_text=5, quality:metadata_only=24, quality:summary_only=5 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 22 | method:api=7, method:hf_api=14, method:html=1, quality:full_text=1, quality:metadata_only=21 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 30 | method:github_api=30, quality:metadata_only=18, quality:summary_only=12 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 150 | method:api=7, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=5, method:github_api=1, method:hf_api=5, method:html=107, method:metadata=3, method:rss=16, quality:full_text=107, quality:metadata_only=18, quality:summary_only=25 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 59 | method:arxiv_api=4, method:gdelt=7, method:github_api=7, method:hf_api=1, method:html=32, method:rss=8, quality:full_text=32, quality:metadata_only=4, quality:summary_only=23 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 14 | method:arxiv_api=1, method:gdelt=4, method:html=6, method:rss=3, quality:full_text=6, quality:metadata_only=2, quality:summary_only=6 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 3 | method:html=2, method:rss=1, quality:full_text=2, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 9 | method:arxiv_api=8, method:html=1, quality:full_text=1, quality:summary_only=8 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 19 | method:gdelt=19, quality:summary_only=19 | - | monitor |
