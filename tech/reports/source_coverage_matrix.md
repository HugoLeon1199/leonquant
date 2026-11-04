# Tech Source Coverage Matrix

- generated_at_utc: 2026-11-04T20:29:46.085694+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 108
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'rss': 27, 'html': 525, 'arxiv_api': 6, 'gdelt': 36}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 95, 'full_text': 525}
- real_candidate_count: 680
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 83
- official_org_candidate_count: 62
- weak_metadata_match_count: 13
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5082, 'metadata_only': 0.4918}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 96 | method:api=5, method:changelog_snapshot=4, method:github_api=31, method:hf_api=27, method:html=5, method:metadata=4, method:rss=20, quality:full_text=5, quality:metadata_only=56, quality:summary_only=35 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 581 | method:api=3, method:arxiv_api=6, method:changelog_snapshot=1, method:gdelt=36, method:github_api=11, method:html=520, method:rss=4, quality:full_text=520, quality:metadata_only=4, quality:summary_only=57 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 49 | method:api=3, method:gdelt=1, method:github_api=22, method:hf_api=17, method:html=6, quality:full_text=6, quality:metadata_only=35, quality:summary_only=8 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 38 | method:api=8, method:gdelt=1, method:hf_api=27, method:rss=2, quality:metadata_only=35, quality:summary_only=3 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 166 | method:api=5, method:changelog_snapshot=5, method:gdelt=3, method:github_api=2, method:hf_api=9, method:html=131, method:metadata=4, method:rss=7, quality:full_text=131, quality:metadata_only=19, quality:summary_only=16 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 129 | method:arxiv_api=2, method:gdelt=29, method:github_api=14, method:hf_api=1, method:html=74, method:rss=9, quality:full_text=74, quality:metadata_only=4, quality:summary_only=51 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 26 | method:gdelt=2, method:html=20, method:rss=4, quality:full_text=20, quality:summary_only=6 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 6 | method:html=5, method:rss=1, quality:full_text=5, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 8 | method:arxiv_api=6, method:html=2, quality:full_text=2, quality:summary_only=6 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 31 | method:gdelt=31, quality:summary_only=31 | - | monitor |
