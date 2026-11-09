# Tech Source Coverage Matrix

- generated_at_utc: 2026-11-09T23:02:43.135244+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 99
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'changelog_snapshot': 5, 'api': 8, 'metadata': 3, 'rss': 30, 'html': 531, 'gdelt': 45, 'arxiv_api': 7}
- content_quality_mix: {'metadata_only': 62, 'summary_only': 105, 'full_text': 531}
- real_candidate_count: 698
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 64
- weak_metadata_match_count: 11
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.504, 'metadata_only': 0.496}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 106 | method:api=7, method:changelog_snapshot=4, method:github_api=30, method:hf_api=27, method:html=12, method:metadata=3, method:rss=23, quality:full_text=12, quality:metadata_only=60, quality:summary_only=34 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 588 | method:api=1, method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=45, method:github_api=12, method:html=519, method:rss=3, quality:full_text=519, quality:metadata_only=2, quality:summary_only=67 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 48 | method:gdelt=1, method:github_api=22, method:hf_api=18, method:html=7, quality:full_text=7, quality:metadata_only=33, quality:summary_only=8 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 35 | method:api=7, method:hf_api=27, method:html=1, quality:full_text=1, quality:metadata_only=34 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 176 | method:api=8, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=8, method:github_api=2, method:hf_api=9, method:html=129, method:metadata=3, method:rss=11, quality:full_text=129, quality:metadata_only=21, quality:summary_only=26 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 117 | method:arxiv_api=5, method:gdelt=20, method:github_api=12, method:html=75, method:rss=5, quality:full_text=75, quality:metadata_only=3, quality:summary_only=39 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 26 | method:gdelt=3, method:html=17, method:rss=6, quality:full_text=17, quality:metadata_only=2, quality:summary_only=7 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 8 | method:html=6, method:rss=2, quality:full_text=6, quality:summary_only=2 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 11 | method:arxiv_api=7, method:html=4, quality:full_text=4, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 4 | method:rss=4, quality:summary_only=4 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 40 | method:gdelt=40, quality:summary_only=40 | - | monitor |
