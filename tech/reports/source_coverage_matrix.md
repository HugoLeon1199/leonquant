# Tech Source Coverage Matrix

- generated_at_utc: 2026-09-27T13:08:16.395366+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 92
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 5, 'html': 387, 'rss': 27, 'gdelt': 49}
- content_quality_mix: {'metadata_only': 59, 'summary_only': 104, 'full_text': 387}
- real_candidate_count: 550
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 77
- official_org_candidate_count: 64
- weak_metadata_match_count: 16
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.4825, 'metadata_only': 0.5175}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 94 | method:api=3, method:changelog_snapshot=4, method:github_api=34, method:hf_api=27, method:metadata=5, method:rss=21, quality:metadata_only=54, quality:summary_only=40 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 452 | method:api=5, method:changelog_snapshot=1, method:gdelt=48, method:github_api=8, method:html=387, method:rss=3, quality:full_text=387, quality:metadata_only=5, quality:summary_only=60 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 48 | method:api=5, method:github_api=25, method:hf_api=16, method:html=1, method:rss=1, quality:full_text=1, quality:metadata_only=36, quality:summary_only=11 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 36 | method:api=8, method:hf_api=27, method:html=1, quality:full_text=1, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 147 | method:api=3, method:changelog_snapshot=5, method:gdelt=1, method:github_api=1, method:hf_api=10, method:html=113, method:metadata=5, method:rss=9, quality:full_text=113, quality:metadata_only=19, quality:summary_only=15 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 105 | method:gdelt=46, method:github_api=12, method:hf_api=1, method:html=44, method:rss=2, quality:full_text=44, quality:metadata_only=4, quality:summary_only=57 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 7 | method:html=4, method:rss=3, quality:full_text=4, quality:summary_only=3 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 9 | method:html=9, quality:full_text=9 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 5 | method:gdelt=1, method:rss=4, quality:summary_only=5 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 4 | method:gdelt=1, method:rss=3, quality:summary_only=4 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 49 | method:gdelt=49, quality:summary_only=49 | - | monitor |
