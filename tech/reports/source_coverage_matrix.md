# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-31T07:03:40.718075+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 111
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 3, 'rss': 29, 'html': 578, 'arxiv_api': 8, 'gdelt': 27}
- content_quality_mix: {'metadata_only': 62, 'summary_only': 87, 'full_text': 578}
- real_candidate_count: 727
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 85
- official_org_candidate_count: 62
- weak_metadata_match_count: 14
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5079, 'metadata_only': 0.4921}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 102 | method:api=5, method:changelog_snapshot=4, method:github_api=32, method:hf_api=27, method:html=8, method:metadata=3, method:rss=23, quality:full_text=8, quality:metadata_only=58, quality:summary_only=36 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 622 | method:api=3, method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=27, method:github_api=10, method:html=570, method:rss=3, quality:full_text=570, quality:metadata_only=4, quality:summary_only=48 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 49 | method:api=3, method:github_api=23, method:hf_api=15, method:html=7, method:rss=1, quality:full_text=7, quality:metadata_only=33, quality:summary_only=9 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 37 | method:api=8, method:hf_api=27, method:rss=2, quality:metadata_only=35, quality:summary_only=2 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 183 | method:api=5, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=3, method:github_api=2, method:hf_api=9, method:html=145, method:metadata=3, method:rss=10, quality:full_text=145, quality:metadata_only=19, quality:summary_only=19 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 108 | method:arxiv_api=3, method:gdelt=18, method:github_api=13, method:hf_api=2, method:html=67, method:rss=5, quality:full_text=67, quality:metadata_only=5, quality:summary_only=36 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 23 | method:gdelt=3, method:html=17, method:rss=3, quality:full_text=17, quality:metadata_only=1, quality:summary_only=5 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 10 | method:gdelt=1, method:html=9, quality:full_text=9, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 10 | method:arxiv_api=8, method:html=2, quality:full_text=2, quality:summary_only=8 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 26 | method:gdelt=26, quality:summary_only=26 | - | monitor |
