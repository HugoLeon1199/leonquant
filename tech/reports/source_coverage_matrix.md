# Tech Source Coverage Matrix

- generated_at_utc: 2026-07-22T04:38:40.440847+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 117
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'rss': 29, 'html': 573, 'arxiv_api': 8, 'gdelt': 33}
- content_quality_mix: {'metadata_only': 58, 'summary_only': 98, 'full_text': 573}
- real_candidate_count: 729
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
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 103 | method:api=6, method:changelog_snapshot=4, method:github_api=33, method:hf_api=27, method:html=6, method:metadata=4, method:rss=23, quality:full_text=6, quality:metadata_only=56, quality:summary_only=41 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 623 | method:api=2, method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=33, method:github_api=9, method:html=567, method:rss=3, quality:full_text=567, quality:metadata_only=2, quality:summary_only=54 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 50 | method:api=1, method:gdelt=4, method:github_api=23, method:hf_api=15, method:html=7, quality:full_text=7, quality:metadata_only=31, quality:summary_only=12 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 39 | method:api=7, method:gdelt=1, method:hf_api=27, method:html=4, quality:full_text=4, quality:metadata_only=34, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 178 | method:api=7, method:arxiv_api=2, method:changelog_snapshot=5, method:gdelt=2, method:github_api=2, method:hf_api=10, method:html=135, method:metadata=4, method:rss=11, quality:full_text=135, quality:metadata_only=22, quality:summary_only=21 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 128 | method:arxiv_api=3, method:gdelt=24, method:github_api=12, method:hf_api=2, method:html=81, method:rss=6, quality:full_text=81, quality:metadata_only=5, quality:summary_only=42 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 26 | method:gdelt=2, method:html=18, method:rss=6, quality:full_text=18, quality:summary_only=8 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 16 | method:html=16, quality:full_text=16 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 11 | method:arxiv_api=8, method:html=3, quality:full_text=3, quality:summary_only=8 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 28 | method:gdelt=28, quality:summary_only=28 | - | monitor |
