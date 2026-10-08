# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-08T07:30:57.734475+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 123
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 5, 'arxiv_api': 8, 'rss': 23, 'html': 630, 'gdelt': 43}
- content_quality_mix: {'metadata_only': 59, 'summary_only': 102, 'full_text': 630}
- real_candidate_count: 791
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 85
- official_org_candidate_count: 60
- weak_metadata_match_count: 11
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5164, 'metadata_only': 0.4836}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 108 | method:api=8, method:changelog_snapshot=4, method:github_api=35, method:hf_api=27, method:html=12, method:metadata=5, method:rss=17, quality:full_text=12, quality:metadata_only=59, quality:summary_only=37 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 680 | method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=43, method:github_api=7, method:html=618, method:rss=3, quality:full_text=618, quality:summary_only=62 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 53 | method:arxiv_api=1, method:gdelt=4, method:github_api=26, method:hf_api=15, method:html=6, method:rss=1, quality:full_text=6, quality:metadata_only=30, quality:summary_only=17 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 37 | method:api=8, method:hf_api=27, method:html=1, method:rss=1, quality:full_text=1, quality:metadata_only=35, quality:summary_only=1 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 217 | method:api=8, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=9, method:github_api=1, method:hf_api=9, method:html=167, method:metadata=5, method:rss=12, quality:full_text=167, quality:metadata_only=23, quality:summary_only=27 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 131 | method:arxiv_api=2, method:gdelt=23, method:github_api=10, method:hf_api=3, method:html=90, method:rss=3, quality:full_text=90, quality:metadata_only=6, quality:summary_only=35 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 13 | method:arxiv_api=1, method:gdelt=2, method:html=9, method:rss=1, quality:full_text=9, quality:summary_only=4 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 8 | method:html=8, quality:full_text=8 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 9 | method:arxiv_api=7, method:html=2, quality:full_text=2, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 34 | method:gdelt=34, quality:summary_only=34 | - | monitor |
