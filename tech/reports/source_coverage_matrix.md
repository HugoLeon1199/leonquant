# Tech Source Coverage Matrix

- generated_at_utc: 2026-08-09T03:11:51.641493+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 95
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'changelog_snapshot': 5, 'api': 8, 'metadata': 4, 'html': 287, 'arxiv_api': 7, 'rss': 30, 'gdelt': 15}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 78, 'full_text': 287}
- real_candidate_count: 425
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 65
- weak_metadata_match_count: 13
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5122, 'metadata_only': 0.4878}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 96 | method:api=3, method:changelog_snapshot=4, method:github_api=33, method:hf_api=27, method:html=1, method:metadata=4, method:rss=24, quality:full_text=1, quality:metadata_only=55, quality:summary_only=40 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 326 | method:api=5, method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=15, method:github_api=9, method:html=286, method:rss=3, quality:full_text=286, quality:metadata_only=5, quality:summary_only=35 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 49 | method:api=4, method:gdelt=3, method:github_api=22, method:hf_api=17, method:html=2, method:rss=1, quality:full_text=2, quality:metadata_only=36, quality:summary_only=11 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 35 | method:api=7, method:gdelt=1, method:hf_api=27, quality:metadata_only=34, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 131 | method:api=4, method:arxiv_api=3, method:changelog_snapshot=5, method:gdelt=1, method:github_api=3, method:hf_api=10, method:html=90, method:metadata=4, method:rss=11, quality:full_text=90, quality:metadata_only=19, quality:summary_only=22 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 53 | method:arxiv_api=2, method:gdelt=8, method:github_api=12, method:html=25, method:rss=6, quality:full_text=25, quality:metadata_only=3, quality:summary_only=25 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 15 | method:arxiv_api=1, method:gdelt=1, method:html=10, method:rss=3, quality:full_text=10, quality:summary_only=5 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 4 | method:gdelt=1, method:html=2, method:rss=1, quality:full_text=2, quality:summary_only=2 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 7 | method:arxiv_api=6, method:html=1, quality:full_text=1, quality:summary_only=6 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 12 | method:gdelt=12, quality:summary_only=12 | - | monitor |
