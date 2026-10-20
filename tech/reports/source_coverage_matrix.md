# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-20T22:22:36.756127+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 140
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 5, 'html': 570, 'rss': 23, 'arxiv_api': 6, 'gdelt': 50}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 106, 'full_text': 570}
- real_candidate_count: 736
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 83
- official_org_candidate_count: 60
- weak_metadata_match_count: 11
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5, 'metadata_only': 0.5}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 108 | method:api=6, method:changelog_snapshot=4, method:github_api=34, method:hf_api=27, method:html=15, method:metadata=5, method:rss=17, quality:full_text=15, quality:metadata_only=57, quality:summary_only=36 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 625 | method:api=2, method:arxiv_api=6, method:changelog_snapshot=1, method:gdelt=50, method:github_api=8, method:html=555, method:rss=3, quality:full_text=555, quality:metadata_only=3, quality:summary_only=67 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 69 | method:api=2, method:gdelt=14, method:github_api=22, method:hf_api=15, method:html=15, method:rss=1, quality:full_text=15, quality:metadata_only=32, quality:summary_only=22 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 37 | method:api=8, method:hf_api=27, method:html=1, method:rss=1, quality:full_text=1, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 176 | method:api=6, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=8, method:github_api=4, method:hf_api=8, method:html=131, method:metadata=5, method:rss=8, quality:full_text=131, quality:metadata_only=20, quality:summary_only=25 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 143 | method:arxiv_api=3, method:gdelt=23, method:github_api=12, method:hf_api=3, method:html=97, method:rss=5, quality:full_text=97, quality:metadata_only=6, quality:summary_only=40 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 23 | method:arxiv_api=1, method:gdelt=3, method:html=16, method:rss=3, quality:full_text=16, quality:summary_only=7 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 10 | method:html=9, method:rss=1, quality:full_text=9, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 7 | method:arxiv_api=6, method:html=1, quality:full_text=1, quality:summary_only=6 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 33 | method:gdelt=33, quality:summary_only=33 | - | monitor |
