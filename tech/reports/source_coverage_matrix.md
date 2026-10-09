# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-09T07:29:14.437244+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 116
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 5, 'arxiv_api': 10, 'rss': 25, 'html': 603, 'gdelt': 39}
- content_quality_mix: {'metadata_only': 59, 'summary_only': 102, 'full_text': 603}
- real_candidate_count: 764
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 87
- official_org_candidate_count: 62
- weak_metadata_match_count: 13
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5242, 'metadata_only': 0.4758}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 102 | method:api=7, method:changelog_snapshot=4, method:github_api=34, method:hf_api=27, method:html=6, method:metadata=5, method:rss=19, quality:full_text=6, quality:metadata_only=58, quality:summary_only=38 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 659 | method:api=1, method:arxiv_api=10, method:changelog_snapshot=1, method:gdelt=39, method:github_api=8, method:html=597, method:rss=3, quality:full_text=597, quality:metadata_only=1, quality:summary_only=61 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 44 | method:api=1, method:gdelt=2, method:github_api=25, method:hf_api=15, method:html=1, quality:full_text=1, quality:metadata_only=31, quality:summary_only=12 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 37 | method:api=8, method:gdelt=1, method:hf_api=27, method:html=1, quality:full_text=1, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 201 | method:api=7, method:arxiv_api=4, method:changelog_snapshot=5, method:gdelt=8, method:github_api=1, method:hf_api=9, method:html=150, method:metadata=5, method:rss=12, quality:full_text=150, quality:metadata_only=22, quality:summary_only=29 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 129 | method:arxiv_api=4, method:gdelt=23, method:github_api=10, method:hf_api=3, method:html=85, method:rss=4, quality:full_text=85, quality:metadata_only=6, quality:summary_only=38 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 13 | method:gdelt=1, method:html=11, method:rss=1, quality:full_text=11, quality:summary_only=2 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 11 | method:html=11, quality:full_text=11 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 11 | method:arxiv_api=8, method:html=3, quality:full_text=3, quality:summary_only=8 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 35 | method:gdelt=35, quality:summary_only=35 | - | monitor |
