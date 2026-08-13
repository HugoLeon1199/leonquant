# Tech Source Coverage Matrix

- generated_at_utc: 2026-08-13T14:36:27.849393+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 120
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'rss': 26, 'changelog_snapshot': 5, 'api': 8, 'metadata': 4, 'html': 674, 'arxiv_api': 7, 'gdelt': 37}
- content_quality_mix: {'metadata_only': 59, 'summary_only': 97, 'full_text': 674}
- real_candidate_count: 830
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 62
- weak_metadata_match_count: 11
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5203, 'metadata_only': 0.4797}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 103 | method:api=4, method:changelog_snapshot=4, method:github_api=33, method:hf_api=27, method:html=11, method:metadata=4, method:rss=20, quality:full_text=11, quality:metadata_only=55, quality:summary_only=37 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 723 | method:api=4, method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=36, method:github_api=9, method:html=663, method:rss=3, quality:full_text=663, quality:metadata_only=4, quality:summary_only=56 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 53 | method:api=4, method:gdelt=1, method:github_api=23, method:hf_api=15, method:html=8, method:rss=2, quality:full_text=8, quality:metadata_only=34, quality:summary_only=11 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 38 | method:api=8, method:gdelt=1, method:hf_api=27, method:html=1, method:rss=1, quality:full_text=1, quality:metadata_only=35, quality:summary_only=2 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 202 | method:api=4, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=6, method:github_api=2, method:hf_api=10, method:html=161, method:metadata=4, method:rss=9, quality:full_text=161, quality:metadata_only=19, quality:summary_only=22 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 133 | method:arxiv_api=5, method:gdelt=28, method:github_api=12, method:hf_api=2, method:html=81, method:rss=5, quality:full_text=81, quality:metadata_only=5, quality:summary_only=47 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 22 | method:gdelt=1, method:html=20, method:rss=1, quality:full_text=20, quality:summary_only=2 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 9 | method:html=9, quality:full_text=9 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 9 | method:arxiv_api=6, method:html=3, quality:full_text=3, quality:summary_only=6 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 4 | method:gdelt=1, method:rss=3, quality:summary_only=4 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 33 | method:gdelt=33, quality:summary_only=33 | - | monitor |
