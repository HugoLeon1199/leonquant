# Tech Source Coverage Matrix

- generated_at_utc: 2026-11-10T08:29:58.967756+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 101
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'changelog_snapshot': 5, 'api': 8, 'metadata': 3, 'arxiv_api': 8, 'rss': 30, 'html': 575, 'gdelt': 45}
- content_quality_mix: {'metadata_only': 62, 'summary_only': 106, 'full_text': 575}
- real_candidate_count: 743
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 85
- official_org_candidate_count: 63
- weak_metadata_match_count: 10
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5079, 'metadata_only': 0.4921}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 107 | method:api=6, method:changelog_snapshot=4, method:github_api=31, method:hf_api=27, method:html=13, method:metadata=3, method:rss=23, quality:full_text=13, quality:metadata_only=59, quality:summary_only=35 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 632 | method:api=2, method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=45, method:github_api=11, method:html=562, method:rss=3, quality:full_text=562, quality:metadata_only=3, quality:summary_only=67 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 46 | method:api=1, method:gdelt=1, method:github_api=22, method:hf_api=16, method:html=6, quality:full_text=6, quality:metadata_only=32, quality:summary_only=8 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 37 | method:api=7, method:hf_api=27, method:html=2, method:rss=1, quality:full_text=2, quality:metadata_only=34, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 176 | method:api=7, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=6, method:github_api=2, method:hf_api=9, method:html=130, method:metadata=3, method:rss=13, quality:full_text=130, quality:metadata_only=20, quality:summary_only=26 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 125 | method:arxiv_api=6, method:gdelt=19, method:github_api=12, method:hf_api=2, method:html=81, method:rss=5, quality:full_text=81, quality:metadata_only=5, quality:summary_only=39 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 23 | method:gdelt=3, method:html=15, method:rss=5, quality:full_text=15, quality:metadata_only=2, quality:summary_only=6 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 13 | method:gdelt=1, method:html=10, method:rss=2, quality:full_text=10, quality:summary_only=3 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 12 | method:arxiv_api=7, method:html=5, quality:full_text=5, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 4 | method:rss=4, quality:summary_only=4 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 43 | method:gdelt=43, quality:summary_only=43 | - | monitor |
