# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-28T06:55:56.669485+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 110
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 4, 'metadata': 6, 'arxiv_api': 9, 'rss': 24, 'html': 589, 'gdelt': 50}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 110, 'full_text': 589}
- real_candidate_count: 759
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 86
- official_org_candidate_count: 61
- weak_metadata_match_count: 11
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5122, 'metadata_only': 0.4878}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 99 | method:api=5, method:changelog_snapshot=3, method:gdelt=1, method:github_api=32, method:hf_api=27, method:html=7, method:metadata=6, method:rss=18, quality:full_text=7, quality:metadata_only=56, quality:summary_only=36 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 657 | method:api=3, method:arxiv_api=9, method:changelog_snapshot=1, method:gdelt=49, method:github_api=10, method:html=582, method:rss=3, quality:full_text=582, quality:metadata_only=4, quality:summary_only=71 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 50 | method:api=3, method:gdelt=2, method:github_api=21, method:hf_api=16, method:html=8, quality:full_text=8, quality:metadata_only=34, quality:summary_only=8 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 41 | method:api=8, method:gdelt=3, method:hf_api=27, method:html=2, method:rss=1, quality:full_text=2, quality:metadata_only=35, quality:summary_only=4 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 180 | method:api=5, method:arxiv_api=3, method:changelog_snapshot=4, method:gdelt=5, method:github_api=2, method:hf_api=8, method:html=138, method:metadata=6, method:rss=9, quality:full_text=138, quality:metadata_only=19, quality:summary_only=23 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 139 | method:arxiv_api=3, method:gdelt=33, method:github_api=12, method:hf_api=2, method:html=85, method:rss=4, quality:full_text=85, quality:metadata_only=5, quality:summary_only=49 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 35 | method:gdelt=7, method:html=25, method:rss=3, quality:full_text=25, quality:summary_only=10 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 14 | method:gdelt=3, method:html=11, quality:full_text=11, quality:summary_only=3 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 8 | method:arxiv_api=7, method:html=1, quality:full_text=1, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 45 | method:gdelt=45, quality:summary_only=45 | - | monitor |
