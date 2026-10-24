# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-24T06:01:33.562696+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 114
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 4, 'metadata': 5, 'rss': 27, 'html': 516, 'arxiv_api': 7, 'gdelt': 43}
- content_quality_mix: {'summary_only': 104, 'metadata_only': 59, 'full_text': 516}
- real_candidate_count: 679
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 63
- weak_metadata_match_count: 13
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5203, 'metadata_only': 0.4797}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 101 | method:api=5, method:changelog_snapshot=3, method:github_api=34, method:hf_api=27, method:html=6, method:metadata=5, method:rss=21, quality:full_text=6, quality:metadata_only=55, quality:summary_only=40 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 575 | method:api=3, method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=43, method:github_api=8, method:html=510, method:rss=3, quality:full_text=510, quality:metadata_only=4, quality:summary_only=61 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 53 | method:api=3, method:gdelt=4, method:github_api=23, method:hf_api=15, method:html=7, method:rss=1, quality:full_text=7, quality:metadata_only=33, quality:summary_only=13 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 39 | method:api=8, method:hf_api=27, method:html=3, method:rss=1, quality:full_text=3, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 165 | method:api=5, method:arxiv_api=1, method:changelog_snapshot=4, method:gdelt=4, method:github_api=3, method:hf_api=8, method:html=126, method:metadata=5, method:rss=9, quality:full_text=126, quality:metadata_only=18, quality:summary_only=21 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 107 | method:arxiv_api=3, method:gdelt=26, method:github_api=12, method:hf_api=3, method:html=59, method:rss=4, quality:full_text=59, quality:metadata_only=6, quality:summary_only=42 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 25 | method:gdelt=4, method:html=17, method:rss=4, quality:full_text=17, quality:summary_only=8 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 12 | method:gdelt=1, method:html=10, method:rss=1, quality:full_text=10, quality:summary_only=2 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 11 | method:arxiv_api=7, method:html=4, quality:full_text=4, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 39 | method:gdelt=39, quality:summary_only=39 | - | monitor |
