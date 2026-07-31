# Tech Source Coverage Matrix

- generated_at_utc: 2026-07-31T10:04:12.326320+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 103
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'changelog_snapshot': 5, 'api': 8, 'metadata': 4, 'rss': 25, 'html': 590, 'arxiv_api': 6, 'gdelt': 25}
- content_quality_mix: {'summary_only': 82, 'metadata_only': 60, 'full_text': 590}
- real_candidate_count: 732
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 83
- official_org_candidate_count: 60
- weak_metadata_match_count: 15
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5082, 'metadata_only': 0.4918}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 102 | method:api=6, method:changelog_snapshot=4, method:github_api=33, method:hf_api=27, method:html=9, method:metadata=4, method:rss=19, quality:full_text=9, quality:metadata_only=58, quality:summary_only=35 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 627 | method:api=2, method:arxiv_api=6, method:changelog_snapshot=1, method:gdelt=25, method:github_api=9, method:html=581, method:rss=3, quality:full_text=581, quality:metadata_only=2, quality:summary_only=44 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 43 | method:api=2, method:arxiv_api=1, method:github_api=21, method:hf_api=15, method:html=3, method:rss=1, quality:full_text=3, quality:metadata_only=32, quality:summary_only=8 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 37 | method:api=8, method:hf_api=27, method:html=1, method:rss=1, quality:full_text=1, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 173 | method:api=6, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=1, method:github_api=3, method:hf_api=10, method:html=131, method:metadata=4, method:rss=12, quality:full_text=131, quality:metadata_only=21, quality:summary_only=21 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 126 | method:arxiv_api=3, method:gdelt=16, method:github_api=13, method:hf_api=2, method:html=87, method:rss=5, quality:full_text=87, quality:metadata_only=5, quality:summary_only=34 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 25 | method:gdelt=5, method:html=18, method:rss=2, quality:full_text=18, quality:metadata_only=1, quality:summary_only=6 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 15 | method:html=14, method:rss=1, quality:full_text=14, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 11 | method:arxiv_api=6, method:html=5, quality:full_text=5, quality:summary_only=6 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 25 | method:gdelt=25, quality:summary_only=25 | - | monitor |
