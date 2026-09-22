# Tech Source Coverage Matrix

- generated_at_utc: 2026-09-22T06:22:42.374902+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 104
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'rss': 26, 'html': 558, 'gdelt': 30}
- content_quality_mix: {'summary_only': 82, 'metadata_only': 60, 'full_text': 558}
- real_candidate_count: 700
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 77
- official_org_candidate_count: 62
- weak_metadata_match_count: 14
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.4828, 'metadata_only': 0.5172}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 105 | method:api=5, method:changelog_snapshot=4, method:github_api=34, method:hf_api=27, method:html=11, method:metadata=4, method:rss=20, quality:full_text=11, quality:metadata_only=57, quality:summary_only=37 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 592 | method:api=3, method:changelog_snapshot=1, method:gdelt=30, method:github_api=8, method:html=547, method:rss=3, quality:full_text=547, quality:metadata_only=3, quality:summary_only=42 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 50 | method:api=3, method:gdelt=2, method:github_api=24, method:hf_api=15, method:html=5, method:rss=1, quality:full_text=5, quality:metadata_only=33, quality:summary_only=12 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 38 | method:api=8, method:hf_api=27, method:html=2, method:rss=1, quality:full_text=2, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 165 | method:api=5, method:changelog_snapshot=5, method:gdelt=3, method:github_api=1, method:hf_api=10, method:html=130, method:metadata=4, method:rss=7, quality:full_text=130, quality:metadata_only=20, quality:summary_only=15 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 98 | method:gdelt=16, method:github_api=12, method:hf_api=2, method:html=64, method:rss=4, quality:full_text=64, quality:metadata_only=5, quality:summary_only=29 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 20 | method:gdelt=3, method:html=17, quality:full_text=17, quality:summary_only=3 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 13 | method:html=13, quality:full_text=13 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 3 | method:html=1, method:rss=2, quality:full_text=1, quality:summary_only=2 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 28 | method:gdelt=28, quality:summary_only=28 | - | monitor |
