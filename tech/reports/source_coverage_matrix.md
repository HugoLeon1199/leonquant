# Tech Source Coverage Matrix

- generated_at_utc: 2026-08-21T08:01:59.597997+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 114
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'arxiv_api': 9, 'rss': 26, 'html': 575, 'gdelt': 29}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 90, 'full_text': 575}
- real_candidate_count: 725
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 86
- official_org_candidate_count: 62
- weak_metadata_match_count: 13
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.52, 'metadata_only': 0.48}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 105 | method:api=3, method:changelog_snapshot=4, method:github_api=34, method:hf_api=27, method:html=13, method:metadata=4, method:rss=20, quality:full_text=13, quality:metadata_only=55, quality:summary_only=37 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 617 | method:api=5, method:arxiv_api=9, method:changelog_snapshot=1, method:gdelt=29, method:github_api=8, method:html=562, method:rss=3, quality:full_text=562, quality:metadata_only=5, quality:summary_only=50 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 48 | method:api=5, method:github_api=23, method:hf_api=15, method:html=5, quality:full_text=5, quality:metadata_only=35, quality:summary_only=8 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 38 | method:api=8, method:gdelt=1, method:hf_api=27, method:html=2, quality:full_text=2, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 189 | method:api=3, method:arxiv_api=3, method:changelog_snapshot=5, method:gdelt=5, method:github_api=2, method:hf_api=10, method:html=146, method:metadata=4, method:rss=11, quality:full_text=146, quality:metadata_only=18, quality:summary_only=25 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 105 | method:arxiv_api=3, method:gdelt=18, method:github_api=12, method:hf_api=1, method:html=68, method:rss=3, quality:full_text=68, quality:metadata_only=4, quality:summary_only=33 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 15 | method:gdelt=2, method:html=12, method:rss=1, quality:full_text=12, quality:summary_only=3 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 13 | method:html=13, quality:full_text=13 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 10 | method:arxiv_api=8, method:html=1, method:rss=1, quality:full_text=1, quality:summary_only=9 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 27 | method:gdelt=27, quality:summary_only=27 | - | monitor |
