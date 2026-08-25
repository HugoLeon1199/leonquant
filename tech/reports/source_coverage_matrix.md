# Tech Source Coverage Matrix

- generated_at_utc: 2026-08-25T14:09:03.566759+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 126
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'rss': 27, 'html': 664, 'arxiv_api': 8, 'gdelt': 35}
- content_quality_mix: {'metadata_only': 59, 'summary_only': 97, 'full_text': 664}
- real_candidate_count: 820
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 85
- official_org_candidate_count: 60
- weak_metadata_match_count: 14
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5242, 'metadata_only': 0.4758}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 106 | method:api=2, method:changelog_snapshot=4, method:github_api=33, method:hf_api=27, method:html=15, method:metadata=4, method:rss=21, quality:full_text=15, quality:metadata_only=53, quality:summary_only=38 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 711 | method:api=6, method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=35, method:github_api=9, method:html=649, method:rss=3, quality:full_text=649, quality:metadata_only=6, quality:summary_only=56 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 51 | method:api=6, method:github_api=24, method:hf_api=16, method:html=5, quality:full_text=5, quality:metadata_only=37, quality:summary_only=9 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 39 | method:api=8, method:hf_api=27, method:html=3, method:rss=1, quality:full_text=3, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 216 | method:api=2, method:arxiv_api=3, method:changelog_snapshot=5, method:gdelt=7, method:github_api=1, method:hf_api=9, method:html=170, method:metadata=4, method:rss=15, quality:full_text=170, quality:metadata_only=16, quality:summary_only=30 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 112 | method:arxiv_api=2, method:gdelt=20, method:github_api=12, method:hf_api=1, method:html=74, method:rss=3, quality:full_text=74, quality:metadata_only=4, quality:summary_only=34 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 22 | method:gdelt=2, method:html=19, method:rss=1, quality:full_text=19, quality:summary_only=3 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 9 | method:html=9, quality:full_text=9 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 13 | method:arxiv_api=8, method:html=4, method:rss=1, quality:full_text=4, quality:summary_only=9 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 33 | method:gdelt=33, quality:summary_only=33 | - | monitor |
