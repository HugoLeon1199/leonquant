# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-10T07:14:54.997080+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 119
- candidates_by_method: {'github_api': 42, 'hf_api': 26, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'html': 531, 'arxiv_api': 10, 'rss': 28, 'gdelt': 39}
- content_quality_mix: {'metadata_only': 59, 'summary_only': 103, 'full_text': 531}
- real_candidate_count: 693
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 86
- official_org_candidate_count: 64
- weak_metadata_match_count: 11
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.528, 'metadata_only': 0.472}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 100 | method:api=7, method:changelog_snapshot=4, method:github_api=34, method:hf_api=26, method:html=3, method:metadata=4, method:rss=22, quality:full_text=3, quality:metadata_only=58, quality:summary_only=39 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 590 | method:api=1, method:arxiv_api=10, method:changelog_snapshot=1, method:gdelt=39, method:github_api=8, method:html=528, method:rss=3, quality:full_text=528, quality:metadata_only=1, quality:summary_only=61 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 46 | method:api=1, method:gdelt=1, method:github_api=25, method:hf_api=16, method:html=3, quality:full_text=3, quality:metadata_only=32, quality:summary_only=11 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 39 | method:api=8, method:gdelt=1, method:hf_api=26, method:html=4, quality:full_text=4, quality:metadata_only=34, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 191 | method:api=7, method:arxiv_api=4, method:changelog_snapshot=5, method:gdelt=6, method:github_api=1, method:hf_api=9, method:html=142, method:metadata=4, method:rss=13, quality:full_text=142, quality:metadata_only=21, quality:summary_only=28 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 121 | method:arxiv_api=4, method:gdelt=28, method:github_api=10, method:hf_api=1, method:html=73, method:rss=5, quality:full_text=73, quality:metadata_only=4, quality:summary_only=44 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 18 | method:gdelt=1, method:html=15, method:rss=2, quality:full_text=15, quality:summary_only=3 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 14 | method:html=14, quality:full_text=14 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 9 | method:arxiv_api=8, method:html=1, quality:full_text=1, quality:summary_only=8 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 36 | method:gdelt=36, quality:summary_only=36 | - | monitor |
