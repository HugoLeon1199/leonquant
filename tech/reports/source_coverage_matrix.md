# Tech Source Coverage Matrix

- generated_at_utc: 2026-09-11T06:05:55.152811+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 109
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'arxiv_api': 8, 'html': 599, 'rss': 27, 'gdelt': 30}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 91, 'full_text': 599}
- real_candidate_count: 750
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 85
- official_org_candidate_count: 62
- weak_metadata_match_count: 12
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5161, 'metadata_only': 0.4839}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 111 | method:api=7, method:changelog_snapshot=4, method:gdelt=1, method:github_api=33, method:hf_api=27, method:html=14, method:metadata=4, method:rss=21, quality:full_text=14, quality:metadata_only=59, quality:summary_only=38 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 636 | method:api=1, method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=29, method:github_api=9, method:html=585, method:rss=3, quality:full_text=585, quality:metadata_only=1, quality:summary_only=50 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 47 | method:api=1, method:arxiv_api=2, method:github_api=24, method:hf_api=16, method:html=4, quality:full_text=4, quality:metadata_only=32, quality:summary_only=11 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 37 | method:api=8, method:hf_api=27, method:html=2, quality:full_text=2, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 186 | method:api=7, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=4, method:github_api=2, method:hf_api=9, method:html=144, method:metadata=4, method:rss=10, quality:full_text=144, quality:metadata_only=21, quality:summary_only=21 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 119 | method:arxiv_api=2, method:gdelt=20, method:github_api=11, method:hf_api=1, method:html=80, method:rss=5, quality:full_text=80, quality:metadata_only=4, quality:summary_only=35 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 16 | method:gdelt=4, method:html=12, quality:full_text=12, quality:summary_only=4 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 8 | method:html=7, method:rss=1, quality:full_text=7, quality:metadata_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 9 | method:arxiv_api=6, method:html=2, method:rss=1, quality:full_text=2, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 29 | method:gdelt=29, quality:summary_only=29 | - | monitor |
