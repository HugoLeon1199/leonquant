# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-04T07:01:55.962995+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 99
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 5, 'html': 325, 'rss': 27, 'arxiv_api': 7, 'gdelt': 25}
- content_quality_mix: {'metadata_only': 59, 'summary_only': 87, 'full_text': 325}
- real_candidate_count: 471
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 64
- weak_metadata_match_count: 11
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5124, 'metadata_only': 0.4876}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 97 | method:api=8, method:changelog_snapshot=4, method:github_api=32, method:hf_api=27, method:metadata=5, method:rss=21, quality:metadata_only=59, quality:summary_only=38 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 371 | method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=25, method:github_api=10, method:html=325, method:rss=3, quality:full_text=325, quality:summary_only=46 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 44 | method:github_api=24, method:hf_api=15, method:html=5, quality:full_text=5, quality:metadata_only=30, quality:summary_only=9 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 36 | method:api=8, method:hf_api=27, method:html=1, quality:full_text=1, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 120 | method:api=8, method:arxiv_api=3, method:changelog_snapshot=5, method:gdelt=2, method:github_api=1, method:hf_api=9, method:html=76, method:metadata=5, method:rss=11, quality:full_text=76, quality:metadata_only=23, quality:summary_only=21 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 83 | method:arxiv_api=2, method:gdelt=19, method:github_api=11, method:hf_api=3, method:html=40, method:rss=8, quality:full_text=40, quality:metadata_only=6, quality:summary_only=37 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 15 | method:arxiv_api=1, method:gdelt=3, method:html=11, quality:full_text=11, quality:summary_only=4 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 7 | method:html=7, quality:full_text=7 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 8 | method:arxiv_api=6, method:html=1, method:rss=1, quality:full_text=1, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 25 | method:gdelt=25, quality:summary_only=25 | - | monitor |
