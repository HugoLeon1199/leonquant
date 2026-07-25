# Tech Source Coverage Matrix

- generated_at_utc: 2026-07-25T14:47:11.565227+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 123
- candidates_by_method: {'github_api': 42, 'hf_api': 26, 'changelog_snapshot': 5, 'api': 8, 'metadata': 4, 'html': 568, 'rss': 27, 'arxiv_api': 10, 'gdelt': 37}
- content_quality_mix: {'metadata_only': 57, 'summary_only': 102, 'full_text': 568}
- real_candidate_count: 727
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 86
- official_org_candidate_count: 63
- weak_metadata_match_count: 15
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.544, 'metadata_only': 0.456}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 101 | method:api=8, method:changelog_snapshot=4, method:github_api=34, method:hf_api=26, method:html=4, method:metadata=4, method:rss=21, quality:full_text=4, quality:metadata_only=57, quality:summary_only=40 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 623 | method:arxiv_api=10, method:changelog_snapshot=1, method:gdelt=37, method:github_api=8, method:html=564, method:rss=3, quality:full_text=564, quality:summary_only=59 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 49 | method:gdelt=1, method:github_api=23, method:hf_api=15, method:html=10, quality:full_text=10, quality:metadata_only=30, quality:summary_only=9 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 40 | method:api=8, method:gdelt=2, method:hf_api=26, method:html=4, quality:full_text=4, quality:metadata_only=34, quality:summary_only=2 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 198 | method:api=8, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=7, method:github_api=3, method:hf_api=10, method:html=147, method:metadata=4, method:rss=13, quality:full_text=147, quality:metadata_only=23, quality:summary_only=28 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 103 | method:arxiv_api=4, method:gdelt=19, method:github_api=12, method:hf_api=1, method:html=64, method:rss=3, quality:full_text=64, quality:metadata_only=4, quality:summary_only=35 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 19 | method:gdelt=3, method:html=12, method:rss=4, quality:full_text=12, quality:summary_only=7 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 11 | method:gdelt=1, method:html=9, method:rss=1, quality:full_text=9, quality:summary_only=2 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 13 | method:arxiv_api=9, method:html=3, method:rss=1, quality:full_text=3, quality:summary_only=10 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 33 | method:gdelt=33, quality:summary_only=33 | - | monitor |
