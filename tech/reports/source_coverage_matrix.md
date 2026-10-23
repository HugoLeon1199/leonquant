# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-23T12:42:03.706554+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 126
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 4, 'metadata': 6, 'rss': 23, 'html': 660, 'arxiv_api': 7, 'gdelt': 47}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 104, 'full_text': 660}
- real_candidate_count: 824
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 60
- weak_metadata_match_count: 11
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5041, 'metadata_only': 0.4959}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 110 | method:api=6, method:changelog_snapshot=3, method:github_api=32, method:hf_api=27, method:html=19, method:metadata=6, method:rss=17, quality:full_text=19, quality:metadata_only=57, quality:summary_only=34 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 711 | method:api=2, method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=47, method:github_api=10, method:html=641, method:rss=3, quality:full_text=641, quality:metadata_only=3, quality:summary_only=67 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 53 | method:api=2, method:gdelt=6, method:github_api=22, method:hf_api=15, method:html=8, quality:full_text=8, quality:metadata_only=32, quality:summary_only=13 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 40 | method:api=8, method:hf_api=27, method:html=5, quality:full_text=5, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 179 | method:api=6, method:arxiv_api=1, method:changelog_snapshot=4, method:gdelt=2, method:github_api=2, method:hf_api=8, method:html=140, method:metadata=6, method:rss=10, quality:full_text=140, quality:metadata_only=20, quality:summary_only=19 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 140 | method:arxiv_api=3, method:gdelt=30, method:github_api=12, method:hf_api=3, method:html=89, method:rss=3, quality:full_text=89, quality:metadata_only=6, quality:summary_only=45 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 26 | method:gdelt=5, method:html=18, method:rss=3, quality:full_text=18, quality:summary_only=8 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 12 | method:gdelt=2, method:html=9, method:rss=1, quality:full_text=9, quality:summary_only=3 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 9 | method:arxiv_api=7, method:html=2, quality:full_text=2, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 41 | method:gdelt=41, quality:summary_only=41 | - | monitor |
