# Tech Source Coverage Matrix

- generated_at_utc: 2026-11-21T20:10:17.523060+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 87
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 3, 'html': 326, 'rss': 33, 'arxiv_api': 7, 'gdelt': 23}
- content_quality_mix: {'summary_only': 85, 'metadata_only': 63, 'full_text': 326}
- real_candidate_count: 474
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 67
- weak_metadata_match_count: 13
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.496, 'metadata_only': 0.504}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 102 | method:api=6, method:changelog_snapshot=4, method:github_api=35, method:hf_api=27, method:metadata=3, method:rss=27, quality:metadata_only=61, quality:summary_only=41 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 369 | method:api=2, method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=23, method:github_api=7, method:html=326, method:rss=3, quality:full_text=326, quality:metadata_only=2, quality:summary_only=41 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 42 | method:api=1, method:gdelt=1, method:github_api=23, method:hf_api=16, method:html=1, quality:full_text=1, quality:metadata_only=32, quality:summary_only=9 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 35 | method:api=7, method:hf_api=27, method:html=1, quality:full_text=1, quality:metadata_only=34 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 148 | method:api=7, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=9, method:github_api=3, method:hf_api=9, method:html=101, method:metadata=3, method:rss=10, quality:full_text=101, quality:metadata_only=21, quality:summary_only=26 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 51 | method:arxiv_api=2, method:gdelt=8, method:github_api=12, method:hf_api=2, method:html=19, method:rss=8, quality:full_text=19, quality:metadata_only=5, quality:summary_only=27 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 9 | method:gdelt=2, method:html=3, method:rss=4, quality:full_text=3, quality:metadata_only=2, quality:summary_only=4 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 9 | method:html=9, quality:full_text=9 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 7 | method:arxiv_api=7, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 22 | method:gdelt=22, quality:summary_only=22 | - | monitor |
