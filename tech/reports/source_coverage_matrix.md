# Tech Source Coverage Matrix

- generated_at_utc: 2026-07-23T15:29:24.944249+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 126
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'html': 674, 'rss': 29, 'arxiv_api': 10, 'gdelt': 47}
- content_quality_mix: {'metadata_only': 58, 'summary_only': 114, 'full_text': 674}
- real_candidate_count: 846
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 87
- official_org_candidate_count: 65
- weak_metadata_match_count: 15
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5397, 'metadata_only': 0.4603}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 106 | method:api=6, method:changelog_snapshot=4, method:github_api=34, method:hf_api=27, method:html=8, method:metadata=4, method:rss=23, quality:full_text=8, quality:metadata_only=56, quality:summary_only=42 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 737 | method:api=2, method:arxiv_api=10, method:changelog_snapshot=1, method:gdelt=47, method:github_api=8, method:html=666, method:rss=3, quality:full_text=666, quality:metadata_only=2, quality:summary_only=69 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 52 | method:api=1, method:arxiv_api=1, method:gdelt=1, method:github_api=24, method:hf_api=15, method:html=10, quality:full_text=10, quality:metadata_only=31, quality:summary_only=11 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 36 | method:api=7, method:gdelt=1, method:hf_api=27, method:html=1, quality:full_text=1, quality:metadata_only=34, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 209 | method:api=7, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=7, method:github_api=2, method:hf_api=10, method:html=159, method:metadata=4, method:rss=14, quality:full_text=159, quality:metadata_only=22, quality:summary_only=28 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 162 | method:arxiv_api=1, method:gdelt=33, method:github_api=12, method:hf_api=2, method:html=108, method:rss=6, quality:full_text=108, quality:metadata_only=5, quality:summary_only=49 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 18 | method:gdelt=3, method:html=11, method:rss=4, quality:full_text=11, quality:summary_only=7 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 14 | method:html=13, method:rss=1, quality:full_text=13, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 12 | method:arxiv_api=10, method:html=2, quality:full_text=2, quality:summary_only=10 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 42 | method:gdelt=42, quality:summary_only=42 | - | monitor |
