# Tech Source Coverage Matrix

- generated_at_utc: 2026-11-19T08:53:19.311371+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 103
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'rss': 30, 'changelog_snapshot': 5, 'metadata': 3, 'arxiv_api': 8, 'html': 627, 'gdelt': 41}
- content_quality_mix: {'metadata_only': 63, 'summary_only': 101, 'full_text': 627}
- real_candidate_count: 791
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 85
- official_org_candidate_count: 64
- weak_metadata_match_count: 9
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5, 'metadata_only': 0.5}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 112 | method:api=8, method:changelog_snapshot=4, method:github_api=33, method:hf_api=27, method:html=13, method:metadata=3, method:rss=24, quality:full_text=13, quality:metadata_only=63, quality:summary_only=36 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 676 | method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=41, method:github_api=9, method:html=614, method:rss=3, quality:full_text=614, quality:summary_only=62 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 43 | method:gdelt=2, method:github_api=23, method:hf_api=15, method:html=3, quality:full_text=3, quality:metadata_only=30, quality:summary_only=10 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 36 | method:api=8, method:gdelt=1, method:hf_api=27, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 195 | method:api=8, method:arxiv_api=3, method:changelog_snapshot=5, method:gdelt=8, method:github_api=1, method:hf_api=9, method:html=147, method:metadata=3, method:rss=11, quality:full_text=147, quality:metadata_only=22, quality:summary_only=26 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 135 | method:arxiv_api=3, method:gdelt=26, method:github_api=12, method:hf_api=3, method:html=86, method:rss=5, quality:full_text=86, quality:metadata_only=6, quality:summary_only=43 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 24 | method:gdelt=3, method:html=17, method:rss=4, quality:full_text=17, quality:metadata_only=2, quality:summary_only=5 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 13 | method:html=12, method:rss=1, quality:full_text=12, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 8 | method:arxiv_api=7, method:html=1, quality:full_text=1, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 39 | method:gdelt=39, quality:summary_only=39 | - | monitor |
