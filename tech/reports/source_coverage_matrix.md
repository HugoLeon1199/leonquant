# Tech Source Coverage Matrix

- generated_at_utc: 2026-09-01T12:39:01.699937+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 132
- candidates_by_method: {'hf_api': 27, 'github_api': 42, 'api': 8, 'changelog_snapshot': 5, 'metadata': 5, 'arxiv_api': 10, 'html': 643, 'rss': 23, 'gdelt': 24}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 84, 'full_text': 643}
- real_candidate_count: 787
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 87
- official_org_candidate_count: 61
- weak_metadata_match_count: 15
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5161, 'metadata_only': 0.4839}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 99 | method:api=3, method:changelog_snapshot=4, method:github_api=35, method:hf_api=27, method:html=6, method:metadata=4, method:rss=20, quality:full_text=6, quality:metadata_only=54, quality:summary_only=39 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 687 | method:api=5, method:arxiv_api=10, method:changelog_snapshot=1, method:gdelt=24, method:github_api=7, method:html=637, method:rss=3, quality:full_text=637, quality:metadata_only=5, quality:summary_only=45 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 49 | method:api=5, method:arxiv_api=1, method:gdelt=1, method:github_api=24, method:hf_api=16, method:html=2, quality:full_text=2, quality:metadata_only=36, quality:summary_only=11 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 38 | method:api=8, method:gdelt=2, method:hf_api=27, method:html=1, quality:full_text=1, quality:metadata_only=35, quality:summary_only=2 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 221 | method:api=3, method:arxiv_api=3, method:changelog_snapshot=5, method:gdelt=7, method:github_api=2, method:hf_api=10, method:html=176, method:metadata=5, method:rss=10, quality:full_text=176, quality:metadata_only=19, quality:summary_only=26 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 87 | method:arxiv_api=1, method:gdelt=11, method:github_api=11, method:html=62, method:rss=2, quality:full_text=62, quality:metadata_only=3, quality:summary_only=22 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 19 | method:arxiv_api=1, method:gdelt=2, method:html=15, method:rss=1, quality:full_text=15, quality:summary_only=4 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 16 | method:html=15, method:rss=1, quality:full_text=15, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 9 | method:arxiv_api=7, method:html=1, method:rss=1, quality:full_text=1, quality:summary_only=8 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 1 | method:metadata=1, quality:metadata_only=1 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 20 | method:gdelt=20, quality:summary_only=20 | - | monitor |
