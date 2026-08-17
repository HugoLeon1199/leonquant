# Tech Source Coverage Matrix

- generated_at_utc: 2026-08-17T02:37:32.325353+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 97
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'html': 277, 'rss': 30, 'arxiv_api': 9, 'gdelt': 6}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 71, 'full_text': 277}
- real_candidate_count: 408
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 86
- official_org_candidate_count: 66
- weak_metadata_match_count: 12
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.52, 'metadata_only': 0.48}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 95 | method:api=3, method:changelog_snapshot=4, method:github_api=33, method:hf_api=27, method:metadata=4, method:rss=24, quality:metadata_only=55, quality:summary_only=40 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 310 | method:api=5, method:arxiv_api=9, method:changelog_snapshot=1, method:gdelt=6, method:github_api=9, method:html=277, method:rss=3, quality:full_text=277, quality:metadata_only=5, quality:summary_only=28 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 50 | method:api=5, method:gdelt=1, method:github_api=23, method:hf_api=16, method:html=3, method:rss=2, quality:full_text=3, quality:metadata_only=36, quality:summary_only=11 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 39 | method:api=8, method:hf_api=27, method:html=3, method:rss=1, quality:full_text=3, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 128 | method:api=3, method:arxiv_api=2, method:changelog_snapshot=5, method:github_api=1, method:hf_api=10, method:html=93, method:metadata=4, method:rss=10, quality:full_text=93, quality:metadata_only=18, quality:summary_only=17 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 46 | method:arxiv_api=2, method:gdelt=4, method:github_api=13, method:hf_api=1, method:html=18, method:rss=8, quality:full_text=18, quality:metadata_only=4, quality:summary_only=24 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 12 | method:arxiv_api=1, method:gdelt=1, method:html=9, method:rss=1, quality:full_text=9, quality:summary_only=3 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 7 | method:html=6, method:rss=1, quality:full_text=6, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 10 | method:arxiv_api=9, method:rss=1, quality:summary_only=10 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 5 | method:gdelt=5, quality:summary_only=5 | - | monitor |
