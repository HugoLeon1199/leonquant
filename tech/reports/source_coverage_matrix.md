# Tech Source Coverage Matrix

- generated_at_utc: 2026-08-26T22:16:59.266640+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 111
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'rss': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'html': 561, 'arxiv_api': 8, 'gdelt': 33}
- content_quality_mix: {'metadata_only': 59, 'summary_only': 95, 'full_text': 561}
- real_candidate_count: 715
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 85
- official_org_candidate_count: 63
- weak_metadata_match_count: 12
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5242, 'metadata_only': 0.4758}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 101 | method:api=1, method:changelog_snapshot=4, method:github_api=34, method:hf_api=27, method:html=10, method:metadata=4, method:rss=21, quality:full_text=10, quality:metadata_only=52, quality:summary_only=39 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 611 | method:api=7, method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=33, method:github_api=8, method:html=551, method:rss=3, quality:full_text=551, quality:metadata_only=7, quality:summary_only=53 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 57 | method:api=7, method:gdelt=2, method:github_api=25, method:hf_api=17, method:html=5, method:rss=1, quality:full_text=5, quality:metadata_only=39, quality:summary_only=13 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 38 | method:api=8, method:hf_api=27, method:html=2, method:rss=1, quality:full_text=2, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 177 | method:api=1, method:arxiv_api=2, method:changelog_snapshot=5, method:gdelt=5, method:github_api=1, method:hf_api=9, method:html=140, method:metadata=4, method:rss=10, quality:full_text=140, quality:metadata_only=15, quality:summary_only=22 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 102 | method:arxiv_api=2, method:gdelt=17, method:github_api=11, method:html=67, method:rss=5, quality:full_text=67, quality:metadata_only=3, quality:summary_only=32 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 27 | method:gdelt=7, method:html=17, method:rss=3, quality:full_text=17, quality:summary_only=10 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 8 | method:gdelt=1, method:html=7, quality:full_text=7, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 10 | method:arxiv_api=7, method:html=2, method:rss=1, quality:full_text=2, quality:summary_only=8 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 27 | method:gdelt=27, quality:summary_only=27 | - | monitor |
