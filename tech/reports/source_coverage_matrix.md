# Tech Source Coverage Matrix

- generated_at_utc: 2026-07-20T10:23:36.258246+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 96
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'html': 340, 'rss': 30, 'arxiv_api': 10, 'gdelt': 5}
- content_quality_mix: {'metadata_only': 59, 'summary_only': 72, 'full_text': 340}
- real_candidate_count: 471
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 87
- official_org_candidate_count: 66
- weak_metadata_match_count: 13
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5317, 'metadata_only': 0.4683}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 98 | method:api=6, method:changelog_snapshot=4, method:github_api=33, method:hf_api=27, method:metadata=4, method:rss=24, quality:metadata_only=57, quality:summary_only=41 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 370 | method:api=2, method:arxiv_api=10, method:changelog_snapshot=1, method:gdelt=5, method:github_api=9, method:html=340, method:rss=3, quality:full_text=340, quality:metadata_only=2, quality:summary_only=28 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 48 | method:api=1, method:arxiv_api=1, method:gdelt=2, method:github_api=24, method:hf_api=16, method:html=4, quality:full_text=4, quality:metadata_only=32, quality:summary_only=12 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 35 | method:api=7, method:hf_api=27, method:html=1, quality:full_text=1, quality:metadata_only=34 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 149 | method:api=7, method:arxiv_api=4, method:changelog_snapshot=5, method:github_api=2, method:hf_api=10, method:html=103, method:metadata=4, method:rss=14, quality:full_text=103, quality:metadata_only=23, quality:summary_only=23 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 46 | method:arxiv_api=1, method:gdelt=1, method:github_api=11, method:hf_api=1, method:html=24, method:rss=8, quality:full_text=24, quality:metadata_only=4, quality:summary_only=18 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 15 | method:arxiv_api=2, method:gdelt=1, method:html=11, method:rss=1, quality:full_text=11, quality:summary_only=4 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 6 | method:html=5, method:rss=1, quality:full_text=5, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 12 | method:arxiv_api=8, method:html=3, method:rss=1, quality:full_text=3, quality:summary_only=9 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 3 | method:gdelt=3, quality:summary_only=3 | - | monitor |
