# Tech Source Coverage Matrix

- generated_at_utc: 2026-11-24T11:02:31.199206+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 118
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 3, 'arxiv_api': 9, 'rss': 32, 'html': 629, 'gdelt': 36}
- content_quality_mix: {'metadata_only': 62, 'summary_only': 100, 'full_text': 629}
- real_candidate_count: 791
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 86
- official_org_candidate_count: 65
- weak_metadata_match_count: 12
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5118, 'metadata_only': 0.4882}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 103 | method:api=6, method:changelog_snapshot=4, method:github_api=35, method:hf_api=27, method:html=2, method:metadata=3, method:rss=26, quality:full_text=2, quality:metadata_only=60, quality:summary_only=41 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 685 | method:api=2, method:arxiv_api=9, method:changelog_snapshot=1, method:gdelt=36, method:github_api=7, method:html=627, method:rss=3, quality:full_text=627, quality:metadata_only=2, quality:summary_only=56 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 44 | method:api=1, method:arxiv_api=1, method:github_api=22, method:hf_api=15, method:html=5, quality:full_text=5, quality:metadata_only=31, quality:summary_only=8 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 37 | method:api=7, method:hf_api=27, method:html=2, method:rss=1, quality:full_text=2, quality:metadata_only=34, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 207 | method:api=7, method:arxiv_api=4, method:changelog_snapshot=5, method:gdelt=11, method:github_api=4, method:hf_api=10, method:html=151, method:metadata=3, method:rss=12, quality:full_text=151, quality:metadata_only=22, quality:summary_only=34 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 120 | method:arxiv_api=3, method:gdelt=12, method:github_api=12, method:hf_api=2, method:html=81, method:rss=10, quality:full_text=81, quality:metadata_only=5, quality:summary_only=34 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 26 | method:gdelt=5, method:html=17, method:rss=4, quality:full_text=17, quality:metadata_only=2, quality:summary_only=7 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 8 | method:html=8, quality:full_text=8 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 14 | method:arxiv_api=8, method:html=5, method:rss=1, quality:full_text=5, quality:summary_only=9 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 36 | method:gdelt=36, quality:summary_only=36 | - | monitor |
