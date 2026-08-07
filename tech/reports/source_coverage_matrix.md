# Tech Source Coverage Matrix

- generated_at_utc: 2026-08-07T20:06:40.401131+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 116
- candidates_by_method: {'github_api': 42, 'hf_api': 26, 'changelog_snapshot': 5, 'api': 8, 'metadata': 4, 'html': 436, 'arxiv_api': 7, 'rss': 27, 'gdelt': 37}
- content_quality_mix: {'summary_only': 97, 'metadata_only': 59, 'full_text': 436}
- real_candidate_count: 592
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 83
- official_org_candidate_count: 63
- weak_metadata_match_count: 13
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5164, 'metadata_only': 0.4836}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 97 | method:api=3, method:changelog_snapshot=4, method:github_api=34, method:hf_api=26, method:html=5, method:metadata=4, method:rss=21, quality:full_text=5, quality:metadata_only=54, quality:summary_only=38 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 492 | method:api=5, method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=37, method:github_api=8, method:html=431, method:rss=3, quality:full_text=431, quality:metadata_only=5, quality:summary_only=56 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 54 | method:api=4, method:gdelt=2, method:github_api=22, method:hf_api=16, method:html=9, method:rss=1, quality:full_text=9, quality:metadata_only=35, quality:summary_only=10 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 41 | method:api=7, method:gdelt=1, method:hf_api=26, method:html=5, method:rss=2, quality:full_text=5, quality:metadata_only=33, quality:summary_only=3 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 153 | method:api=4, method:arxiv_api=3, method:changelog_snapshot=5, method:gdelt=2, method:github_api=3, method:hf_api=10, method:html=110, method:metadata=4, method:rss=12, quality:full_text=110, quality:metadata_only=19, quality:summary_only=24 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 101 | method:arxiv_api=2, method:gdelt=30, method:github_api=13, method:html=52, method:rss=4, quality:full_text=52, quality:metadata_only=3, quality:summary_only=46 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 14 | method:arxiv_api=1, method:gdelt=3, method:html=8, method:rss=2, quality:full_text=8, quality:summary_only=6 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 12 | method:html=11, method:rss=1, quality:full_text=11, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 9 | method:arxiv_api=6, method:html=3, quality:full_text=3, quality:summary_only=6 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 32 | method:gdelt=32, quality:summary_only=32 | - | monitor |
