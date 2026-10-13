# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-13T07:52:55.379488+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 107
- candidates_by_method: {'github_api': 42, 'hf_api': 26, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'rss': 26, 'html': 539, 'arxiv_api': 2, 'gdelt': 24}
- content_quality_mix: {'metadata_only': 59, 'summary_only': 78, 'full_text': 539}
- real_candidate_count: 676
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 78
- official_org_candidate_count: 62
- weak_metadata_match_count: 11
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.4957, 'metadata_only': 0.5043}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 102 | method:api=7, method:changelog_snapshot=4, method:github_api=34, method:hf_api=26, method:html=7, method:metadata=4, method:rss=20, quality:full_text=7, quality:metadata_only=58, quality:summary_only=37 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 571 | method:api=1, method:arxiv_api=2, method:changelog_snapshot=1, method:gdelt=24, method:github_api=8, method:html=532, method:rss=3, quality:full_text=532, quality:metadata_only=1, quality:summary_only=38 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 50 | method:api=1, method:github_api=26, method:hf_api=16, method:html=7, quality:full_text=7, quality:metadata_only=32, quality:summary_only=11 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 36 | method:api=8, method:hf_api=26, method:html=2, quality:full_text=2, quality:metadata_only=34 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 150 | method:api=7, method:changelog_snapshot=5, method:gdelt=1, method:github_api=1, method:hf_api=9, method:html=112, method:metadata=4, method:rss=11, quality:full_text=112, quality:metadata_only=21, quality:summary_only=17 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 106 | method:arxiv_api=1, method:gdelt=17, method:github_api=9, method:hf_api=1, method:html=71, method:rss=7, quality:full_text=71, quality:metadata_only=4, quality:summary_only=31 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 28 | method:gdelt=4, method:html=23, method:rss=1, quality:full_text=23, quality:summary_only=5 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 8 | method:html=8, quality:full_text=8 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 5 | method:arxiv_api=2, method:html=3, quality:full_text=3, quality:summary_only=2 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 24 | method:gdelt=24, quality:summary_only=24 | - | monitor |
