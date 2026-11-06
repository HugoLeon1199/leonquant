# Tech Source Coverage Matrix

- generated_at_utc: 2026-11-06T20:01:10.817668+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 106
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 3, 'rss': 30, 'html': 459, 'arxiv_api': 8, 'gdelt': 30}
- content_quality_mix: {'summary_only': 91, 'metadata_only': 62, 'full_text': 459}
- real_candidate_count: 612
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 85
- official_org_candidate_count: 64
- weak_metadata_match_count: 11
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5079, 'metadata_only': 0.4921}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 103 | method:api=5, method:changelog_snapshot=4, method:github_api=31, method:hf_api=27, method:html=9, method:metadata=3, method:rss=24, quality:full_text=9, quality:metadata_only=58, quality:summary_only=36 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 506 | method:api=3, method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=30, method:github_api=11, method:html=450, method:rss=3, quality:full_text=450, quality:metadata_only=4, quality:summary_only=52 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 49 | method:api=3, method:gdelt=3, method:github_api=22, method:hf_api=17, method:html=4, quality:full_text=4, quality:metadata_only=35, quality:summary_only=10 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 37 | method:api=8, method:gdelt=1, method:hf_api=27, method:html=1, quality:full_text=1, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 156 | method:api=5, method:changelog_snapshot=5, method:gdelt=1, method:github_api=2, method:hf_api=9, method:html=119, method:metadata=3, method:rss=12, quality:full_text=119, quality:metadata_only=18, quality:summary_only=19 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 97 | method:arxiv_api=3, method:gdelt=21, method:github_api=13, method:hf_api=1, method:html=54, method:rss=5, quality:full_text=54, quality:metadata_only=4, quality:summary_only=39 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 21 | method:gdelt=3, method:html=12, method:rss=6, quality:full_text=12, quality:metadata_only=3, quality:summary_only=6 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 6 | method:gdelt=1, method:html=4, method:rss=1, quality:full_text=4, quality:summary_only=2 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 14 | method:arxiv_api=8, method:html=6, quality:full_text=6, quality:summary_only=8 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 26 | method:gdelt=26, quality:summary_only=26 | - | monitor |
