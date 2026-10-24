# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-24T16:41:01.124936+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 111
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 4, 'metadata': 6, 'rss': 24, 'html': 582, 'arxiv_api': 7, 'gdelt': 39}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 97, 'full_text': 582}
- real_candidate_count: 739
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 61
- weak_metadata_match_count: 11
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5041, 'metadata_only': 0.4959}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 98 | method:api=5, method:changelog_snapshot=3, method:github_api=33, method:hf_api=27, method:html=6, method:metadata=6, method:rss=18, quality:full_text=6, quality:metadata_only=56, quality:summary_only=36 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 638 | method:api=3, method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=39, method:github_api=9, method:html=576, method:rss=3, quality:full_text=576, quality:metadata_only=4, quality:summary_only=58 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 51 | method:api=3, method:gdelt=4, method:github_api=22, method:hf_api=15, method:html=7, quality:full_text=7, quality:metadata_only=33, quality:summary_only=11 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 40 | method:api=8, method:gdelt=2, method:hf_api=27, method:html=3, quality:full_text=3, quality:metadata_only=35, quality:summary_only=2 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 172 | method:api=5, method:arxiv_api=1, method:changelog_snapshot=4, method:gdelt=2, method:github_api=3, method:hf_api=8, method:html=136, method:metadata=6, method:rss=7, quality:full_text=136, quality:metadata_only=19, quality:summary_only=17 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 109 | method:arxiv_api=3, method:gdelt=22, method:github_api=12, method:hf_api=3, method:html=64, method:rss=5, quality:full_text=64, quality:metadata_only=6, quality:summary_only=39 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 27 | method:gdelt=4, method:html=20, method:rss=3, quality:full_text=20, quality:summary_only=7 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 9 | method:html=8, method:rss=1, quality:full_text=8, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 10 | method:arxiv_api=7, method:html=3, quality:full_text=3, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 35 | method:gdelt=35, quality:summary_only=35 | - | monitor |
