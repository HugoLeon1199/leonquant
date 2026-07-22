# Tech Source Coverage Matrix

- generated_at_utc: 2026-07-22T15:20:41.160643+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 113
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'html': 704, 'rss': 29, 'arxiv_api': 8, 'gdelt': 32}
- content_quality_mix: {'metadata_only': 58, 'summary_only': 97, 'full_text': 704}
- real_candidate_count: 859
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 85
- official_org_candidate_count: 65
- weak_metadata_match_count: 14
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5323, 'metadata_only': 0.4677}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 105 | method:api=6, method:changelog_snapshot=4, method:github_api=34, method:hf_api=27, method:html=7, method:metadata=4, method:rss=23, quality:full_text=7, quality:metadata_only=56, quality:summary_only=42 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 751 | method:api=2, method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=32, method:github_api=8, method:html=697, method:rss=3, quality:full_text=697, quality:metadata_only=2, quality:summary_only=52 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 49 | method:api=1, method:gdelt=1, method:github_api=24, method:hf_api=16, method:html=7, quality:full_text=7, quality:metadata_only=32, quality:summary_only=10 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 41 | method:api=7, method:gdelt=1, method:hf_api=27, method:html=5, method:rss=1, quality:full_text=5, quality:metadata_only=34, quality:summary_only=2 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 210 | method:api=7, method:arxiv_api=2, method:changelog_snapshot=5, method:gdelt=3, method:github_api=2, method:hf_api=9, method:html=164, method:metadata=4, method:rss=14, quality:full_text=164, quality:metadata_only=21, quality:summary_only=25 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 160 | method:arxiv_api=3, method:gdelt=25, method:github_api=12, method:hf_api=2, method:html=110, method:rss=8, quality:full_text=110, quality:metadata_only=5, quality:summary_only=45 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 20 | method:gdelt=2, method:html=15, method:rss=3, quality:full_text=15, quality:summary_only=5 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 16 | method:html=16, quality:full_text=16 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 9 | method:arxiv_api=8, method:html=1, quality:full_text=1, quality:summary_only=8 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 30 | method:gdelt=30, quality:summary_only=30 | - | monitor |
