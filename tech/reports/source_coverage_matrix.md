# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-21T22:26:03.469045+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 123
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 4, 'metadata': 6, 'rss': 23, 'html': 575, 'arxiv_api': 7, 'gdelt': 45}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 102, 'full_text': 575}
- real_candidate_count: 737
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 60
- weak_metadata_match_count: 13
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5041, 'metadata_only': 0.4959}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 109 | method:api=6, method:changelog_snapshot=3, method:github_api=34, method:hf_api=27, method:html=16, method:metadata=6, method:rss=17, quality:full_text=16, quality:metadata_only=57, quality:summary_only=36 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 625 | method:api=2, method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=45, method:github_api=8, method:html=559, method:rss=3, quality:full_text=559, quality:metadata_only=3, quality:summary_only=63 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 55 | method:api=2, method:gdelt=8, method:github_api=24, method:hf_api=15, method:html=6, quality:full_text=6, quality:metadata_only=32, quality:summary_only=17 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 35 | method:api=8, method:hf_api=27, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 172 | method:api=6, method:arxiv_api=2, method:changelog_snapshot=4, method:gdelt=3, method:github_api=2, method:hf_api=8, method:html=133, method:metadata=6, method:rss=8, quality:full_text=133, quality:metadata_only=20, quality:summary_only=19 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 131 | method:arxiv_api=2, method:gdelt=27, method:github_api=12, method:hf_api=3, method:html=81, method:rss=6, quality:full_text=81, quality:metadata_only=6, quality:summary_only=44 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 22 | method:arxiv_api=1, method:gdelt=5, method:html=12, method:rss=4, quality:full_text=12, quality:summary_only=10 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 7 | method:html=6, method:rss=1, quality:full_text=6, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 7 | method:arxiv_api=6, method:html=1, quality:full_text=1, quality:summary_only=6 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 37 | method:gdelt=37, quality:summary_only=37 | - | monitor |
