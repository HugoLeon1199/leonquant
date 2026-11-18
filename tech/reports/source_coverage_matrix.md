# Tech Source Coverage Matrix

- generated_at_utc: 2026-11-18T08:38:18.469998+00:00
- active_url_sources: 63
- active_watchlist_entities: 26
- active_api_sources: 27
- active_rss_sources: 63
- active_sitemap_sources: 0
- metadata_only_sources: 46
- watchlist_checked: 26
- watchlist_hit_count: 116
- candidates_by_method: {'github_api': 42, 'hf_api': 27, 'api': 8, 'changelog_snapshot': 5, 'metadata': 3, 'rss': 29, 'html': 641, 'arxiv_api': 7, 'gdelt': 42}
- content_quality_mix: {'metadata_only': 62, 'summary_only': 101, 'full_text': 641}
- real_candidate_count: 804
- manual_signal_count: 0
- manual_signal_share: 0.0
- real_api_candidate_count: 84
- official_org_candidate_count: 63
- weak_metadata_match_count: 10
- needs_manual_source_strategy_count: 0
- P0 configured/checked/success/failed/zero_hit: 31/31/31/0/0
- missing_critical_entities: []
- verified_timestamp_ratio: 1.0
- full_text/summary/metadata ratio: {'full_text': 0.0, 'summary_only': 0.504, 'metadata_only': 0.496}
- primary/independent/community source counts: 27/63/19

| lane | configured_url_sources | P0 configured/checked/success/failed/zero_hit | watchlist_entities | api_sources | rss_sources | sitemap_sources | candidates collected | content quality / method | blockers | priority fix |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| official_ai_labs | 7 | 11/11/11/0/0 | 26 | 0 | 7 | 0 | 116 | method:api=8, method:changelog_snapshot=4, method:github_api=33, method:hf_api=27, method:html=18, method:metadata=3, method:rss=23, quality:full_text=18, quality:metadata_only=62, quality:summary_only=36 | watchlist entities are not URL crawl sources | add RSS/API/direct metadata strategy |
| independent_ai_news | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 685 | method:arxiv_api=7, method:changelog_snapshot=1, method:gdelt=42, method:github_api=9, method:html=623, method:rss=3, quality:full_text=623, quality:summary_only=62 | - | monitor |
| china_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 45 | method:gdelt=1, method:github_api=23, method:hf_api=16, method:html=5, quality:full_text=5, quality:metadata_only=31, quality:summary_only=9 | - | monitor |
| model_hubs | 0 | 1/1/1/0/0 | 26 | 2 | 0 | 0 | 36 | method:api=8, method:hf_api=27, method:html=1, quality:full_text=1, quality:metadata_only=35 | - | monitor |
| github_releases | 0 | 8/8/8/0/0 | 26 | 13 | 0 | 0 | 42 | method:github_api=42, quality:metadata_only=18, quality:summary_only=24 | - | monitor |
| image_video_ai | 0 | 0/0/0/0/0 | 26 | 0 | 0 | 0 | 189 | method:api=8, method:arxiv_api=1, method:changelog_snapshot=5, method:gdelt=6, method:github_api=1, method:hf_api=10, method:html=146, method:metadata=3, method:rss=9, quality:full_text=146, quality:metadata_only=22, quality:summary_only=21 | - | monitor |
| automation_agents | 0 | 4/4/4/0/0 | 26 | 4 | 0 | 0 | 134 | method:arxiv_api=2, method:gdelt=22, method:github_api=13, method:hf_api=1, method:html=91, method:rss=5, quality:full_text=91, quality:metadata_only=4, quality:summary_only=39 | - | monitor |
| chips_infra | 1 | 4/4/4/0/0 | 0 | 0 | 1 | 0 | 27 | method:gdelt=4, method:html=18, method:rss=5, quality:full_text=18, quality:metadata_only=2, quality:summary_only=7 | - | monitor |
| business_funding | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 14 | method:gdelt=1, method:html=13, quality:full_text=13, quality:summary_only=1 | - | monitor |
| policy_risk | 2 | 3/3/3/0/0 | 0 | 0 | 2 | 0 | 0 | - | - | monitor |
| research_papers | 0 | 0/0/0/0/0 | 0 | 8 | 0 | 0 | 8 | method:arxiv_api=7, method:html=1, quality:full_text=1, quality:summary_only=7 | - | monitor |
| community_forums | 1 | 0/0/0/0/0 | 0 | 0 | 1 | 0 | 3 | method:rss=3, quality:summary_only=3 | - | monitor |
| gdelt | 0 | 0/0/0/0/0 | 0 | 0 | 0 | 0 | 41 | method:gdelt=41, quality:summary_only=41 | - | monitor |
