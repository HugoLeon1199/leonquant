# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-26T14:22:34.541311+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 111
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 4, 'metadata': 5, 'html': 487, 'rss': 30, 'arxiv_api': 7, 'gdelt': 31}
- content_quality_mix: {'summary_only': 95, 'metadata_only': 59, 'full_text': 487}
- real_candidate_count: 641
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 66
- weak_metadata_match_count: 11
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5203, 'metadata_only': 0.4797}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 97 | method:api=5, method:changelog_snapshot=3, method:github_api=32, method:hf_api=27, method:html=1, method:metadata=5, method:rss=24, quality:full_text=1, quality:metadata_only=55, quality:summary_only=41 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 541 | method:api=3, method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=31, method:github_api=10, method:html=486, method:rss=3, quality:full_text=486, quality:metadata_only=4, quality:summary_only=51 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 48 | method:api=3, method:arxiv_api=3, method:gdelt=3, method:github_api=21, method:hf_api=15, method:html=3, quality:full_text=3, quality:metadata_only=33, quality:summary_only=12 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 39 | method:api=8, method:gdelt=1, method:hf_api=27, method:html=3, quality:full_text=3, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 168 | method:api=5, method:arxiv_api=3, method:changelog_snapshot=4, method:gdelt=2, method:github_api=3, method:hf_api=8, method:html=129, method:metadata=5, method:rss=9, quality:full_text=129, quality:metadata_only=18, quality:summary_only=21 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 98 | method:arxiv_api=2, method:gdelt=14, method:github_api=12, method:hf_api=3, method:html=61, method:rss=6, quality:full_text=61, quality:metadata_only=6, quality:summary_only=31 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 24 | method:gdelt=9, method:html=11, method:rss=4, quality:full_text=11, quality:summary_only=13 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 11 | method:gdelt=1, method:html=9, method:rss=1, quality:full_text=9, quality:summary_only=2 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 7 | method:arxiv_api=6, method:rss=1, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 28 | method:gdelt=28, quality:summary_only=28 | - | monitor |
