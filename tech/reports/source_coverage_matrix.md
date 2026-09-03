# Tech Source Coverage Matrix

- generated_at_utc: 2026-09-03T12:10:31.035503+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 120
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'html': 692, 'rss': 27, 'arxiv_api': 9, 'gdelt': 37}
- content_quality_mix: {'metadata_only': 61, 'summary_only': 98, 'full_text': 692}
- real_candidate_count: 851
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 86
- official_org_candidate_count: 63
- weak_metadata_match_count: 13
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.512, 'metadata_only': 0.488}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 104 | method:api=8, method:changelog_snapshot=4, method:github_api=33, method:hf_api=27, method:html=7, method:metadata=4, method:rss=21, quality:full_text=7, quality:metadata_only=61, quality:summary_only=36 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 744 | method:arxiv_api=9, method:changelog_snapshot=1, method:gdelt=37, method:github_api=9, method:html=685, method:rss=3, quality:full_text=685, quality:summary_only=59 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 43 | method:github_api=23, method:hf_api=15, method:html=5, quality:full_text=5, quality:metadata_only=30, quality:summary_only=8 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 39 | method:api=8, method:gdelt=1, method:hf_api=27, method:html=2, method:rss=1, quality:full_text=2, quality:metadata_only=35, quality:summary_only=2 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 226 | method:api=8, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=12, method:github_api=1, method:hf_api=9, method:html=174, method:metadata=4, method:rss=12, quality:full_text=174, quality:metadata_only=22, quality:summary_only=30 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 131 | method:arxiv_api=2, method:gdelt=20, method:github_api=11, method:hf_api=2, method:html=92, method:rss=4, quality:full_text=92, quality:metadata_only=6, quality:summary_only=33 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 23 | method:arxiv_api=1, method:gdelt=2, method:html=18, method:rss=2, quality:full_text=18, quality:metadata_only=1, quality:summary_only=4 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 19 | method:gdelt=1, method:html=16, method:rss=2, quality:full_text=16, quality:metadata_only=1, quality:summary_only=2 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 11 | method:arxiv_api=9, method:html=1, method:rss=1, quality:full_text=1, quality:summary_only=10 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 32 | method:gdelt=32, quality:summary_only=32 | - | monitor |
