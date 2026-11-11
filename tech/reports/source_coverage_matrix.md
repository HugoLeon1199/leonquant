# Tech Source Coverage Matrix

- generated_at_utc: 2026-11-11T20:16:14.481017+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 98
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 3, 'rss': 30, 'html': 504, 'arxiv_api': 5, 'gdelt': 52}
- content_quality_mix: {'summary_only': 111, 'metadata_only': 61, 'full_text': 504}
- real_candidate_count: 676
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 82
- official_org_candidate_count: 64
- weak_metadata_match_count: 9
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5041, 'metadata_only': 0.4959}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 98 | method:api=5, method:changelog_snapshot=4, method:github_api=31, method:hf_api=27, method:html=5, method:metadata=3, method:rss=23, quality:full_text=5, quality:metadata_only=58, quality:summary_only=35 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 574 | method:api=3, method:arxiv_api=5, method:changelog_snapshot=1, method:gdelt=52, method:github_api=11, method:html=499, method:rss=3, quality:full_text=499, quality:metadata_only=3, quality:summary_only=72 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 45 | method:api=2, method:github_api=21, method:hf_api=17, method:html=5, quality:full_text=5, quality:metadata_only=34, quality:summary_only=6 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 35 | method:api=7, method:gdelt=1, method:hf_api=27, quality:metadata_only=34, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 169 | method:api=6, method:changelog_snapshot=5, method:gdelt=5, method:github_api=2, method:hf_api=9, method:html=126, method:metadata=3, method:rss=13, quality:full_text=126, quality:metadata_only=19, quality:summary_only=24 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 116 | method:arxiv_api=3, method:gdelt=19, method:github_api=12, method:hf_api=1, method:html=75, method:rss=6, quality:full_text=75, quality:metadata_only=4, quality:summary_only=37 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 30 | method:gdelt=6, method:html=19, method:rss=5, quality:full_text=19, quality:metadata_only=2, quality:summary_only=9 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 7 | method:html=7, quality:full_text=7 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 5 | method:arxiv_api=5, quality:summary_only=5 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 4 | method:rss=4, quality:summary_only=4 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 49 | method:gdelt=49, quality:summary_only=49 | - | monitor |
