# Tech Source Coverage Matrix

- generated_at_utc: 2026-08-26T08:04:21.216484+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 121
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'rss': 28, 'html': 606, 'arxiv_api': 8, 'gdelt': 36}
- content_quality_mix: {'summary_only': 99, 'metadata_only': 59, 'full_text': 606}
- real_candidate_count: 764
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 85
- official_org_candidate_count: 62
- weak_metadata_match_count: 14
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5242, 'metadata_only': 0.4758}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 96 | method:api=2, method:changelog_snapshot=4, method:github_api=33, method:hf_api=27, method:html=4, method:metadata=4, method:rss=22, quality:full_text=4, quality:metadata_only=53, quality:summary_only=39 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 665 | method:api=6, method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=36, method:github_api=9, method:html=602, method:rss=3, quality:full_text=602, quality:metadata_only=6, quality:summary_only=57 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 53 | method:api=6, method:gdelt=1, method:github_api=25, method:hf_api=15, method:html=6, quality:full_text=6, quality:metadata_only=36, quality:summary_only=11 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 36 | method:api=8, method:hf_api=27, method:html=1, quality:full_text=1, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 199 | method:api=2, method:arxiv_api=2, method:changelog_snapshot=5, method:gdelt=4, method:github_api=1, method:hf_api=9, method:html=158, method:metadata=4, method:rss=14, quality:full_text=158, quality:metadata_only=16, quality:summary_only=25 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 117 | method:arxiv_api=2, method:gdelt=23, method:github_api=11, method:hf_api=2, method:html=76, method:rss=3, quality:full_text=76, quality:metadata_only=5, quality:summary_only=36 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 25 | method:gdelt=7, method:html=16, method:rss=2, quality:full_text=16, quality:summary_only=9 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 8 | method:html=8, quality:full_text=8 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 13 | method:arxiv_api=7, method:html=5, method:rss=1, quality:full_text=5, quality:summary_only=8 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 33 | method:gdelt=33, quality:summary_only=33 | - | monitor |
