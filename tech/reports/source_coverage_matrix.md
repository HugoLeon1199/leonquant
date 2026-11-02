# Tech Source Coverage Matrix

- generated_at_utc: 2026-11-02T22:23:03.549894+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 117
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'rss': 27, 'metadata': 4, 'html': 545, 'gdelt': 24, 'arxiv_api': 6}
- content_quality_mix: {'metadata_only': 62, 'summary_only': 81, 'full_text': 545}
- real_candidate_count: 688
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 83
- official_org_candidate_count: 62
- weak_metadata_match_count: 10
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.4918, 'metadata_only': 0.5082}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 95 | method:api=5, method:changelog_snapshot=4, method:github_api=30, method:hf_api=27, method:html=4, method:metadata=4, method:rss=21, quality:full_text=4, quality:metadata_only=58, quality:summary_only=33 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 590 | method:api=3, method:arxiv_api=6, method:changelog_snapshot=1, method:gdelt=24, method:github_api=12, method:html=541, method:rss=3, quality:full_text=541, quality:metadata_only=4, quality:summary_only=45 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 54 | method:api=3, method:github_api=22, method:hf_api=17, method:html=12, quality:full_text=12, quality:metadata_only=35, quality:summary_only=7 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 38 | method:api=8, method:hf_api=27, method:html=3, quality:full_text=3, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 176 | method:api=5, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=5, method:github_api=2, method:hf_api=10, method:html=135, method:metadata=4, method:rss=9, quality:full_text=135, quality:metadata_only=21, quality:summary_only=20 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 107 | method:arxiv_api=3, method:gdelt=15, method:github_api=13, method:html=71, method:rss=5, quality:full_text=71, quality:metadata_only=3, quality:summary_only=33 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 18 | method:gdelt=2, method:html=11, method:rss=5, quality:full_text=11, quality:metadata_only=2, quality:summary_only=5 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 11 | method:html=10, method:rss=1, quality:full_text=10, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 6 | method:arxiv_api=6, quality:summary_only=6 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 23 | method:gdelt=23, quality:summary_only=23 | - | monitor |
