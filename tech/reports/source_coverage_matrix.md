# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-23T06:07:08.168268+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 120
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 4, 'metadata': 5, 'rss': 26, 'html': 599, 'arxiv_api': 7, 'gdelt': 50}
- content_quality_mix: {'summary_only': 110, 'metadata_only': 59, 'full_text': 599}
- real_candidate_count: 768
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 61
- weak_metadata_match_count: 11
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5203, 'metadata_only': 0.4797}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 112 | method:api=6, method:changelog_snapshot=3, method:github_api=32, method:hf_api=27, method:html=19, method:metadata=5, method:rss=20, quality:full_text=19, quality:metadata_only=56, quality:summary_only=37 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 653 | method:api=2, method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=50, method:github_api=10, method:html=580, method:rss=3, quality:full_text=580, quality:metadata_only=3, quality:summary_only=70 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 49 | method:api=2, method:gdelt=5, method:github_api=22, method:hf_api=15, method:html=5, quality:full_text=5, quality:metadata_only=32, quality:summary_only=12 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 38 | method:api=8, method:hf_api=27, method:html=3, quality:full_text=3, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 185 | method:api=6, method:arxiv_api=1, method:changelog_snapshot=4, method:gdelt=2, method:github_api=2, method:hf_api=8, method:html=146, method:metadata=5, method:rss=11, quality:full_text=146, quality:metadata_only=19, quality:summary_only=20 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 134 | method:arxiv_api=3, method:gdelt=34, method:github_api=12, method:hf_api=3, method:html=79, method:rss=3, quality:full_text=79, quality:metadata_only=6, quality:summary_only=49 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 23 | method:gdelt=5, method:html=14, method:rss=4, quality:full_text=14, quality:summary_only=9 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 12 | method:gdelt=2, method:html=9, method:rss=1, quality:full_text=9, quality:summary_only=3 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 11 | method:arxiv_api=7, method:html=4, quality:full_text=4, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 45 | method:gdelt=45, quality:summary_only=45 | - | monitor |
