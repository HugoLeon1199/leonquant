# Tech Source Coverage Matrix

- generated_at_utc: 2026-11-13T08:08:07.332141+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 115
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'html': 607, 'rss': 26, 'gdelt': 40}
- content_quality_mix: {'metadata_only': 61, 'summary_only': 91, 'full_text': 607}
- real_candidate_count: 759
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 77
- official_org_candidate_count: 61
- weak_metadata_match_count: 10
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.4741, 'metadata_only': 0.5259}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 107 | method:api=5, method:changelog_snapshot=4, method:github_api=32, method:hf_api=27, method:html=16, method:metadata=4, method:rss=19, quality:full_text=16, quality:metadata_only=58, quality:summary_only=33 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 648 | method:api=3, method:changelog_snapshot=1, method:gdelt=40, method:github_api=10, method:html=591, method:rss=3, quality:full_text=591, quality:metadata_only=3, quality:summary_only=54 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 42 | method:api=2, method:gdelt=1, method:github_api=22, method:hf_api=16, method:html=1, quality:full_text=1, quality:metadata_only=33, quality:summary_only=8 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 36 | method:api=7, method:hf_api=27, method:rss=2, quality:metadata_only=34, quality:summary_only=2 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 191 | method:api=6, method:changelog_snapshot=5, method:gdelt=7, method:github_api=1, method:hf_api=9, method:html=153, method:metadata=4, method:rss=6, quality:full_text=153, quality:metadata_only=20, quality:summary_only=18 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 119 | method:gdelt=18, method:github_api=13, method:hf_api=2, method:html=77, method:rss=9, quality:full_text=77, quality:metadata_only=5, quality:summary_only=37 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 28 | method:gdelt=8, method:html=16, method:rss=4, quality:full_text=16, quality:metadata_only=2, quality:summary_only=10 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 7 | method:html=6, method:rss=1, quality:full_text=6, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 4 | method:html=4, quality:full_text=4 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 4 | method:rss=4, quality:summary_only=4 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 36 | method:gdelt=36, quality:summary_only=36 | - | monitor |
