# Tech Source Coverage Matrix

- generated_at_utc: 2026-09-03T05:54:20.932771+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 116
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'rss': 27, 'html': 625, 'arxiv_api': 9, 'gdelt': 37}
- content_quality_mix: {'metadata_only': 61, 'summary_only': 98, 'full_text': 625}
- real_candidate_count: 784
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 86
- official_org_candidate_count: 63
- weak_metadata_match_count: 11
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.512, 'metadata_only': 0.488}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 104 | method:api=8, method:changelog_snapshot=4, method:github_api=33, method:hf_api=27, method:html=7, method:metadata=4, method:rss=21, quality:full_text=7, quality:metadata_only=61, quality:summary_only=36 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 677 | method:arxiv_api=9, method:changelog_snapshot=1, method:gdelt=37, method:github_api=9, method:html=618, method:rss=3, quality:full_text=618, quality:summary_only=59 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 44 | method:github_api=23, method:hf_api=16, method:html=5, quality:full_text=5, quality:metadata_only=31, quality:summary_only=8 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 38 | method:api=8, method:gdelt=1, method:hf_api=27, method:html=1, method:rss=1, quality:full_text=1, quality:metadata_only=35, quality:summary_only=2 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 214 | method:api=8, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=11, method:github_api=1, method:hf_api=9, method:html=162, method:metadata=4, method:rss=13, quality:full_text=162, quality:metadata_only=22, quality:summary_only=30 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 117 | method:arxiv_api=2, method:gdelt=20, method:github_api=11, method:hf_api=1, method:html=80, method:rss=3, quality:full_text=80, quality:metadata_only=5, quality:summary_only=32 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 22 | method:arxiv_api=1, method:gdelt=3, method:html=16, method:rss=2, quality:full_text=16, quality:metadata_only=1, quality:summary_only=5 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 14 | method:gdelt=1, method:html=11, method:rss=2, quality:full_text=11, quality:metadata_only=1, quality:summary_only=2 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 11 | method:arxiv_api=9, method:html=1, method:rss=1, quality:full_text=1, quality:summary_only=10 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 33 | method:gdelt=33, quality:summary_only=33 | - | monitor |
