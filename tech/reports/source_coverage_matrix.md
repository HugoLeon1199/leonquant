# Tech Source Coverage Matrix

- generated_at_utc: 2026-09-08T17:19:39.099039+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 97
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'rss': 26, 'html': 469, 'gdelt': 35, 'arxiv_api': 8}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 95, 'full_text': 469}
- real_candidate_count: 624
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 85
- official_org_candidate_count: 61
- weak_metadata_match_count: 11
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5161, 'metadata_only': 0.4839}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 104 | method:api=7, method:changelog_snapshot=4, method:github_api=33, method:hf_api=27, method:html=9, method:metadata=4, method:rss=20, quality:full_text=9, quality:metadata_only=59, quality:summary_only=36 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 517 | method:api=1, method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=35, method:github_api=9, method:html=460, method:rss=3, quality:full_text=460, quality:metadata_only=1, quality:summary_only=56 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 43 | method:api=1, method:gdelt=1, method:github_api=23, method:hf_api=15, method:html=3, quality:full_text=3, quality:metadata_only=31, quality:summary_only=9 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 36 | method:api=8, method:hf_api=27, method:html=1, quality:full_text=1, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 163 | method:api=7, method:arxiv_api=2, method:changelog_snapshot=5, method:gdelt=7, method:github_api=1, method:hf_api=9, method:html=116, method:metadata=4, method:rss=12, quality:full_text=116, quality:metadata_only=21, quality:summary_only=26 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 97 | method:arxiv_api=1, method:gdelt=19, method:github_api=11, method:hf_api=2, method:html=60, method:rss=4, quality:full_text=60, quality:metadata_only=5, quality:summary_only=32 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 19 | method:arxiv_api=2, method:gdelt=3, method:html=13, method:rss=1, quality:full_text=13, quality:summary_only=6 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 10 | method:gdelt=2, method:html=6, method:rss=2, quality:full_text=6, quality:metadata_only=1, quality:summary_only=3 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 11 | method:arxiv_api=8, method:html=3, quality:full_text=3, quality:summary_only=8 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 33 | method:gdelt=33, quality:summary_only=33 | - | monitor |
