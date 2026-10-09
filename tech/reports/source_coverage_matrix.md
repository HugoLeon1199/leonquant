# Tech Source Coverage Matrix

- generated_at_utc: 2026-10-09T23:20:55.214207+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 118
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 4, 'html': 492, 'arxiv_api': 10, 'rss': 28, 'gdelt': 42}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 106, 'full_text': 492}
- real_candidate_count: 658
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 87
- official_org_candidate_count: 64
- weak_metadata_match_count: 10
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5238, 'metadata_only': 0.4762}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 101 | method:api=7, method:changelog_snapshot=4, method:github_api=34, method:hf_api=27, method:html=3, method:metadata=4, method:rss=22, quality:full_text=3, quality:metadata_only=59, quality:summary_only=39 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 554 | method:api=1, method:arxiv_api=10, method:changelog_snapshot=1, method:gdelt=42, method:github_api=8, method:html=489, method:rss=3, quality:full_text=489, quality:metadata_only=1, quality:summary_only=64 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 45 | method:api=1, method:gdelt=2, method:github_api=25, method:hf_api=15, method:html=2, quality:full_text=2, quality:metadata_only=31, quality:summary_only=12 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 41 | method:api=8, method:gdelt=1, method:hf_api=27, method:html=4, method:rss=1, quality:full_text=4, quality:metadata_only=35, quality:summary_only=2 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 181 | method:api=7, method:arxiv_api=4, method:changelog_snapshot=5, method:gdelt=6, method:github_api=1, method:hf_api=9, method:html=131, method:metadata=4, method:rss=14, quality:full_text=131, quality:metadata_only=21, quality:summary_only=29 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 118 | method:arxiv_api=4, method:gdelt=29, method:github_api=10, method:hf_api=3, method:html=68, method:rss=4, quality:full_text=68, quality:metadata_only=6, quality:summary_only=44 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 15 | method:gdelt=1, method:html=12, method:rss=2, quality:full_text=12, quality:summary_only=3 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 8 | method:html=8, quality:full_text=8 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 9 | method:arxiv_api=8, method:html=1, quality:full_text=1, quality:summary_only=8 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 38 | method:gdelt=38, quality:summary_only=38 | - | monitor |
