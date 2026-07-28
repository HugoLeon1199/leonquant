# Tech Source Coverage Matrix

- generated_at_utc: 2026-07-28T20:38:24.989823+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 122
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'changelog_snapshot': 5, 'api': 8, 'metadata': 4, 'html': 505, 'rss': 28, 'arxiv_api': 5, 'gdelt': 39}
- content_quality_mix: {'summary_only': 100, 'metadata_only': 58, 'full_text': 505}
- real_candidate_count: 663
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 82
- official_org_candidate_count: 65
- weak_metadata_match_count: 13
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5207, 'metadata_only': 0.4793}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 102 | method:api=7, method:changelog_snapshot=4, method:github_api=33, method:hf_api=27, method:html=5, method:metadata=4, method:rss=22, quality:full_text=5, quality:metadata_only=57, quality:summary_only=40 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 558 | method:api=1, method:arxiv_api=5, method:changelog_snapshot=1, method:gdelt=39, method:github_api=9, method:html=500, method:rss=3, quality:full_text=500, quality:metadata_only=1, quality:summary_only=57 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 47 | method:api=1, method:gdelt=2, method:github_api=24, method:hf_api=15, method:html=5, quality:full_text=5, quality:metadata_only=31, quality:summary_only=11 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 36 | method:api=8, method:gdelt=1, method:hf_api=27, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 175 | method:api=7, method:arxiv_api=2, method:changelog_snapshot=5, method:gdelt=6, method:github_api=3, method:hf_api=10, method:html=128, method:metadata=4, method:rss=10, quality:full_text=128, quality:metadata_only=22, quality:summary_only=25 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 107 | method:arxiv_api=2, method:gdelt=18, method:github_api=11, method:hf_api=2, method:html=67, method:rss=7, quality:full_text=67, quality:metadata_only=5, quality:summary_only=35 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 22 | method:gdelt=6, method:html=12, method:rss=4, quality:full_text=12, quality:summary_only=10 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 10 | method:gdelt=2, method:html=7, method:rss=1, quality:full_text=7, quality:summary_only=3 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 8 | method:arxiv_api=5, method:html=3, quality:full_text=3, quality:summary_only=5 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 34 | method:gdelt=34, quality:summary_only=34 | - | monitor |
