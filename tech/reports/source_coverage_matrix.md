# Tech Source Coverage Matrix

- generated_at_utc: 2026-11-08T18:25:12.545617+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 91
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 3, 'rss': 33, 'html': 245, 'gdelt': 41, 'arxiv_api': 8}
- content_quality_mix: {'metadata_only': 62, 'summary_only': 105, 'full_text': 245}
- real_candidate_count: 412
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 85
- official_org_candidate_count: 67
- weak_metadata_match_count: 10
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5079, 'metadata_only': 0.4921}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 97 | method:api=6, method:changelog_snapshot=4, method:github_api=31, method:hf_api=27, method:metadata=3, method:rss=26, quality:metadata_only=59, quality:summary_only=38 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 312 | method:api=2, method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=41, method:github_api=11, method:html=245, method:rss=4, quality:full_text=245, quality:metadata_only=3, quality:summary_only=64 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 46 | method:api=2, method:gdelt=3, method:github_api=21, method:hf_api=16, method:html=3, method:rss=1, quality:full_text=3, quality:metadata_only=33, quality:summary_only=10 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 38 | method:api=8, method:gdelt=1, method:hf_api=27, method:html=1, method:rss=1, quality:full_text=1, quality:metadata_only=35, quality:summary_only=2 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 120 | method:api=6, method:changelog_snapshot=5, method:gdelt=9, method:github_api=2, method:hf_api=10, method:html=74, method:metadata=3, method:rss=11, quality:full_text=74, quality:metadata_only=20, quality:summary_only=26 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 64 | method:arxiv_api=3, method:gdelt=16, method:github_api=13, method:hf_api=1, method:html=23, method:rss=8, quality:full_text=23, quality:metadata_only=4, quality:summary_only=37 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 18 | method:gdelt=2, method:html=10, method:rss=6, quality:full_text=10, quality:metadata_only=3, quality:summary_only=5 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 6 | method:gdelt=2, method:html=3, method:rss=1, quality:full_text=3, quality:summary_only=3 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 8 | method:arxiv_api=8, quality:summary_only=8 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 35 | method:gdelt=35, quality:summary_only=35 | - | monitor |
