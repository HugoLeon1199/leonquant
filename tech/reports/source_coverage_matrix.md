# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-15T17:50:34.427886+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 101
- candidates_by_method: {'hf_api': 27, 'github_api': 42, 'api': 8, 'changelog_snapshot': 5, 'rss': 26, 'metadata': 4, 'html': 492, 'arxiv_api': 7, 'gdelt': 40}
- content_quality_mix: {'metadata_only': 59, 'summary_only': 100, 'full_text': 492}
- real_candidate_count: 651
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 62
- weak_metadata_match_count: 11
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5122, 'metadata_only': 0.4878}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 108 | method:api=8, method:changelog_snapshot=4, method:github_api=35, method:hf_api=27, method:html=9, method:metadata=4, method:rss=21, quality:full_text=9, quality:metadata_only=59, quality:summary_only=40 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 540 | method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=40, method:github_api=7, method:html=483, method:rss=2, quality:full_text=483, quality:summary_only=57 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 49 | method:gdelt=2, method:github_api=26, method:hf_api=17, method:html=3, method:rss=1, quality:full_text=3, quality:metadata_only=32, quality:summary_only=14 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 36 | method:api=8, method:hf_api=27, method:rss=1, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 145 | method:api=8, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=4, method:github_api=1, method:hf_api=9, method:html=104, method:metadata=4, method:rss=9, quality:full_text=104, quality:metadata_only=22, quality:summary_only=19 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 106 | method:arxiv_api=2, method:gdelt=27, method:github_api=10, method:hf_api=1, method:html=59, method:rss=7, quality:full_text=59, quality:metadata_only=4, quality:summary_only=43 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 22 | method:gdelt=5, method:html=16, method:rss=1, quality:full_text=16, quality:summary_only=6 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 7 | method:html=7, quality:full_text=7 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 7 | method:arxiv_api=7, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 35 | method:gdelt=35, quality:summary_only=35 | - | monitor |
