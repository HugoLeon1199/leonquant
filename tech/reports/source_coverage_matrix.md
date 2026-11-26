# Tech Source Coverage Matrix

- generated_at_utc: 2026-11-26T22:25:26.286984+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 108
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 3, 'arxiv_api': 7, 'rss': 33, 'html': 504, 'gdelt': 37}
- content_quality_mix: {'metadata_only': 61, 'summary_only': 101, 'full_text': 504}
- real_candidate_count: 666
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 66
- weak_metadata_match_count: 13
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.512, 'metadata_only': 0.488}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 103 | method:api=6, method:changelog_snapshot=4, method:github_api=35, method:hf_api=27, method:html=1, method:metadata=3, method:rss=27, quality:full_text=1, quality:metadata_only=59, quality:summary_only=43 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 560 | method:api=2, method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=37, method:github_api=7, method:html=503, method:rss=3, quality:full_text=503, quality:metadata_only=2, quality:summary_only=55 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 43 | method:api=1, method:gdelt=1, method:github_api=22, method:hf_api=15, method:html=4, quality:full_text=4, quality:metadata_only=31, quality:summary_only=8 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 35 | method:api=7, method:hf_api=27, method:html=1, quality:full_text=1, quality:metadata_only=34 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 208 | method:api=7, method:arxiv_api=3, method:changelog_snapshot=5, method:gdelt=5, method:github_api=4, method:hf_api=9, method:html=158, method:metadata=3, method:rss=14, quality:full_text=158, quality:metadata_only=20, quality:summary_only=30 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 82 | method:gdelt=15, method:github_api=12, method:hf_api=3, method:html=45, method:rss=7, quality:full_text=45, quality:metadata_only=6, quality:summary_only=31 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 27 | method:arxiv_api=1, method:gdelt=8, method:html=14, method:rss=4, quality:full_text=14, quality:metadata_only=2, quality:summary_only=11 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 3 | method:html=3, quality:full_text=3 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 7 | method:arxiv_api=6, method:rss=1, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 36 | method:gdelt=36, quality:summary_only=36 | - | monitor |
