# Tech Source Coverage Matrix

- generated_at_utc: 2026-07-23T20:34:39.023917+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 109
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'html': 521, 'rss': 27, 'arxiv_api': 10, 'gdelt': 49}
- content_quality_mix: {'metadata_only': 58, 'summary_only': 114, 'full_text': 521}
- real_candidate_count: 693
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 87
- official_org_candidate_count: 64
- weak_metadata_match_count: 13
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5397, 'metadata_only': 0.4603}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 104 | method:api=7, method:changelog_snapshot=4, method:github_api=33, method:hf_api=27, method:html=8, method:metadata=4, method:rss=21, quality:full_text=8, quality:metadata_only=57, quality:summary_only=39 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 586 | method:api=1, method:arxiv_api=10, method:changelog_snapshot=1, method:gdelt=49, method:github_api=9, method:html=513, method:rss=3, quality:full_text=513, quality:metadata_only=1, quality:summary_only=72 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 44 | method:arxiv_api=1, method:gdelt=2, method:github_api=23, method:hf_api=15, method:html=3, quality:full_text=3, quality:metadata_only=30, quality:summary_only=11 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 38 | method:api=7, method:gdelt=2, method:hf_api=27, method:html=2, quality:full_text=2, quality:metadata_only=34, quality:summary_only=2 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 172 | method:api=8, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=6, method:github_api=2, method:hf_api=10, method:html=123, method:metadata=4, method:rss=13, quality:full_text=123, quality:metadata_only=23, quality:summary_only=26 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 145 | method:arxiv_api=1, method:gdelt=34, method:github_api=12, method:hf_api=2, method:html=92, method:rss=4, quality:full_text=92, quality:metadata_only=5, quality:summary_only=48 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 22 | method:gdelt=3, method:html=14, method:rss=5, quality:full_text=14, quality:summary_only=8 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 11 | method:html=10, method:rss=1, quality:full_text=10, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 10 | method:arxiv_api=10, quality:summary_only=10 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 44 | method:gdelt=44, quality:summary_only=44 | - | monitor |
