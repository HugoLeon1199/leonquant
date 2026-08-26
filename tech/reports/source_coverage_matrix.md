# Tech Source Coverage Matrix

- generated_at_utc: 2026-08-26T14:08:09.207884+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 126
- candidates_by_method: {'hf_api': 25, 'github_api': 42, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'html': 695, 'rss': 28, 'arxiv_api': 8, 'gdelt': 36}
- content_quality_mix: {'metadata_only': 57, 'summary_only': 99, 'full_text': 695}
- real_candidate_count: 851
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 83
- official_org_candidate_count: 65
- weak_metadata_match_count: 13
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5328, 'metadata_only': 0.4672}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 94 | method:api=1, method:changelog_snapshot=4, method:github_api=33, method:hf_api=25, method:html=5, method:metadata=4, method:rss=22, quality:full_text=5, quality:metadata_only=50, quality:summary_only=39 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 754 | method:api=7, method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=36, method:github_api=9, method:html=690, method:rss=3, quality:full_text=690, quality:metadata_only=7, quality:summary_only=57 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 55 | method:api=7, method:gdelt=3, method:github_api=25, method:hf_api=13, method:html=7, quality:full_text=7, quality:metadata_only=35, quality:summary_only=13 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 35 | method:api=8, method:hf_api=25, method:html=2, quality:full_text=2, quality:metadata_only=33 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 207 | method:api=1, method:arxiv_api=2, method:changelog_snapshot=5, method:gdelt=5, method:github_api=1, method:hf_api=9, method:html=167, method:metadata=4, method:rss=13, quality:full_text=167, quality:metadata_only=15, quality:summary_only=25 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 130 | method:arxiv_api=2, method:gdelt=21, method:github_api=11, method:hf_api=2, method:html=92, method:rss=2, quality:full_text=92, quality:metadata_only=5, quality:summary_only=33 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 27 | method:gdelt=5, method:html=20, method:rss=2, quality:full_text=20, quality:summary_only=7 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 11 | method:gdelt=1, method:html=10, quality:full_text=10, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 12 | method:arxiv_api=7, method:html=4, method:rss=1, quality:full_text=4, quality:summary_only=8 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 30 | method:gdelt=30, quality:summary_only=30 | - | monitor |
