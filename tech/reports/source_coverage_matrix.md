# Tech Source Coverage Matrix

- generated_at_utc: 2026-08-25T02:34:39.300901+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 116
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'rss': 27, 'metadata': 4, 'html': 542, 'arxiv_api': 8, 'gdelt': 28}
- content_quality_mix: {'metadata_only': 59, 'summary_only': 90, 'full_text': 542}
- real_candidate_count: 691
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 85
- official_org_candidate_count: 63
- weak_metadata_match_count: 14
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5242, 'metadata_only': 0.4758}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 105 | method:api=2, method:changelog_snapshot=4, method:github_api=34, method:hf_api=27, method:html=13, method:metadata=4, method:rss=21, quality:full_text=13, quality:metadata_only=53, quality:summary_only=39 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 583 | method:api=6, method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=28, method:github_api=8, method:html=529, method:rss=3, quality:full_text=529, quality:metadata_only=6, quality:summary_only=48 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 48 | method:api=6, method:github_api=23, method:hf_api=16, method:html=3, quality:full_text=3, quality:metadata_only=37, quality:summary_only=8 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 37 | method:api=8, method:hf_api=27, method:html=2, quality:full_text=2, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 185 | method:api=2, method:arxiv_api=3, method:changelog_snapshot=5, method:gdelt=6, method:github_api=3, method:hf_api=9, method:html=142, method:metadata=4, method:rss=11, quality:full_text=142, quality:metadata_only=16, quality:summary_only=27 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 92 | method:arxiv_api=2, method:gdelt=16, method:github_api=12, method:hf_api=1, method:html=58, method:rss=3, quality:full_text=58, quality:metadata_only=4, quality:summary_only=30 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 13 | method:html=12, method:rss=1, quality:full_text=12, quality:summary_only=1 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 7 | method:html=7, quality:full_text=7 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 11 | method:arxiv_api=8, method:html=2, method:rss=1, quality:full_text=2, quality:summary_only=9 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 27 | method:gdelt=27, quality:summary_only=27 | - | monitor |
