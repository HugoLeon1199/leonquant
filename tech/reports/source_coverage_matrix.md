# Tech Source Coverage Matrix

- generated_at_utc: 2026-11-11T07:49:01.910457+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 110
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 3, 'rss': 29, 'html': 633, 'arxiv_api': 5, 'gdelt': 51}
- content_quality_mix: {'metadata_only': 61, 'summary_only': 109, 'full_text': 633}
- real_candidate_count: 803
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 82
- official_org_candidate_count: 63
- weak_metadata_match_count: 9
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5041, 'metadata_only': 0.4959}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 103 | method:api=5, method:changelog_snapshot=4, method:github_api=31, method:hf_api=27, method:html=11, method:metadata=3, method:rss=22, quality:full_text=11, quality:metadata_only=58, quality:summary_only=34 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 696 | method:api=3, method:arxiv_api=5, method:changelog_snapshot=1, method:gdelt=51, method:github_api=11, method:html=622, method:rss=3, quality:full_text=622, quality:metadata_only=3, quality:summary_only=71 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 41 | method:api=2, method:github_api=21, method:hf_api=16, method:html=2, quality:full_text=2, quality:metadata_only=33, quality:summary_only=6 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 35 | method:api=7, method:hf_api=27, method:html=1, quality:full_text=1, quality:metadata_only=34 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 180 | method:api=6, method:changelog_snapshot=5, method:gdelt=5, method:github_api=2, method:hf_api=9, method:html=143, method:metadata=3, method:rss=7, quality:full_text=143, quality:metadata_only=19, quality:summary_only=18 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 152 | method:arxiv_api=3, method:gdelt=20, method:github_api=12, method:hf_api=2, method:html=108, method:rss=7, quality:full_text=108, quality:metadata_only=5, quality:summary_only=39 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 30 | method:gdelt=6, method:html=17, method:rss=7, quality:full_text=17, quality:metadata_only=2, quality:summary_only=11 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 15 | method:gdelt=2, method:html=13, quality:full_text=13, quality:summary_only=2 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 6 | method:arxiv_api=5, method:html=1, quality:full_text=1, quality:summary_only=5 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 4 | method:rss=4, quality:summary_only=4 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 50 | method:gdelt=50, quality:summary_only=50 | - | monitor |
