# Tech Source Coverage Matrix

- generated_at_utc: 2026-07-19T14:37:49.577096+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 103
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'html': 369, 'rss': 30, 'gdelt': 26, 'arxiv_api': 8}
- content_quality_mix: {'metadata_only': 59, 'summary_only': 91, 'full_text': 369}
- real_candidate_count: 519
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 85
- official_org_candidate_count: 66
- weak_metadata_match_count: 14
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5242, 'metadata_only': 0.4758}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 99 | method:api=6, method:changelog_snapshot=4, method:github_api=34, method:hf_api=27, method:metadata=4, method:rss=24, quality:metadata_only=57, quality:summary_only=42 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 417 | method:api=2, method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=26, method:github_api=8, method:html=369, method:rss=3, quality:full_text=369, quality:metadata_only=2, quality:summary_only=46 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 55 | method:api=1, method:gdelt=10, method:github_api=25, method:hf_api=15, method:html=4, quality:full_text=4, quality:metadata_only=31, quality:summary_only=20 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 38 | method:api=7, method:gdelt=4, method:hf_api=27, quality:metadata_only=34, quality:summary_only=4 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 146 | method:api=7, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=1, method:github_api=2, method:hf_api=10, method:html=100, method:metadata=4, method:rss=16, quality:full_text=100, quality:metadata_only=23, quality:summary_only=23 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 60 | method:arxiv_api=4, method:gdelt=7, method:github_api=11, method:hf_api=2, method:html=29, method:rss=7, quality:full_text=29, quality:metadata_only=5, quality:summary_only=26 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 21 | method:arxiv_api=1, method:gdelt=3, method:html=16, method:rss=1, quality:full_text=16, quality:summary_only=5 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 5 | method:gdelt=1, method:html=3, method:rss=1, quality:full_text=3, quality:summary_only=2 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 12 | method:arxiv_api=8, method:html=4, quality:full_text=4, quality:summary_only=8 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 16 | method:gdelt=16, quality:summary_only=16 | - | monitor |
