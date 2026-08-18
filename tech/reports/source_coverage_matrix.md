# Tech Source Coverage Matrix

- generated_at_utc: 2026-08-18T07:58:30.118751+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 108
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'arxiv_api': 7, 'html': 555, 'rss': 28, 'gdelt': 20}
- content_quality_mix: {'summary_only': 81, 'metadata_only': 60, 'full_text': 555}
- real_candidate_count: 696
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 64
- weak_metadata_match_count: 16
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5122, 'metadata_only': 0.4878}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 98 | method:api=3, method:changelog_snapshot=4, method:github_api=34, method:hf_api=27, method:html=4, method:metadata=4, method:rss=22, quality:full_text=4, quality:metadata_only=55, quality:summary_only=39 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 595 | method:api=5, method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=20, method:github_api=8, method:html=551, method:rss=3, quality:full_text=551, quality:metadata_only=5, quality:summary_only=39 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 52 | method:api=5, method:gdelt=1, method:github_api=24, method:hf_api=15, method:html=5, method:rss=2, quality:full_text=5, quality:metadata_only=35, quality:summary_only=12 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 40 | method:api=8, method:hf_api=27, method:html=4, method:rss=1, quality:full_text=4, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 166 | method:api=3, method:arxiv_api=3, method:changelog_snapshot=5, method:gdelt=3, method:github_api=2, method:hf_api=9, method:html=124, method:metadata=4, method:rss=13, quality:full_text=124, quality:metadata_only=17, quality:summary_only=25 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 91 | method:arxiv_api=2, method:gdelt=9, method:github_api=13, method:hf_api=2, method:html=61, method:rss=4, quality:full_text=61, quality:metadata_only=5, quality:summary_only=25 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 19 | method:arxiv_api=1, method:gdelt=4, method:html=14, quality:full_text=14, quality:summary_only=5 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 15 | method:gdelt=3, method:html=12, quality:full_text=12, quality:summary_only=3 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 10 | method:arxiv_api=6, method:html=3, method:rss=1, quality:full_text=3, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 19 | method:gdelt=19, quality:summary_only=19 | - | monitor |
