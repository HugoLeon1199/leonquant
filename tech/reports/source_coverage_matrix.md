# Tech Source Coverage Matrix

- generated_at_utc: 2026-08-14T08:41:40.980142+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 106
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'changelog_snapshot': 5, 'api': 8, 'metadata': 4, 'rss': 27, 'arxiv_api': 7, 'html': 574, 'gdelt': 43}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 103, 'full_text': 574}
- real_candidate_count: 737
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 63
- weak_metadata_match_count: 14
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5122, 'metadata_only': 0.4878}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 102 | method:api=4, method:changelog_snapshot=4, method:github_api=34, method:hf_api=27, method:html=8, method:metadata=4, method:rss=21, quality:full_text=8, quality:metadata_only=56, quality:summary_only=38 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 631 | method:api=4, method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=42, method:github_api=8, method:html=566, method:rss=3, quality:full_text=566, quality:metadata_only=4, quality:summary_only=61 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 56 | method:api=4, method:gdelt=1, method:github_api=24, method:hf_api=15, method:html=10, method:rss=2, quality:full_text=10, quality:metadata_only=34, quality:summary_only=12 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 40 | method:api=8, method:gdelt=1, method:hf_api=27, method:html=2, method:rss=2, quality:full_text=2, quality:metadata_only=35, quality:summary_only=3 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 152 | method:api=4, method:arxiv_api=2, method:changelog_snapshot=5, method:gdelt=6, method:github_api=1, method:hf_api=10, method:html=113, method:metadata=4, method:rss=7, quality:full_text=113, quality:metadata_only=19, quality:summary_only=20 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 120 | method:arxiv_api=2, method:gdelt=25, method:github_api=13, method:hf_api=2, method:html=71, method:rss=7, quality:full_text=71, quality:metadata_only=5, quality:summary_only=44 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 26 | method:gdelt=8, method:html=17, method:rss=1, quality:full_text=17, quality:summary_only=9 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 11 | method:gdelt=1, method:html=9, method:rss=1, quality:full_text=9, quality:summary_only=2 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 10 | method:arxiv_api=6, method:html=3, method:rss=1, quality:full_text=3, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 4 | method:gdelt=1, method:rss=3, quality:summary_only=4 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 40 | method:gdelt=40, quality:summary_only=40 | - | monitor |
