# Tech Source Coverage Matrix

- generated_at_utc: 2026-09-01T17:23:32.747015+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 105
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'rss': 27, 'metadata': 4, 'arxiv_api': 8, 'html': 476, 'gdelt': 30}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 91, 'full_text': 476}
- real_candidate_count: 627
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 85
- official_org_candidate_count: 63
- weak_metadata_match_count: 11
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5161, 'metadata_only': 0.4839}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 100 | method:api=4, method:changelog_snapshot=4, method:github_api=34, method:hf_api=27, method:html=6, method:metadata=4, method:rss=21, quality:full_text=6, quality:metadata_only=56, quality:summary_only=38 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 524 | method:api=4, method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=30, method:github_api=8, method:html=470, method:rss=3, quality:full_text=470, quality:metadata_only=4, quality:summary_only=50 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 48 | method:api=4, method:arxiv_api=1, method:gdelt=2, method:github_api=24, method:hf_api=15, method:rss=2, quality:metadata_only=34, quality:summary_only=14 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 41 | method:api=8, method:gdelt=3, method:hf_api=27, method:html=1, method:rss=2, quality:full_text=1, quality:metadata_only=35, quality:summary_only=5 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 168 | method:api=4, method:arxiv_api=2, method:changelog_snapshot=5, method:gdelt=8, method:github_api=1, method:hf_api=10, method:html=123, method:metadata=4, method:rss=11, quality:full_text=123, quality:metadata_only=19, quality:summary_only=26 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 93 | method:arxiv_api=1, method:gdelt=13, method:github_api=11, method:hf_api=1, method:html=63, method:rss=4, quality:full_text=63, quality:metadata_only=5, quality:summary_only=25 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 16 | method:arxiv_api=1, method:gdelt=4, method:html=10, method:rss=1, quality:full_text=10, quality:summary_only=6 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 16 | method:html=15, method:rss=1, quality:full_text=15, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 7 | method:arxiv_api=6, method:rss=1, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 25 | method:gdelt=25, quality:summary_only=25 | - | monitor |
