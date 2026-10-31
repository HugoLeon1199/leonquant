# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-31T13:43:24.296807+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 110
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 3, 'rss': 29, 'html': 616, 'arxiv_api': 8, 'gdelt': 29}
- content_quality_mix: {'metadata_only': 62, 'summary_only': 89, 'full_text': 616}
- real_candidate_count: 767
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 85
- official_org_candidate_count: 63
- weak_metadata_match_count: 11
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5079, 'metadata_only': 0.4921}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 102 | method:api=5, method:changelog_snapshot=4, method:github_api=32, method:hf_api=27, method:html=8, method:metadata=3, method:rss=23, quality:full_text=8, quality:metadata_only=58, quality:summary_only=36 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 662 | method:api=3, method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=29, method:github_api=10, method:html=608, method:rss=3, quality:full_text=608, quality:metadata_only=4, quality:summary_only=50 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 48 | method:api=3, method:github_api=23, method:hf_api=16, method:html=6, quality:full_text=6, quality:metadata_only=34, quality:summary_only=8 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 36 | method:api=8, method:hf_api=27, method:html=1, quality:full_text=1, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 192 | method:api=5, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=3, method:github_api=2, method:hf_api=9, method:html=155, method:metadata=3, method:rss=9, quality:full_text=155, quality:metadata_only=19, quality:summary_only=18 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 114 | method:arxiv_api=3, method:gdelt=21, method:github_api=13, method:hf_api=1, method:html=69, method:rss=7, quality:full_text=69, quality:metadata_only=4, quality:summary_only=41 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 24 | method:gdelt=2, method:html=18, method:rss=4, quality:full_text=18, quality:metadata_only=1, quality:summary_only=5 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 13 | method:gdelt=1, method:html=12, quality:full_text=12, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 10 | method:arxiv_api=8, method:html=2, quality:full_text=2, quality:summary_only=8 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 28 | method:gdelt=28, quality:summary_only=28 | - | monitor |
