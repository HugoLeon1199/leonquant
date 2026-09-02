# Tech Source Coverage Matrix

- generated_at_utc: 2026-09-02T12:11:08.851825+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 126
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'html': 827, 'rss': 27, 'arxiv_api': 7, 'gdelt': 40}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 100, 'full_text': 827}
- real_candidate_count: 987
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 64
- weak_metadata_match_count: 11
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5122, 'metadata_only': 0.4878}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 103 | method:api=5, method:changelog_snapshot=4, method:github_api=34, method:hf_api=27, method:html=8, method:metadata=4, method:rss=21, quality:full_text=8, quality:metadata_only=57, quality:summary_only=38 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 881 | method:api=3, method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=40, method:github_api=8, method:html=819, method:rss=3, quality:full_text=819, quality:metadata_only=3, quality:summary_only=59 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 46 | method:api=3, method:gdelt=1, method:github_api=24, method:hf_api=16, method:html=2, quality:full_text=2, quality:metadata_only=34, quality:summary_only=10 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 40 | method:api=8, method:gdelt=3, method:hf_api=27, method:html=2, quality:full_text=2, quality:metadata_only=35, quality:summary_only=3 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 260 | method:api=5, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=8, method:github_api=1, method:hf_api=9, method:html=214, method:metadata=4, method:rss=13, quality:full_text=214, quality:metadata_only=19, quality:summary_only=27 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 155 | method:arxiv_api=2, method:gdelt=21, method:github_api=11, method:hf_api=1, method:html=117, method:rss=3, quality:full_text=117, quality:metadata_only=5, quality:summary_only=33 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 36 | method:arxiv_api=1, method:gdelt=6, method:html=27, method:rss=2, quality:full_text=27, quality:summary_only=9 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 23 | method:html=23, quality:full_text=23 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 11 | method:arxiv_api=7, method:html=3, method:rss=1, quality:full_text=3, quality:summary_only=8 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 35 | method:gdelt=35, quality:summary_only=35 | - | monitor |
