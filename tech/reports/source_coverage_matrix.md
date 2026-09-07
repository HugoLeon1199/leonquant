# Tech Source Coverage Matrix

- generated_at_utc: 2026-09-07T06:11:49.318135+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 93
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'html': 299, 'rss': 30, 'arxiv_api': 8, 'gdelt': 25}
- content_quality_mix: {'metadata_only': 61, 'summary_only': 88, 'full_text': 299}
- real_candidate_count: 448
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 85
- official_org_candidate_count: 65
- weak_metadata_match_count: 13
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5081, 'metadata_only': 0.4919}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 99 | method:api=7, method:changelog_snapshot=4, method:github_api=33, method:hf_api=27, method:metadata=4, method:rss=24, quality:metadata_only=60, quality:summary_only=39 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 346 | method:api=1, method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=25, method:github_api=9, method:html=299, method:rss=3, quality:full_text=299, quality:metadata_only=1, quality:summary_only=46 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 45 | method:api=1, method:gdelt=1, method:github_api=23, method:hf_api=16, method:html=3, method:rss=1, quality:full_text=3, quality:metadata_only=32, quality:summary_only=10 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 35 | method:api=8, method:hf_api=27, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 132 | method:api=7, method:arxiv_api=2, method:changelog_snapshot=5, method:gdelt=2, method:github_api=1, method:hf_api=9, method:html=93, method:metadata=4, method:rss=9, quality:full_text=93, quality:metadata_only=21, quality:summary_only=18 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 62 | method:arxiv_api=1, method:gdelt=17, method:github_api=11, method:hf_api=1, method:html=28, method:rss=4, quality:full_text=28, quality:metadata_only=4, quality:summary_only=30 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 20 | method:arxiv_api=2, method:gdelt=3, method:html=11, method:rss=4, quality:full_text=11, quality:metadata_only=1, quality:summary_only=8 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 5 | method:gdelt=1, method:html=3, method:rss=1, quality:full_text=3, quality:metadata_only=1, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 10 | method:arxiv_api=8, method:html=1, method:rss=1, quality:full_text=1, quality:summary_only=9 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 23 | method:gdelt=23, quality:summary_only=23 | - | monitor |
