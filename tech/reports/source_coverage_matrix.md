# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-22T06:11:47.336247+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 125
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'html': 613, 'changelog_snapshot': 4, 'metadata': 6, 'rss': 23, 'arxiv_api': 7, 'gdelt': 48}
- content_quality_mix: {'summary_only': 105, 'metadata_only': 60, 'full_text': 613}
- real_candidate_count: 778
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 59
- weak_metadata_match_count: 13
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5041, 'metadata_only': 0.4959}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 115 | method:api=6, method:changelog_snapshot=3, method:github_api=32, method:hf_api=27, method:html=24, method:metadata=6, method:rss=17, quality:full_text=24, quality:metadata_only=57, quality:summary_only=34 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 660 | method:api=2, method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=48, method:github_api=10, method:html=589, method:rss=3, quality:full_text=589, quality:metadata_only=3, quality:summary_only=68 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 59 | method:api=2, method:gdelt=11, method:github_api=22, method:hf_api=16, method:html=7, method:rss=1, quality:full_text=7, quality:metadata_only=33, quality:summary_only=19 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 37 | method:api=8, method:hf_api=27, method:html=1, method:rss=1, quality:full_text=1, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 173 | method:api=6, method:changelog_snapshot=4, method:gdelt=1, method:github_api=2, method:hf_api=7, method:html=138, method:metadata=6, method:rss=9, quality:full_text=138, quality:metadata_only=19, quality:summary_only=16 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 139 | method:arxiv_api=5, method:gdelt=29, method:github_api=12, method:hf_api=3, method:html=85, method:rss=5, quality:full_text=85, quality:metadata_only=6, quality:summary_only=48 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 17 | method:gdelt=4, method:html=10, method:rss=3, quality:full_text=10, quality:summary_only=7 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 9 | method:gdelt=1, method:html=7, method:rss=1, quality:full_text=7, quality:summary_only=2 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 8 | method:arxiv_api=7, method:html=1, quality:full_text=1, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 37 | method:gdelt=37, quality:summary_only=37 | - | monitor |
