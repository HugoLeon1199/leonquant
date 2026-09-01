# Tech Source Coverage Matrix

- generated_at_utc: 2026-09-01T06:18:59.577005+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 132
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'arxiv_api': 10, 'rss': 26, 'html': 564, 'gdelt': 20}
- content_quality_mix: {'metadata_only': 59, 'summary_only': 83, 'full_text': 564}
- real_candidate_count: 706
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 87
- official_org_candidate_count: 61
- weak_metadata_match_count: 14
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5317, 'metadata_only': 0.4683}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 100 | method:api=3, method:changelog_snapshot=4, method:github_api=36, method:hf_api=27, method:html=6, method:metadata=4, method:rss=20, quality:full_text=6, quality:metadata_only=54, quality:summary_only=40 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 603 | method:api=5, method:arxiv_api=10, method:changelog_snapshot=1, method:gdelt=20, method:github_api=6, method:html=558, method:rss=3, quality:full_text=558, quality:metadata_only=5, quality:summary_only=40 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 52 | method:api=5, method:arxiv_api=1, method:gdelt=1, method:github_api=26, method:hf_api=15, method:html=3, method:rss=1, quality:full_text=3, quality:metadata_only=35, quality:summary_only=14 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 39 | method:api=8, method:gdelt=2, method:hf_api=27, method:html=1, method:rss=1, quality:full_text=1, quality:metadata_only=35, quality:summary_only=3 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 206 | method:api=3, method:arxiv_api=3, method:changelog_snapshot=5, method:gdelt=5, method:github_api=1, method:hf_api=9, method:html=166, method:metadata=4, method:rss=10, quality:full_text=166, quality:metadata_only=17, quality:summary_only=23 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 76 | method:arxiv_api=1, method:gdelt=10, method:github_api=11, method:hf_api=2, method:html=50, method:rss=2, quality:full_text=50, quality:metadata_only=5, quality:summary_only=21 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 22 | method:arxiv_api=1, method:gdelt=2, method:html=18, method:rss=1, quality:full_text=18, quality:summary_only=4 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 12 | method:html=11, method:rss=1, quality:full_text=11, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 9 | method:arxiv_api=7, method:html=1, method:rss=1, quality:full_text=1, quality:summary_only=8 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 16 | method:gdelt=16, quality:summary_only=16 | - | monitor |
