# Tech Source Coverage Matrix

- generated_at_utc: 2026-08-22T19:40:35.786134+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 93
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'rss': 30, 'html': 278, 'arxiv_api': 9, 'gdelt': 25}
- content_quality_mix: {'metadata_only': 59, 'summary_only': 91, 'full_text': 278}
- real_candidate_count: 428
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 86
- official_org_candidate_count: 66
- weak_metadata_match_count: 12
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.528, 'metadata_only': 0.472}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 93 | method:api=2, method:changelog_snapshot=4, method:github_api=32, method:hf_api=27, method:metadata=4, method:rss=24, quality:metadata_only=53, quality:summary_only=40 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 332 | method:api=6, method:arxiv_api=9, method:changelog_snapshot=1, method:gdelt=25, method:github_api=10, method:html=278, method:rss=3, quality:full_text=278, quality:metadata_only=6, quality:summary_only=48 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 49 | method:api=6, method:gdelt=1, method:github_api=23, method:hf_api=15, method:html=4, quality:full_text=4, quality:metadata_only=36, quality:summary_only=9 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 37 | method:api=8, method:gdelt=2, method:hf_api=27, quality:metadata_only=35, quality:summary_only=2 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 124 | method:api=2, method:arxiv_api=3, method:changelog_snapshot=5, method:gdelt=4, method:github_api=1, method:hf_api=9, method:html=85, method:metadata=4, method:rss=11, quality:full_text=85, quality:metadata_only=16, quality:summary_only=23 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 50 | method:arxiv_api=3, method:gdelt=14, method:github_api=12, method:hf_api=2, method:html=14, method:rss=5, quality:full_text=14, quality:metadata_only=5, quality:summary_only=31 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 10 | method:gdelt=3, method:html=5, method:rss=2, quality:full_text=5, quality:summary_only=5 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 6 | method:html=6, quality:full_text=6 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 11 | method:arxiv_api=8, method:html=2, method:rss=1, quality:full_text=2, quality:summary_only=9 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 23 | method:gdelt=23, quality:summary_only=23 | - | monitor |
