# Tech Source Coverage Matrix

- generated_at_utc: 2026-08-30T12:58:59.100317+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 101
- candidates_by_method: {'github_api': 42, 'hf_api': 26, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'html': 383, 'rss': 30, 'gdelt': 25, 'arxiv_api': 9}
- content_quality_mix: {'metadata_only': 58, 'summary_only': 91, 'full_text': 383}
- real_candidate_count: 532
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 85
- official_org_candidate_count: 64
- weak_metadata_match_count: 13
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5323, 'metadata_only': 0.4677}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 94 | method:api=2, method:changelog_snapshot=4, method:github_api=34, method:hf_api=26, method:metadata=4, method:rss=24, quality:metadata_only=52, quality:summary_only=42 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 435 | method:api=6, method:arxiv_api=9, method:changelog_snapshot=1, method:gdelt=25, method:github_api=8, method:html=383, method:rss=3, quality:full_text=383, quality:metadata_only=6, quality:summary_only=46 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 49 | method:api=6, method:gdelt=2, method:github_api=24, method:hf_api=15, method:html=2, quality:full_text=2, quality:metadata_only=36, quality:summary_only=11 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 36 | method:api=8, method:gdelt=2, method:hf_api=26, quality:metadata_only=34, quality:summary_only=2 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 149 | method:api=2, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=4, method:github_api=1, method:hf_api=9, method:html=112, method:metadata=4, method:rss=11, quality:full_text=112, quality:metadata_only=16, quality:summary_only=21 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 64 | method:arxiv_api=4, method:gdelt=8, method:github_api=11, method:hf_api=1, method:html=37, method:rss=3, quality:full_text=37, quality:metadata_only=4, quality:summary_only=23 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 15 | method:gdelt=7, method:html=7, method:rss=1, quality:full_text=7, quality:summary_only=8 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 8 | method:html=7, method:rss=1, quality:full_text=7, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 13 | method:arxiv_api=9, method:gdelt=1, method:html=1, method:rss=2, quality:full_text=1, quality:summary_only=12 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 19 | method:gdelt=19, quality:summary_only=19 | - | monitor |
