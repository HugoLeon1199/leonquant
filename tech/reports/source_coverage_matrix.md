# Tech Source Coverage Matrix

- generated_at_utc: 2026-09-22T12:41:10.390418+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 104
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'rss': 26, 'metadata': 4, 'html': 638, 'gdelt': 23}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 75, 'full_text': 638}
- real_candidate_count: 773
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 77
- official_org_candidate_count: 62
- weak_metadata_match_count: 15
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.4828, 'metadata_only': 0.5172}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 107 | method:api=5, method:changelog_snapshot=4, method:github_api=34, method:hf_api=27, method:html=13, method:metadata=4, method:rss=20, quality:full_text=13, quality:metadata_only=57, quality:summary_only=37 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 663 | method:api=3, method:changelog_snapshot=1, method:gdelt=23, method:github_api=8, method:html=625, method:rss=3, quality:full_text=625, quality:metadata_only=3, quality:summary_only=35 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 51 | method:api=3, method:gdelt=1, method:github_api=24, method:hf_api=17, method:html=5, method:rss=1, quality:full_text=5, quality:metadata_only=35, quality:summary_only=11 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 38 | method:api=8, method:hf_api=27, method:html=2, method:rss=1, quality:full_text=2, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 173 | method:api=5, method:changelog_snapshot=5, method:gdelt=2, method:github_api=1, method:hf_api=10, method:html=139, method:metadata=4, method:rss=7, quality:full_text=139, quality:metadata_only=20, quality:summary_only=14 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 103 | method:gdelt=16, method:github_api=12, method:html=71, method:rss=4, quality:full_text=71, quality:metadata_only=3, quality:summary_only=29 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 23 | method:html=23, quality:full_text=23 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 17 | method:html=17, quality:full_text=17 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 5 | method:html=3, method:rss=2, quality:full_text=3, quality:summary_only=2 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 22 | method:gdelt=22, quality:summary_only=22 | - | monitor |
