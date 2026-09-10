# Tech Source Coverage Matrix

- generated_at_utc: 2026-09-10T21:43:06.277589+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 98
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'rss': 27, 'html': 565, 'arxiv_api': 7, 'gdelt': 34}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 94, 'full_text': 565}
- real_candidate_count: 719
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 62
- weak_metadata_match_count: 15
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5122, 'metadata_only': 0.4878}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 110 | method:api=7, method:changelog_snapshot=4, method:gdelt=1, method:github_api=33, method:hf_api=27, method:html=13, method:metadata=4, method:rss=21, quality:full_text=13, quality:metadata_only=59, quality:summary_only=38 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 606 | method:api=1, method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=33, method:github_api=9, method:html=552, method:rss=3, quality:full_text=552, quality:metadata_only=1, quality:summary_only=53 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 45 | method:api=1, method:github_api=25, method:hf_api=16, method:html=3, quality:full_text=3, quality:metadata_only=32, quality:summary_only=10 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 37 | method:api=8, method:hf_api=27, method:html=2, quality:full_text=2, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 182 | method:api=7, method:changelog_snapshot=5, method:gdelt=4, method:github_api=1, method:hf_api=9, method:html=141, method:metadata=4, method:rss=11, quality:full_text=141, quality:metadata_only=21, quality:summary_only=20 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 115 | method:arxiv_api=4, method:gdelt=22, method:github_api=11, method:hf_api=1, method:html=72, method:rss=5, quality:full_text=72, quality:metadata_only=4, quality:summary_only=39 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 18 | method:gdelt=5, method:html=13, quality:full_text=13, quality:summary_only=5 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 9 | method:gdelt=1, method:html=7, method:rss=1, quality:full_text=7, quality:metadata_only=1, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 10 | method:arxiv_api=7, method:html=2, method:rss=1, quality:full_text=2, quality:summary_only=8 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 34 | method:gdelt=34, quality:summary_only=34 | - | monitor |
