# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-16T22:10:04.697440+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 111
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'rss': 28, 'arxiv_api': 8, 'html': 493, 'gdelt': 40}
- content_quality_mix: {'summary_only': 102, 'metadata_only': 60, 'full_text': 493}
- real_candidate_count: 655
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 85
- official_org_candidate_count: 64
- weak_metadata_match_count: 12
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5161, 'metadata_only': 0.4839}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 102 | method:api=8, method:changelog_snapshot=4, method:github_api=35, method:hf_api=27, method:html=2, method:metadata=4, method:rss=22, quality:full_text=2, quality:metadata_only=59, quality:summary_only=41 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 550 | method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=40, method:github_api=7, method:html=491, method:rss=3, quality:full_text=491, quality:metadata_only=1, quality:summary_only=58 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 44 | method:gdelt=1, method:github_api=24, method:hf_api=15, method:html=4, quality:full_text=4, quality:metadata_only=30, quality:summary_only=10 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 39 | method:api=8, method:gdelt=1, method:hf_api=27, method:html=1, method:rss=2, quality:full_text=1, quality:metadata_only=35, quality:summary_only=3 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 153 | method:api=8, method:arxiv_api=3, method:changelog_snapshot=5, method:gdelt=3, method:github_api=2, method:hf_api=9, method:html=107, method:metadata=4, method:rss=12, quality:full_text=107, quality:metadata_only=22, quality:summary_only=24 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 124 | method:arxiv_api=3, method:gdelt=32, method:github_api=13, method:hf_api=3, method:html=66, method:rss=7, quality:full_text=66, quality:metadata_only=6, quality:summary_only=52 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 19 | method:gdelt=2, method:html=14, method:rss=3, quality:full_text=14, quality:summary_only=5 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 14 | method:gdelt=1, method:html=13, quality:full_text=13, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 11 | method:arxiv_api=6, method:html=5, quality:full_text=5, quality:summary_only=6 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 37 | method:gdelt=37, quality:summary_only=37 | - | monitor |
