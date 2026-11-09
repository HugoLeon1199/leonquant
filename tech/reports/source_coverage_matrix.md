# Tech Source Coverage Matrix

- generated_at_utc: 2026-11-09T08:03:17.228815+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 86
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'html': 351, 'rss': 30, 'arxiv_api': 7, 'gdelt': 31}
- content_quality_mix: {'metadata_only': 62, 'summary_only': 92, 'full_text': 351}
- real_candidate_count: 505
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 65
- weak_metadata_match_count: 9
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.4959, 'metadata_only': 0.5041}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 99 | method:api=6, method:changelog_snapshot=4, method:github_api=31, method:hf_api=27, method:html=4, method:metadata=4, method:rss=23, quality:full_text=4, quality:metadata_only=59, quality:summary_only=36 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 403 | method:api=2, method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=31, method:github_api=11, method:html=347, method:rss=4, quality:full_text=347, quality:metadata_only=3, quality:summary_only=53 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 45 | method:api=2, method:gdelt=2, method:github_api=21, method:hf_api=16, method:html=4, quality:full_text=4, quality:metadata_only=33, quality:summary_only=8 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 35 | method:api=8, method:hf_api=27, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 152 | method:api=6, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=5, method:github_api=2, method:hf_api=9, method:html=107, method:metadata=4, method:rss=13, quality:full_text=107, quality:metadata_only=20, quality:summary_only=25 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 69 | method:arxiv_api=5, method:gdelt=6, method:github_api=13, method:hf_api=2, method:html=38, method:rss=5, quality:full_text=38, quality:metadata_only=5, quality:summary_only=26 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 18 | method:gdelt=1, method:html=11, method:rss=6, quality:full_text=11, quality:metadata_only=3, quality:summary_only=4 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 5 | method:gdelt=1, method:html=3, method:rss=1, quality:full_text=3, quality:summary_only=2 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 10 | method:arxiv_api=7, method:html=3, quality:full_text=3, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 28 | method:gdelt=28, quality:summary_only=28 | - | monitor |
