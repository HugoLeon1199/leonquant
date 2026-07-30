# Tech Source Coverage Matrix

- generated_at_utc: 2026-07-30T15:27:27.037067+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 129
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'changelog_snapshot': 5, 'api': 8, 'metadata': 4, 'html': 699, 'rss': 27, 'arxiv_api': 8, 'gdelt': 40}
- content_quality_mix: {'summary_only': 101, 'metadata_only': 60, 'full_text': 699}
- real_candidate_count: 860
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 85
- official_org_candidate_count: 62
- weak_metadata_match_count: 13
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5161, 'metadata_only': 0.4839}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 103 | method:api=7, method:changelog_snapshot=4, method:github_api=33, method:hf_api=27, method:html=7, method:metadata=4, method:rss=21, quality:full_text=7, quality:metadata_only=59, quality:summary_only=37 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 754 | method:api=1, method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=40, method:github_api=9, method:html=692, method:rss=3, quality:full_text=692, quality:metadata_only=1, quality:summary_only=61 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 46 | method:api=1, method:gdelt=1, method:github_api=22, method:hf_api=15, method:html=6, method:rss=1, quality:full_text=6, quality:metadata_only=31, quality:summary_only=9 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 36 | method:api=8, method:hf_api=27, method:rss=1, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 213 | method:api=7, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=3, method:github_api=4, method:hf_api=11, method:html=164, method:metadata=4, method:rss=14, quality:full_text=164, quality:metadata_only=23, quality:summary_only=26 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 146 | method:arxiv_api=4, method:gdelt=25, method:github_api=11, method:hf_api=1, method:html=101, method:rss=4, quality:full_text=101, quality:metadata_only=4, quality:summary_only=41 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 36 | method:arxiv_api=1, method:gdelt=7, method:html=26, method:rss=2, quality:full_text=26, quality:metadata_only=1, quality:summary_only=9 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 15 | method:html=14, method:rss=1, quality:full_text=14, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 15 | method:arxiv_api=7, method:html=8, quality:full_text=8, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 38 | method:gdelt=38, quality:summary_only=38 | - | monitor |
