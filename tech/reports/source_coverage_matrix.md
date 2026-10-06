# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-06T23:08:07.274545+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 110
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'rss': 26, 'html': 601, 'arxiv_api': 7, 'gdelt': 33}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 92, 'full_text': 601}
- real_candidate_count: 753
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 62
- weak_metadata_match_count: 12
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5122, 'metadata_only': 0.4878}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 107 | method:api=8, method:changelog_snapshot=4, method:github_api=36, method:hf_api=27, method:html=8, method:metadata=4, method:rss=20, quality:full_text=8, quality:metadata_only=60, quality:summary_only=39 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 643 | method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=33, method:github_api=6, method:html=593, method:rss=3, quality:full_text=593, quality:summary_only=50 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 46 | method:gdelt=1, method:github_api=26, method:hf_api=16, method:html=3, quality:full_text=3, quality:metadata_only=31, quality:summary_only=12 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 35 | method:api=8, method:hf_api=27, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 202 | method:api=8, method:arxiv_api=3, method:changelog_snapshot=5, method:gdelt=6, method:github_api=2, method:hf_api=9, method:html=154, method:metadata=4, method:rss=11, quality:full_text=154, quality:metadata_only=22, quality:summary_only=26 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 119 | method:arxiv_api=4, method:gdelt=19, method:github_api=10, method:hf_api=2, method:html=79, method:rss=5, quality:full_text=79, quality:metadata_only=5, quality:summary_only=35 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 15 | method:gdelt=2, method:html=12, method:rss=1, quality:full_text=12, quality:summary_only=3 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 8 | method:gdelt=1, method:html=6, method:rss=1, quality:full_text=6, quality:summary_only=2 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 9 | method:arxiv_api=7, method:html=2, quality:full_text=2, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 28 | method:gdelt=28, quality:summary_only=28 | - | monitor |
