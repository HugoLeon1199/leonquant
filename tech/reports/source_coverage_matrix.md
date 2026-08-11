# Tech Source Coverage Matrix

- generated_at_utc: 2026-08-11T03:14:49.812814+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 106
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'changelog_snapshot': 4, 'api': 8, 'metadata': 5, 'rss': 28, 'arxiv_api': 6, 'html': 500, 'gdelt': 21}
- content_quality_mix: {'metadata_only': 61, 'summary_only': 80, 'full_text': 500}
- real_candidate_count: 641
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 83
- official_org_candidate_count: 63
- weak_metadata_match_count: 15
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5, 'metadata_only': 0.5}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 97 | method:api=4, method:changelog_snapshot=4, method:github_api=32, method:hf_api=27, method:html=4, method:metadata=4, method:rss=22, quality:full_text=4, quality:metadata_only=56, quality:summary_only=37 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 541 | method:api=4, method:arxiv_api=6, method:gdelt=21, method:github_api=10, method:html=496, method:metadata=1, method:rss=3, quality:full_text=496, quality:metadata_only=5, quality:summary_only=40 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 46 | method:api=4, method:gdelt=1, method:github_api=22, method:hf_api=15, method:html=3, method:rss=1, quality:full_text=3, quality:metadata_only=34, quality:summary_only=9 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 38 | method:api=8, method:gdelt=1, method:hf_api=27, method:html=2, quality:full_text=2, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 153 | method:api=4, method:arxiv_api=2, method:changelog_snapshot=4, method:gdelt=3, method:github_api=2, method:hf_api=11, method:html=110, method:metadata=5, method:rss=12, quality:full_text=110, quality:metadata_only=21, quality:summary_only=22 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 88 | method:gdelt=12, method:github_api=12, method:hf_api=1, method:html=58, method:rss=5, quality:full_text=58, quality:metadata_only=4, quality:summary_only=26 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 28 | method:arxiv_api=1, method:gdelt=5, method:html=19, method:rss=3, quality:full_text=19, quality:summary_only=9 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 8 | method:html=8, quality:full_text=8 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 7 | method:arxiv_api=6, method:html=1, quality:full_text=1, quality:summary_only=6 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 17 | method:gdelt=17, quality:summary_only=17 | - | monitor |
