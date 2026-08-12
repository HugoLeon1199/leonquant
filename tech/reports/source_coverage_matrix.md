# Tech Source Coverage Matrix

- generated_at_utc: 2026-08-12T20:09:53.096858+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 109
- candidates_by_method: {'github_api': 42, 'rss': 26, 'hf_api': 27, 'changelog_snapshot': 5, 'api': 8, 'metadata': 4, 'html': 523, 'arxiv_api': 7, 'gdelt': 33}
- content_quality_mix: {'metadata_only': 59, 'summary_only': 93, 'full_text': 523}
- real_candidate_count: 675
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 61
- weak_metadata_match_count: 16
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5203, 'metadata_only': 0.4797}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 102 | method:api=4, method:changelog_snapshot=4, method:github_api=34, method:hf_api=27, method:html=9, method:metadata=4, method:rss=20, quality:full_text=9, quality:metadata_only=55, quality:summary_only=38 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 570 | method:api=4, method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=33, method:github_api=8, method:html=514, method:rss=3, quality:full_text=514, quality:metadata_only=4, quality:summary_only=52 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 47 | method:api=4, method:github_api=23, method:hf_api=15, method:html=3, method:rss=2, quality:full_text=3, quality:metadata_only=34, quality:summary_only=10 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 36 | method:api=8, method:hf_api=27, method:rss=1, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 175 | method:api=4, method:arxiv_api=2, method:changelog_snapshot=5, method:gdelt=8, method:github_api=2, method:hf_api=10, method:html=132, method:metadata=4, method:rss=8, quality:full_text=132, quality:metadata_only=19, quality:summary_only=24 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 109 | method:arxiv_api=2, method:gdelt=22, method:github_api=13, method:hf_api=2, method:html=62, method:rss=8, quality:full_text=62, quality:metadata_only=5, quality:summary_only=42 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 20 | method:gdelt=2, method:html=17, method:rss=1, quality:full_text=17, quality:summary_only=3 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 10 | method:gdelt=1, method:html=9, quality:full_text=9, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 10 | method:arxiv_api=6, method:html=3, method:rss=1, quality:full_text=3, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 29 | method:gdelt=29, quality:summary_only=29 | - | monitor |
