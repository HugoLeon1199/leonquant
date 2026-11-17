# Tech Source Coverage Matrix

- generated_at_utc: 2026-11-17T09:17:59.362033+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 117
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 3, 'rss': 29, 'arxiv_api': 8, 'html': 622, 'gdelt': 38}
- content_quality_mix: {'metadata_only': 62, 'summary_only': 98, 'full_text': 622}
- real_candidate_count: 782
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 85
- official_org_candidate_count: 63
- weak_metadata_match_count: 12
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5079, 'metadata_only': 0.4921}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 115 | method:api=5, method:changelog_snapshot=4, method:github_api=33, method:hf_api=27, method:html=21, method:metadata=3, method:rss=22, quality:full_text=21, quality:metadata_only=59, quality:summary_only=35 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 663 | method:api=3, method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=38, method:github_api=9, method:html=601, method:rss=3, quality:full_text=601, quality:metadata_only=3, quality:summary_only=59 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 50 | method:api=3, method:arxiv_api=1, method:gdelt=1, method:github_api=22, method:hf_api=17, method:html=6, quality:full_text=6, quality:metadata_only=35, quality:summary_only=9 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 36 | method:api=8, method:hf_api=27, method:html=1, quality:full_text=1, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 184 | method:api=5, method:arxiv_api=2, method:changelog_snapshot=5, method:gdelt=5, method:github_api=1, method:hf_api=9, method:html=147, method:metadata=3, method:rss=7, quality:full_text=147, quality:metadata_only=18, quality:summary_only=19 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 134 | method:arxiv_api=4, method:gdelt=20, method:github_api=13, method:hf_api=1, method:html=90, method:rss=6, quality:full_text=90, quality:metadata_only=4, quality:summary_only=40 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 29 | method:gdelt=2, method:html=22, method:rss=5, quality:full_text=22, quality:metadata_only=2, quality:summary_only=5 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 12 | method:gdelt=1, method:html=11, quality:full_text=11, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 13 | method:arxiv_api=7, method:html=6, quality:full_text=6, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 4 | method:rss=4, quality:summary_only=4 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 37 | method:gdelt=37, quality:summary_only=37 | - | monitor |
