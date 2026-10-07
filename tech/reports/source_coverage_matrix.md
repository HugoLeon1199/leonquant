# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-07T23:38:51.366593+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 121
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'rss': 26, 'html': 594, 'arxiv_api': 7, 'gdelt': 42}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 101, 'full_text': 594}
- real_candidate_count: 755
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 62
- weak_metadata_match_count: 14
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5122, 'metadata_only': 0.4878}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 110 | method:api=8, method:changelog_snapshot=4, method:github_api=35, method:hf_api=27, method:html=12, method:metadata=4, method:rss=20, quality:full_text=12, quality:metadata_only=60, quality:summary_only=38 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 642 | method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=42, method:github_api=7, method:html=582, method:rss=3, quality:full_text=582, quality:summary_only=60 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 53 | method:gdelt=4, method:github_api=26, method:hf_api=16, method:html=7, quality:full_text=7, quality:metadata_only=31, quality:summary_only=15 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 37 | method:api=8, method:hf_api=27, method:html=1, method:rss=1, quality:full_text=1, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 216 | method:api=8, method:arxiv_api=2, method:changelog_snapshot=5, method:gdelt=6, method:github_api=1, method:hf_api=9, method:html=167, method:metadata=4, method:rss=14, quality:full_text=167, quality:metadata_only=22, quality:summary_only=27 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 108 | method:arxiv_api=1, method:gdelt=24, method:github_api=10, method:hf_api=2, method:html=69, method:rss=2, quality:full_text=69, quality:metadata_only=5, quality:summary_only=34 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 18 | method:arxiv_api=1, method:gdelt=2, method:html=13, method:rss=2, quality:full_text=13, quality:summary_only=5 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 7 | method:html=7, quality:full_text=7 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 9 | method:arxiv_api=7, method:html=2, quality:full_text=2, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 33 | method:gdelt=33, quality:summary_only=33 | - | monitor |
