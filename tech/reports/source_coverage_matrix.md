# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-31T22:33:29.616186+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 87
- candidates_by_method: {'github_api': 42, 'hf_api': 26, 'api': 8, 'changelog_snapshot': 5, 'metadata': 3, 'rss': 33, 'html': 321, 'arxiv_api': 8, 'gdelt': 27}
- content_quality_mix: {'metadata_only': 61, 'summary_only': 91, 'full_text': 321}
- real_candidate_count: 473
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 66
- weak_metadata_match_count: 12
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.512, 'metadata_only': 0.488}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 96 | method:api=5, method:changelog_snapshot=4, method:github_api=31, method:hf_api=26, method:metadata=3, method:rss=27, quality:metadata_only=57, quality:summary_only=39 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 374 | method:api=3, method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=27, method:github_api=11, method:html=321, method:rss=3, quality:full_text=321, quality:metadata_only=4, quality:summary_only=49 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 46 | method:api=3, method:github_api=22, method:hf_api=16, method:html=5, quality:full_text=5, quality:metadata_only=34, quality:summary_only=7 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 35 | method:api=8, method:hf_api=26, method:html=1, quality:full_text=1, quality:metadata_only=34 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 129 | method:api=5, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=3, method:github_api=2, method:hf_api=9, method:html=92, method:metadata=3, method:rss=9, quality:full_text=92, quality:metadata_only=19, quality:summary_only=18 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 77 | method:arxiv_api=3, method:gdelt=19, method:github_api=13, method:html=33, method:rss=9, quality:full_text=33, quality:metadata_only=3, quality:summary_only=41 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 15 | method:gdelt=2, method:html=10, method:rss=3, quality:full_text=10, quality:metadata_only=1, quality:summary_only=4 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 9 | method:gdelt=1, method:html=7, method:rss=1, quality:full_text=7, quality:summary_only=2 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 9 | method:arxiv_api=8, method:html=1, quality:full_text=1, quality:summary_only=8 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 26 | method:gdelt=26, quality:summary_only=26 | - | monitor |
