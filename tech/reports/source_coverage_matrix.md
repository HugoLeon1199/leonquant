# Tech Source Coverage Matrix

- generated_at_utc: 2026-11-27T09:45:35.981589+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 116
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'html': 567, 'arxiv_api': 7, 'rss': 30, 'gdelt': 45}
- content_quality_mix: {'metadata_only': 61, 'summary_only': 107, 'full_text': 567}
- real_candidate_count: 735
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 63
- weak_metadata_match_count: 15
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5041, 'metadata_only': 0.4959}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 101 | method:api=6, method:changelog_snapshot=4, method:github_api=35, method:hf_api=27, method:html=1, method:metadata=4, method:rss=24, quality:full_text=1, quality:metadata_only=59, quality:summary_only=41 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 631 | method:api=2, method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=45, method:github_api=7, method:html=566, method:rss=3, quality:full_text=566, quality:metadata_only=2, quality:summary_only=63 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 46 | method:api=1, method:gdelt=1, method:github_api=22, method:hf_api=16, method:html=5, method:rss=1, quality:full_text=5, quality:metadata_only=32, quality:summary_only=9 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 36 | method:api=7, method:hf_api=27, method:html=1, method:rss=1, quality:full_text=1, quality:metadata_only=34, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 213 | method:api=7, method:arxiv_api=3, method:changelog_snapshot=5, method:gdelt=9, method:github_api=4, method:hf_api=9, method:html=158, method:metadata=4, method:rss=14, quality:full_text=158, quality:metadata_only=21, quality:summary_only=34 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 95 | method:gdelt=20, method:github_api=12, method:hf_api=2, method:html=55, method:rss=6, quality:full_text=55, quality:metadata_only=5, quality:summary_only=35 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 25 | method:arxiv_api=1, method:gdelt=7, method:html=13, method:rss=4, quality:full_text=13, quality:metadata_only=2, quality:summary_only=10 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 5 | method:html=5, quality:full_text=5 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 10 | method:arxiv_api=6, method:html=4, quality:full_text=4, quality:summary_only=6 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 42 | method:gdelt=42, quality:summary_only=42 | - | monitor |
