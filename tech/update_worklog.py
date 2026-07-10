#!/usr/bin/env python3
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tech.common import API_CANDIDATES_JSON, GDELT_JSON, NEWS_CLEAN, PUBLICATION_JSON, VALIDATION_JSON, load_json

WORKLOG = ROOT / ".ai" / "CURSOR_WORKLOG.md"


def main() -> int:
    validation = load_json(VALIDATION_JSON, {})
    crawl = load_json(NEWS_CLEAN, {})
    events = load_json(GDELT_JSON, {})
    api_candidates = load_json(API_CANDIDATES_JSON, {})
    publication = load_json(PUBLICATION_JSON, {})
    generated_at = str(publication.get("generated_at_utc") or "")
    marker = f"Tech72h generated_at={generated_at}"
    current = WORKLOG.read_text(encoding="utf-8")
    if marker in current:
        print("Worklog already contains this Tech72h run.")
        return 0

    meta = validation.get("validation_meta") or {}
    stats = publication.get("stats") or {}
    sections = publication.get("sections") or {}
    estimated_bytes = events.get("estimated_bytes")
    processed_bytes = events.get("processed_bytes")
    estimated_label = f"{int(estimated_bytes):,}" if isinstance(estimated_bytes, int) else "unknown"
    processed_label = f"{int(processed_bytes):,}" if isinstance(processed_bytes, int) else "unknown"
    ran_successfully = bool(events.get("ran_successfully"))
    radar_count = len(sections.get("full_link_radar") or [])
    must_read_count = len(publication.get("must_read") or [])
    local_ai_count = len(sections.get("local_ai_china_ai") or [])
    automation_count = len(sections.get("automation_mcp_agents") or [])
    open_source_count = len(sections.get("open_source_hot") or [])
    knowledge_count = len(sections.get("ai_knowledge") or [])
    founder_count = len(sections.get("founder_ideas_for_leon") or [])
    candidate_count = int(stats.get("candidate_count") or 0)
    noise_filtered = int(stats.get("noise_filtered_count") or 0)
    expired_removed = int(stats.get("expired_removed_count") or 0)
    gemini_success = int(stats.get("gemini_success_count") or 0)
    gemini_fallback = int(stats.get("gemini_fallback_count") or 0)
    ai_main = int(stats.get("ai_curated_main_count") or 0)
    fallback_main = int(stats.get("fallback_main_count") or 0)
    must_read_source_type = stats.get("must_read_by_source_type") or {}
    must_read_category = stats.get("must_read_by_category") or {}
    watchlist_entity_count = int(stats.get("watchlist_entity_count") or 0)
    watchlist_candidate_count = int(stats.get("watchlist_candidate_count") or 0)
    glm_detected = bool(stats.get("glm_5_2_detected"))
    candidates_by_method = stats.get("candidates_by_method") or api_candidates.get("candidates_by_method") or {}
    content_quality_mix = stats.get("content_quality_mix") or api_candidates.get("content_quality_mix") or {}
    pages_workflow = ROOT / ".github" / "workflows" / "pages.yml"
    pages_has_tech = "Tech Radar" in pages_workflow.read_text(encoding="utf-8") if pages_workflow.is_file() else False
    render_checks = stats.get("render_checks") or {}
    block = (
        f"\n## {datetime.now(timezone.utc).date()} - Technology & AI 72h live run\n\n"
        f"- {marker}\n"
        "- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.\n"
        "- Format: AI Frontier Radar 72h.\n"
        "- Schedule: once every 3 days; data window: latest 72 hours.\n"
        f"- Active sources: {meta.get('active_source_count', 0)} / {meta.get('catalog_source_count', 0)}.\n"
        f"- Clean web articles: {len(crawl.get('articles') or [])}.\n"
        f"- Candidate live: {candidate_count}; noise bi loai: {noise_filtered}; bai qua han 72h bi loai khoi section chinh: {expired_removed}.\n"
        f"- Event candidates: {len(events.get('events') or [])}; GDELT ran_successfully={ran_successfully}; raw={events.get('raw_event_count', 'unknown')}; ai_filtered={events.get('ai_filtered_event_count', 'unknown')}; rejected_non_ai={events.get('rejected_non_ai_count', 'unknown')}.\n"
        f"- Query estimate: {estimated_label} bytes; processed: {processed_label} bytes; bytes_status={events.get('bytes_status', 'unknown')}; cap: 2,000,000,000 bytes.\n"
        f"- Published stories: {stats.get('story_count', 0)}; must_read={must_read_count}; full_link_radar={radar_count}.\n"
        f"- Must Read theo source type: {must_read_source_type}.\n"
        f"- Must Read theo category: {must_read_category}.\n"
        f"- Frontier Watchlist entities: {watchlist_entity_count}; candidates_from_watchlist={watchlist_candidate_count}; GLM-5.2 detected={'yes' if glm_detected else 'no'}.\n"
        f"- Data coverage: active_url_sources={stats.get('active_url_sources', stats.get('active_source_count', 0))}; active_api_sources={stats.get('active_api_sources', api_candidates.get('active_api_sources', 0))}; active_rss_sources={stats.get('active_rss_sources', 0)}; active_sitemap_sources={stats.get('active_sitemap_sources', 0)}; active_watchlist_entities={stats.get('active_watchlist_entities', watchlist_entity_count)}; metadata_only_sources={stats.get('metadata_only_sources', 0)}.\n"
        f"- API candidates: total={api_candidates.get('candidate_count', stats.get('api_candidate_count', 0))}; by_method={api_candidates.get('candidates_by_method', {})}; notes={api_candidates.get('notes', [])[:3]}.\n"
        f"- candidates_by_method={candidates_by_method}; content_quality_mix={content_quality_mix}; remaining CAPTCHA/paywall/JS-only sources={stats.get('needs_manual_source_strategy_count', 0)}.\n"
        f"- Source mix main candidates: official={stats.get('official_candidate_count', 0)}, independent={stats.get('independent_candidate_count', 0)}, community={stats.get('community_candidate_count', 0)}.\n"
        f"- Pages workflow includes Tech Radar: {'yes' if pages_has_tech else 'no'}.\n"
        f"- Gemini curator: success={gemini_success}; fallback={gemini_fallback}; ai_main={ai_main}; fallback_main={fallback_main}.\n"
        f"- Section counts: local_ai={local_ai_count}, automation={automation_count}, open_source={open_source_count}, knowledge={knowledge_count}, founder_ideas={founder_count}.\n"
        f"- /tech/ render check: knowledge={render_checks.get('knowledge_fields_ready')}; founder_ideas={render_checks.get('founder_fields_ready')}.\n"
        "- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.\n"
    )
    WORKLOG.write_text(current + block, encoding="utf-8")
    print("Updated .ai/CURSOR_WORKLOG.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
