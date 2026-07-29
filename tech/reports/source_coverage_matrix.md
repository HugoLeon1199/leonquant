# Tech Source Coverage Matrix

- generated_at_utc: 2026-07-29T04:35:24.453884+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 125
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'changelog_snapshot': 5, 'api': 8, 'metadata': 4, 'rss': 28, 'arxiv_api': 6, 'html': 570, 'gdelt': 35}
- content_quality_mix: {'summary_only': 97, 'metadata_only': 58, 'full_text': 570}
- real_candidate_count: 725
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 83
- official_org_candidate_count: 65
- weak_metadata_match_count: 14
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5246, 'metadata_only': 0.4754}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 102 | method:api=7, method:changelog_snapshot=4, method:github_api=33, method:hf_api=27, method:html=5, method:metadata=4, method:rss=22, quality:full_text=5, quality:metadata_only=57, quality:summary_only=40 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 620 | method:api=1, method:arxiv_api=6, method:changelog_snapshot=1, method:gdelt=35, method:github_api=9, method:html=565, method:rss=3, quality:full_text=565, quality:metadata_only=1, quality:summary_only=54 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 44 | method:api=1, method:gdelt=1, method:github_api=23, method:hf_api=15, method:html=4, quality:full_text=4, quality:metadata_only=31, quality:summary_only=9 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 36 | method:api=8, method:gdelt=1, method:hf_api=27, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 191 | method:api=7, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=6, method:github_api=3, method:hf_api=10, method:html=143, method:metadata=4, method:rss=12, quality:full_text=143, quality:metadata_only=22, quality:summary_only=26 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 116 | method:arxiv_api=3, method:gdelt=12, method:github_api=12, method:hf_api=2, method:html=82, method:rss=5, quality:full_text=82, quality:metadata_only=5, quality:summary_only=29 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 22 | method:gdelt=6, method:html=12, method:rss=4, quality:full_text=12, quality:summary_only=10 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 12 | method:gdelt=2, method:html=9, method:rss=1, quality:full_text=9, quality:summary_only=3 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 10 | method:arxiv_api=6, method:html=4, quality:full_text=4, quality:summary_only=6 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 32 | method:gdelt=32, quality:summary_only=32 | - | monitor |
