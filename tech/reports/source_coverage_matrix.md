# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-06T00:53:09.618275+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 111
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'html': 538, 'rss': 27, 'arxiv_api': 8, 'gdelt': 20}
- content_quality_mix: {'summary_only': 81, 'metadata_only': 60, 'full_text': 538}
- real_candidate_count: 679
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 85
- official_org_candidate_count: 63
- weak_metadata_match_count: 13
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5161, 'metadata_only': 0.4839}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 110 | method:api=8, method:changelog_snapshot=4, method:github_api=35, method:hf_api=27, method:html=11, method:metadata=4, method:rss=21, quality:full_text=11, quality:metadata_only=60, quality:summary_only=39 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 566 | method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=20, method:github_api=7, method:html=527, method:rss=3, quality:full_text=527, quality:summary_only=39 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 51 | method:github_api=27, method:hf_api=15, method:html=9, quality:full_text=9, quality:metadata_only=30, quality:summary_only=12 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 36 | method:api=8, method:hf_api=27, method:html=1, quality:full_text=1, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 182 | method:api=8, method:changelog_snapshot=5, method:gdelt=4, method:github_api=1, method:hf_api=9, method:html=139, method:metadata=4, method:rss=12, quality:full_text=139, quality:metadata_only=22, quality:summary_only=21 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 112 | method:arxiv_api=2, method:gdelt=12, method:github_api=10, method:hf_api=3, method:html=80, method:rss=5, quality:full_text=80, quality:metadata_only=6, quality:summary_only=26 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 20 | method:gdelt=2, method:html=18, quality:full_text=18, quality:summary_only=2 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 5 | method:html=5, quality:full_text=5 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 15 | method:arxiv_api=8, method:html=4, method:rss=3, quality:full_text=4, quality:summary_only=11 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 20 | method:gdelt=20, quality:summary_only=20 | - | monitor |
