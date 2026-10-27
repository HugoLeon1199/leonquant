# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-27T06:22:48.973914+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 114
- candidates_by_method: {'github_api': 42, 'hf_api': 26, 'api': 8, 'changelog_snapshot': 4, 'metadata': 5, 'arxiv_api': 7, 'html': 573, 'rss': 27, 'gdelt': 34}
- content_quality_mix: {'summary_only': 95, 'metadata_only': 58, 'full_text': 573}
- real_candidate_count: 726
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 83
- official_org_candidate_count: 63
- weak_metadata_match_count: 12
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5246, 'metadata_only': 0.4754}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 96 | method:api=5, method:changelog_snapshot=3, method:github_api=33, method:hf_api=26, method:html=3, method:metadata=5, method:rss=21, quality:full_text=3, quality:metadata_only=54, quality:summary_only=39 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 627 | method:api=3, method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=34, method:github_api=9, method:html=570, method:rss=3, quality:full_text=570, quality:metadata_only=4, quality:summary_only=53 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 48 | method:api=3, method:github_api=21, method:hf_api=16, method:html=8, quality:full_text=8, quality:metadata_only=34, quality:summary_only=6 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 38 | method:api=8, method:hf_api=26, method:html=4, quality:full_text=4, quality:metadata_only=34 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 176 | method:api=5, method:arxiv_api=1, method:changelog_snapshot=4, method:gdelt=4, method:github_api=2, method:hf_api=8, method:html=136, method:metadata=5, method:rss=11, quality:full_text=136, quality:metadata_only=18, quality:summary_only=22 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 132 | method:gdelt=24, method:github_api=12, method:hf_api=1, method:html=90, method:rss=5, quality:full_text=90, quality:metadata_only=4, quality:summary_only=38 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 25 | method:gdelt=5, method:html=17, method:rss=3, quality:full_text=17, quality:summary_only=8 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 9 | method:gdelt=1, method:html=7, method:rss=1, quality:full_text=7, quality:summary_only=2 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 6 | method:arxiv_api=6, quality:summary_only=6 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 32 | method:gdelt=32, quality:summary_only=32 | - | monitor |
