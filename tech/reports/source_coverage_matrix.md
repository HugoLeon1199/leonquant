# Tech Source Coverage Matrix

- generated_at_utc: 2026-11-12T20:53:52.334356+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 107
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 3, 'html': 545, 'rss': 31, 'arxiv_api': 5, 'gdelt': 44}
- content_quality_mix: {'summary_only': 103, 'metadata_only': 62, 'full_text': 545}
- real_candidate_count: 710
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 82
- official_org_candidate_count: 65
- weak_metadata_match_count: 8
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.4959, 'metadata_only': 0.5041}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 104 | method:api=5, method:changelog_snapshot=4, method:github_api=32, method:hf_api=27, method:html=9, method:metadata=3, method:rss=24, quality:full_text=9, quality:metadata_only=59, quality:summary_only=36 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 602 | method:api=3, method:arxiv_api=5, method:changelog_snapshot=1, method:gdelt=44, method:github_api=10, method:html=536, method:rss=3, quality:full_text=536, quality:metadata_only=3, quality:summary_only=63 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 45 | method:api=2, method:gdelt=1, method:github_api=22, method:hf_api=17, method:html=2, method:rss=1, quality:full_text=2, quality:metadata_only=34, quality:summary_only=9 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 36 | method:api=7, method:hf_api=27, method:rss=2, quality:metadata_only=34, quality:summary_only=2 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 183 | method:api=6, method:changelog_snapshot=5, method:gdelt=7, method:github_api=2, method:hf_api=9, method:html=141, method:metadata=3, method:rss=10, quality:full_text=141, quality:metadata_only=19, quality:summary_only=23 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 109 | method:arxiv_api=3, method:gdelt=19, method:github_api=12, method:hf_api=1, method:html=68, method:rss=6, quality:full_text=68, quality:metadata_only=4, quality:summary_only=37 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 24 | method:gdelt=6, method:html=13, method:rss=5, quality:full_text=13, quality:metadata_only=2, quality:summary_only=9 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 5 | method:gdelt=1, method:html=4, quality:full_text=4, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 7 | method:arxiv_api=5, method:html=2, quality:full_text=2, quality:summary_only=5 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 4 | method:rss=4, quality:summary_only=4 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 40 | method:gdelt=40, quality:summary_only=40 | - | monitor |
