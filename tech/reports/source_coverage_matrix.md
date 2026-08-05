# Tech Source Coverage Matrix

- generated_at_utc: 2026-08-05T10:01:20.779783+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 114
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'changelog_snapshot': 5, 'api': 8, 'metadata': 4, 'html': 587, 'arxiv_api': 8, 'rss': 28, 'gdelt': 40}
- content_quality_mix: {'metadata_only': 60, 'summary_only': 102, 'full_text': 587}
- real_candidate_count: 749
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 85
- official_org_candidate_count: 63
- weak_metadata_match_count: 16
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.5161, 'metadata_only': 0.4839}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 102 | method:api=3, method:changelog_snapshot=4, method:github_api=34, method:hf_api=27, method:html=8, method:metadata=4, method:rss=22, quality:full_text=8, quality:metadata_only=55, quality:summary_only=39 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 644 | method:api=5, method:arxiv_api=8, method:changelog_snapshot=1, method:gdelt=40, method:github_api=8, method:html=579, method:rss=3, quality:full_text=579, quality:metadata_only=5, quality:summary_only=60 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 54 | method:api=4, method:gdelt=4, method:github_api=21, method:hf_api=17, method:html=8, quality:full_text=8, quality:metadata_only=36, quality:summary_only=10 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 38 | method:api=7, method:gdelt=2, method:hf_api=27, method:html=2, quality:full_text=2, quality:metadata_only=34, quality:summary_only=2 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 188 | method:api=4, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=6, method:github_api=3, method:hf_api=10, method:html=142, method:metadata=4, method:rss=13, quality:full_text=142, quality:metadata_only=19, quality:summary_only=27 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 128 | method:arxiv_api=4, method:gdelt=26, method:github_api=14, method:html=77, method:rss=7, quality:full_text=77, quality:metadata_only=3, quality:summary_only=48 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 13 | method:arxiv_api=1, method:gdelt=1, method:html=8, method:rss=3, quality:full_text=8, quality:metadata_only=1, quality:summary_only=4 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 12 | method:gdelt=1, method:html=10, method:rss=1, quality:full_text=10, quality:summary_only=2 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 9 | method:arxiv_api=8, method:html=1, quality:full_text=1, quality:summary_only=8 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 36 | method:gdelt=36, quality:summary_only=36 | - | monitor |
