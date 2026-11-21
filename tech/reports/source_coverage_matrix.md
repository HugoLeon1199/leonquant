# Tech Source Coverage Matrix

- generated_at_utc: 2026-11-21T08:22:14.567050+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 107
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'html': 530, 'rss': 27, 'arxiv_api': 7, 'gdelt': 25}
- content_quality_mix: {'metadata_only': 61, 'summary_only': 84, 'full_text': 530}
- real_candidate_count: 675
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 62
- weak_metadata_match_count: 12
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5041, 'metadata_only': 0.4959}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 104 | method:api=6, method:changelog_snapshot=4, method:github_api=35, method:hf_api=27, method:html=7, method:metadata=4, method:rss=21, quality:full_text=7, quality:metadata_only=59, quality:summary_only=38 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 568 | method:api=2, method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=25, method:github_api=7, method:html=523, method:rss=3, quality:full_text=523, quality:metadata_only=2, quality:summary_only=43 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 48 | method:api=1, method:gdelt=1, method:github_api=23, method:hf_api=16, method:html=6, method:rss=1, quality:full_text=6, quality:metadata_only=32, quality:summary_only=10 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 37 | method:api=7, method:hf_api=27, method:html=1, method:rss=2, quality:full_text=1, quality:metadata_only=34, quality:summary_only=2 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 178 | method:api=7, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=5, method:github_api=3, method:hf_api=9, method:html=135, method:metadata=4, method:rss=9, quality:full_text=135, quality:metadata_only=21, quality:summary_only=22 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 92 | method:arxiv_api=2, method:gdelt=13, method:github_api=12, method:hf_api=2, method:html=58, method:rss=5, quality:full_text=58, quality:metadata_only=5, quality:summary_only=29 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 28 | method:gdelt=1, method:html=23, method:rss=4, quality:full_text=23, quality:metadata_only=2, quality:summary_only=3 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 11 | method:html=11, quality:full_text=11 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 12 | method:arxiv_api=7, method:html=5, quality:full_text=5, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 24 | method:gdelt=24, quality:summary_only=24 | - | monitor |
