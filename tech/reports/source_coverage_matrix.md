# Tech Source Coverage Matrix

- generated_at_utc: 2026-08-11T14:42:58.978272+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 120
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'changelog_snapshot': 5, 'api': 8, 'rss': 28, 'metadata': 4, 'html': 652, 'arxiv_api': 6, 'gdelt': 30}
- content_quality_mix: {'summary_only': 90, 'metadata_only': 60, 'full_text': 652}
- real_candidate_count: 802
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 83
- official_org_candidate_count: 64
- weak_metadata_match_count: 12
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5082, 'metadata_only': 0.4918}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 102 | method:api=5, method:changelog_snapshot=4, method:github_api=33, method:hf_api=27, method:html=7, method:metadata=4, method:rss=22, quality:full_text=7, quality:metadata_only=57, quality:summary_only=38 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 697 | method:api=3, method:arxiv_api=6, method:changelog_snapshot=1, method:gdelt=30, method:github_api=9, method:html=645, method:rss=3, quality:full_text=645, quality:metadata_only=3, quality:summary_only=49 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 47 | method:api=3, method:gdelt=1, method:github_api=22, method:hf_api=15, method:html=5, method:rss=1, quality:full_text=5, quality:metadata_only=33, quality:summary_only=9 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 37 | method:api=8, method:gdelt=1, method:hf_api=27, method:html=1, quality:full_text=1, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 194 | method:api=5, method:arxiv_api=2, method:changelog_snapshot=5, method:gdelt=4, method:github_api=2, method:hf_api=10, method:html=152, method:metadata=4, method:rss=10, quality:full_text=152, quality:metadata_only=20, quality:summary_only=22 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 123 | method:gdelt=18, method:github_api=13, method:hf_api=2, method:html=83, method:rss=7, quality:full_text=83, quality:metadata_only=5, quality:summary_only=35 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 25 | method:arxiv_api=1, method:gdelt=7, method:html=14, method:rss=3, quality:full_text=14, quality:summary_only=11 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 12 | method:html=12, quality:full_text=12 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 7 | method:arxiv_api=6, method:html=1, quality:full_text=1, quality:summary_only=6 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 24 | method:gdelt=24, quality:summary_only=24 | - | monitor |
