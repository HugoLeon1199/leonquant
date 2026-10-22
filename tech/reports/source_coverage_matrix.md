# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-22T13:04:16.522581+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 137
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 4, 'html': 684, 'metadata': 5, 'rss': 26, 'arxiv_api': 6, 'gdelt': 52}
- content_quality_mix: {'summary_only': 110, 'metadata_only': 60, 'full_text': 684}
- real_candidate_count: 854
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 83
- official_org_candidate_count: 62
- weak_metadata_match_count: 11
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5082, 'metadata_only': 0.4918}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 118 | method:api=6, method:changelog_snapshot=3, method:github_api=33, method:hf_api=27, method:html=24, method:metadata=5, method:rss=20, quality:full_text=24, quality:metadata_only=57, quality:summary_only=37 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 733 | method:api=2, method:arxiv_api=6, method:changelog_snapshot=1, method:gdelt=52, method:github_api=9, method:html=660, method:rss=3, quality:full_text=660, quality:metadata_only=3, quality:summary_only=70 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 62 | method:api=2, method:gdelt=10, method:github_api=23, method:hf_api=17, method:html=9, method:rss=1, quality:full_text=9, quality:metadata_only=34, quality:summary_only=19 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 37 | method:api=8, method:hf_api=27, method:html=1, method:rss=1, quality:full_text=1, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 187 | method:api=6, method:changelog_snapshot=4, method:gdelt=2, method:github_api=2, method:hf_api=8, method:html=152, method:metadata=5, method:rss=8, quality:full_text=152, quality:metadata_only=19, quality:summary_only=16 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 149 | method:arxiv_api=4, method:gdelt=31, method:github_api=12, method:hf_api=1, method:html=95, method:rss=6, quality:full_text=95, quality:metadata_only=4, quality:summary_only=50 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 18 | method:gdelt=6, method:html=8, method:rss=4, quality:full_text=8, quality:summary_only=10 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 7 | method:gdelt=1, method:html=5, method:rss=1, quality:full_text=5, quality:summary_only=2 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 9 | method:arxiv_api=6, method:html=3, quality:full_text=3, quality:summary_only=6 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 42 | method:gdelt=42, quality:summary_only=42 | - | monitor |
