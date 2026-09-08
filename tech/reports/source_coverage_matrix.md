# Tech Source Coverage Matrix

- generated_at_utc: 2026-09-08T21:56:10.297449+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 103
- candidates_by_method: {'github_api': 42, 'hf_api': 26, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'rss': 27, 'html': 539, 'gdelt': 36, 'arxiv_api': 8}
- content_quality_mix: {'metadata_only': 59, 'summary_only': 97, 'full_text': 539}
- real_candidate_count: 695
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 62
- weak_metadata_match_count: 12
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5203, 'metadata_only': 0.4797}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 106 | method:api=8, method:changelog_snapshot=4, method:github_api=33, method:hf_api=26, method:html=10, method:metadata=4, method:rss=21, quality:full_text=10, quality:metadata_only=59, quality:summary_only=37 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 586 | method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=36, method:github_api=9, method:html=529, method:rss=3, quality:full_text=529, quality:summary_only=57 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 42 | method:gdelt=1, method:github_api=23, method:hf_api=15, method:html=3, quality:full_text=3, quality:metadata_only=30, quality:summary_only=9 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 35 | method:api=8, method:hf_api=26, method:html=1, quality:full_text=1, quality:metadata_only=34 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 184 | method:api=8, method:arxiv_api=2, method:changelog_snapshot=5, method:gdelt=7, method:github_api=1, method:hf_api=9, method:html=137, method:metadata=4, method:rss=11, quality:full_text=137, quality:metadata_only=22, quality:summary_only=25 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 113 | method:arxiv_api=1, method:gdelt=21, method:github_api=11, method:hf_api=1, method:html=75, method:rss=4, quality:full_text=75, quality:metadata_only=4, quality:summary_only=34 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 20 | method:arxiv_api=2, method:gdelt=4, method:html=13, method:rss=1, quality:full_text=13, quality:summary_only=7 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 13 | method:gdelt=1, method:html=11, method:rss=1, quality:full_text=11, quality:metadata_only=1, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 10 | method:arxiv_api=8, method:html=1, method:rss=1, quality:full_text=1, quality:summary_only=9 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 34 | method:gdelt=34, quality:summary_only=34 | - | monitor |
