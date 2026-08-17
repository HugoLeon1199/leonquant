# Tech Source Coverage Matrix

- generated_at_utc: 2026-08-17T19:46:34.412211+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 99
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 5, 'rss': 25, 'html': 459, 'gdelt': 23, 'arxiv_api': 9}
- content_quality_mix: {'metadata_only': 61, 'summary_only': 83, 'full_text': 459}
- real_candidate_count: 603
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 86
- official_org_candidate_count: 62
- weak_metadata_match_count: 15
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5041, 'metadata_only': 0.4959}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 96 | method:api=3, method:changelog_snapshot=4, method:github_api=34, method:hf_api=27, method:html=4, method:metadata=5, method:rss=19, quality:full_text=4, quality:metadata_only=56, quality:summary_only=36 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 504 | method:api=5, method:arxiv_api=9, method:changelog_snapshot=1, method:gdelt=23, method:github_api=8, method:html=455, method:rss=3, quality:full_text=455, quality:metadata_only=5, quality:summary_only=44 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 53 | method:api=5, method:gdelt=1, method:github_api=24, method:hf_api=15, method:html=5, method:rss=3, quality:full_text=5, quality:metadata_only=35, quality:summary_only=13 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 41 | method:api=8, method:gdelt=1, method:hf_api=27, method:html=2, method:rss=3, quality:full_text=2, quality:metadata_only=35, quality:summary_only=4 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 133 | method:api=3, method:arxiv_api=2, method:changelog_snapshot=5, method:gdelt=3, method:github_api=2, method:hf_api=9, method:html=94, method:metadata=5, method:rss=10, quality:full_text=94, quality:metadata_only=18, quality:summary_only=21 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 88 | method:arxiv_api=2, method:gdelt=13, method:github_api=13, method:hf_api=2, method:html=54, method:rss=4, quality:full_text=54, quality:metadata_only=5, quality:summary_only=29 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 13 | method:arxiv_api=1, method:gdelt=3, method:html=9, quality:full_text=9, quality:summary_only=4 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 11 | method:gdelt=2, method:html=9, quality:full_text=9, quality:summary_only=2 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 13 | method:arxiv_api=9, method:html=3, method:rss=1, quality:full_text=3, quality:summary_only=10 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 21 | method:gdelt=21, quality:summary_only=21 | - | monitor |
