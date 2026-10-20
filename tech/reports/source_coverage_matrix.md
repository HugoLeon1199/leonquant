# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-20T18:03:01.550834+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 132
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 5, 'html': 490, 'rss': 24, 'arxiv_api': 6, 'gdelt': 49}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 106, 'full_text': 490}
- real_candidate_count: 656
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 83
- official_org_candidate_count: 60
- weak_metadata_match_count: 12
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5, 'metadata_only': 0.5}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 106 | method:api=6, method:changelog_snapshot=4, method:github_api=33, method:hf_api=27, method:html=13, method:metadata=5, method:rss=18, quality:full_text=13, quality:metadata_only=57, quality:summary_only=36 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 547 | method:api=2, method:arxiv_api=6, method:changelog_snapshot=1, method:gdelt=49, method:github_api=9, method:html=477, method:rss=3, quality:full_text=477, quality:metadata_only=3, quality:summary_only=67 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 67 | method:api=2, method:gdelt=15, method:github_api=22, method:hf_api=15, method:html=12, method:rss=1, quality:full_text=12, quality:metadata_only=32, quality:summary_only=23 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 38 | method:api=8, method:gdelt=1, method:hf_api=27, method:html=1, method:rss=1, quality:full_text=1, quality:metadata_only=35, quality:summary_only=2 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 160 | method:api=6, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=9, method:github_api=3, method:hf_api=8, method:html=115, method:metadata=5, method:rss=8, quality:full_text=115, quality:metadata_only=20, quality:summary_only=25 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 130 | method:arxiv_api=3, method:gdelt=22, method:github_api=12, method:hf_api=3, method:html=84, method:rss=6, quality:full_text=84, quality:metadata_only=6, quality:summary_only=40 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 19 | method:arxiv_api=1, method:gdelt=2, method:html=13, method:rss=3, quality:full_text=13, quality:summary_only=6 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 10 | method:html=9, method:rss=1, quality:full_text=9, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 7 | method:arxiv_api=6, method:html=1, quality:full_text=1, quality:summary_only=6 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 30 | method:gdelt=30, quality:summary_only=30 | - | monitor |
