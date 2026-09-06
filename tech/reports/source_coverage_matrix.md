# Tech Source Coverage Matrix

- generated_at_utc: 2026-09-06T11:42:44.693760+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 92
- candidates_by_method: {'github_api': 42, 'hf_api': 26, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'html': 372, 'rss': 30, 'gdelt': 47, 'arxiv_api': 8}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 110, 'full_text': 372}
- real_candidate_count: 542
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 64
- weak_metadata_match_count: 14
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5122, 'metadata_only': 0.4878}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 98 | method:api=7, method:changelog_snapshot=4, method:github_api=33, method:hf_api=26, method:metadata=4, method:rss=24, quality:metadata_only=59, quality:summary_only=39 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 441 | method:api=1, method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=47, method:github_api=9, method:html=372, method:rss=3, quality:full_text=372, quality:metadata_only=1, quality:summary_only=68 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 45 | method:api=1, method:gdelt=1, method:github_api=23, method:hf_api=16, method:html=3, method:rss=1, quality:full_text=3, quality:metadata_only=32, quality:summary_only=10 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 35 | method:api=8, method:hf_api=26, method:rss=1, quality:metadata_only=34, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 144 | method:api=7, method:arxiv_api=2, method:changelog_snapshot=5, method:gdelt=7, method:github_api=1, method:hf_api=8, method:html=101, method:metadata=4, method:rss=9, quality:full_text=101, quality:metadata_only=20, quality:summary_only=23 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 82 | method:arxiv_api=1, method:gdelt=33, method:github_api=11, method:hf_api=1, method:html=32, method:rss=4, quality:full_text=32, quality:metadata_only=4, quality:summary_only=46 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 20 | method:gdelt=4, method:html=12, method:rss=4, quality:full_text=12, quality:metadata_only=1, quality:summary_only=7 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 8 | method:html=7, method:rss=1, quality:full_text=7, quality:metadata_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 9 | method:arxiv_api=8, method:rss=1, quality:summary_only=9 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 44 | method:gdelt=44, quality:summary_only=44 | - | monitor |
