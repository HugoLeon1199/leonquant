#!/usr/bin/env python3
"""Validate AI Frontier Radar 72h publication quality."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from scripts.tech_common import (
    TECH_API_CANDIDATES,
    TECH_FRONTIER_WATCHLIST,
    TECH_GDELT_OUTPUT,
    TECH_NEWS_FOR_AI_CLEAN,
    TECH_PUBLICATION_OUTPUT,
    TECH_ROLLING_CANDIDATES,
    TECH_SOURCE_REGISTRY,
    TECH_WATCHLIST_STATUS,
)

SCHEMA_VERSION = "ai-frontier-radar-72h-v1"
WINDOW_HOURS = 72
ALLOWED_CATEGORIES = {
    "model",
    "local_ai",
    "tool",
    "automation",
    "mcp",
    "agent",
    "opensource",
    "business",
    "knowledge",
    "industry",
}
REQUIRED_SECTION_KEYS = {
    "ai_models",
    "local_ai_china_ai",
    "ai_tools",
    "automation_mcp_agents",
    "open_source_hot",
    "ai_business_money",
    "industry_impact",
    "ai_knowledge",
    "founder_ideas_for_leon",
    "full_link_radar",
}
FORBIDDEN_TERMS = ("pipeline", "crawler", "gdelt", "gemini", "bigquery")
ALLOWED_SOURCE_LANES = {
    "normal_web",
    "gdelt",
    "frontier_watchlist",
    "model_hub",
    "github_release",
    "huggingface_model",
    "image_video_workflow",
    "research_papers",
    "community",
}
ALLOWED_CONTENT_QUALITY = {"full_text", "summary_only", "metadata_only"}
ALLOWED_RAW_SOURCE_METHODS = {"api", "rss", "sitemap", "html", "gdelt", "github_api", "hf_api", "arxiv_api", "manual_signal", "static_html", "json_ld", "changelog_snapshot", "metadata"}
ALLOWED_MATCH_STRENGTH = {"strong", "medium", "weak"}
ACCENT_RE = re.compile(
    r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩ"
    r"òóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]",
    re.IGNORECASE,
)
COMMUNITY_HINTS = ("discuss.", "forum.", "forums.", "community.", "news.ycombinator.com", "lobste.rs", "stackoverflow.com")
SUPPORT_NOISE_HINTS = ("coredump", "crc fault", "camera init fail", "driver install", "installation issue", "not usable")
MAX_TEXT = 320
STRONG_GDELT_RE = re.compile(
    r"\b(model|llm|large language model|generative ai|genai|agent|mcp|gpu|semiconductor|robotics|automation|ai startup|openai|anthropic|nvidia|deepmind|mistral|hugging face|qwen|deepseek|llama)\b",
    re.IGNORECASE,
)
THEME_DUMP_RE = re.compile(r"\b(TAX_|WB_|EPU_|CRISISLEX_|SOC_|ENV_|MEDIA_|UNGP_|USPEC_)[A-Z0-9_]+,\d+", re.IGNORECASE)
STRONG_TOPIC_TAGS = {
    "model_agent_moi",
    "chip_ha_tang",
    "cybersecurity",
    "robotics",
    "open_source_developer_tools",
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _host(url: str) -> str:
    host = (urlparse(str(url or "")).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def _parse_dt(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _has_accents(text: str) -> bool:
    return bool(ACCENT_RE.search(str(text or "")))


def _check_vietnamese(errs: list[str], text: str, field_name: str) -> None:
    if not str(text or "").strip():
        errs.append(f"{field_name} must not be empty")
        return
    if not _has_accents(text):
        errs.append(f"{field_name} must contain Vietnamese diacritics")


def _check_public_text(errs: list[str], text: str, field_name: str) -> None:
    lowered = str(text or "").lower()
    for term in FORBIDDEN_TERMS:
        if term in lowered:
            errs.append(f"{field_name} contains forbidden term: {term}")
            break
    if len(str(text or "")) > MAX_TEXT:
        errs.append(f"{field_name} too long")
    _check_vietnamese(errs, text, field_name)


def _check_url(errs: list[str], url: str, field_name: str) -> None:
    if not str(url or "").startswith("http"):
        errs.append(f"{field_name} must be a real URL")


def _load_live_url_pool() -> set[str]:
    urls: set[str] = set()
    if TECH_NEWS_FOR_AI_CLEAN.is_file():
        payload = _load_json(TECH_NEWS_FOR_AI_CLEAN)
        for article in payload.get("articles") or []:
            url = str(article.get("url") or "").strip()
            if url.startswith("http"):
                urls.add(url)
    if TECH_GDELT_OUTPUT.is_file():
        payload = _load_json(TECH_GDELT_OUTPUT)
        for event in payload.get("events") or []:
            primary = str(event.get("primary_url") or "").strip()
            if primary.startswith("http"):
                urls.add(primary)
            for url in event.get("source_urls") or []:
                if str(url).startswith("http"):
                    urls.add(str(url))
    if TECH_ROLLING_CANDIDATES.is_file():
        payload = _load_json(TECH_ROLLING_CANDIDATES)
        for candidate in payload.get("candidates") or []:
            url = str(candidate.get("url") or "").strip()
            if url.startswith("http"):
                urls.add(url)
    if TECH_API_CANDIDATES.is_file():
        payload = _load_json(TECH_API_CANDIDATES)
        for candidate in payload.get("candidates") or []:
            url = str(candidate.get("url") or "").strip()
            if url.startswith("http"):
                urls.add(url)
    if TECH_WATCHLIST_STATUS.is_file():
        payload = _load_json(TECH_WATCHLIST_STATUS)
        for entity in payload.get("entities") or []:
            for link in entity.get("top_links") or []:
                url = str(link.get("url") or "").strip()
                if url.startswith("http"):
                    urls.add(url)
    return urls


def validate(payload: dict, *, check_external: bool = True) -> list[str]:
    errs: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        errs.append(f"schema_version must be {SCHEMA_VERSION}")
    if int(payload.get("window_hours") or 0) != WINDOW_HOURS:
        errs.append("window_hours must equal 72")

    executive_summary = payload.get("executive_summary")
    if not isinstance(executive_summary, list) or not executive_summary:
        errs.append("executive_summary must be a non-empty list")
    else:
        for idx, line in enumerate(executive_summary):
            _check_public_text(errs, str(line), f"executive_summary[{idx}]")
            lowered_line = str(line).lower()
            if "giữ lại 0 bài đáng đọc" in lowered_line:
                errs.append("executive_summary must not say 0 bài đáng đọc")

    must_read = payload.get("must_read")
    if not isinstance(must_read, list):
        errs.append("must_read must be a list")
    stats = payload.get("stats") or {}
    curator_candidate_count = int(stats.get("curator_candidate_count") or 0)
    main_candidate_count = int(stats.get("main_candidate_count") or 0)
    must_read_count = len(must_read or [])
    if curator_candidate_count >= 5 and must_read_count == 0:
        errs.append("must_read must not be empty when curator_candidate_count >= 5")
    if main_candidate_count >= 10 and must_read_count < 5:
        errs.append("must_read must contain at least 5 items when main_candidate_count >= 10")
    watchlist_entity_count = int(stats.get("watchlist_entity_count") or 0)
    if watchlist_entity_count and watchlist_entity_count < 10:
        errs.append("frontier watchlist must contain at least 10 entities")
    fallback_watchlist = Path(__file__).resolve().parents[1] / "tech" / "config" / "frontier_watchlist.json"
    if not TECH_FRONTIER_WATCHLIST.is_file() and not fallback_watchlist.is_file():
        errs.append("frontier_watchlist.json missing")
    if not TECH_WATCHLIST_STATUS.is_file() and not payload.get("watchlist_status"):
        errs.append("watchlist_status.json missing")
    if int(stats.get("watchlist_checked") or 0) < max(1, watchlist_entity_count):
        errs.append("critical watchlist entities were not all checked")
    # A 72h window may legitimately have no publishable event in a configured
    # lane. Coverage is reported in stats, but validators must not force-fill
    # model/image-video sections with metadata-only watchlist entries.
    for lane_field in ("model_hub_candidate_count", "image_video_workflow_candidate_count"):
        if lane_field in stats and int(stats.get(lane_field) or 0) < 0:
            errs.append(f"{lane_field} must not be negative")
    if "active_url_sources" in stats and "active_watchlist_entities" in stats:
        if int(stats.get("active_url_sources") or 0) == int(stats.get("active_watchlist_entities") or 0) and int(stats.get("active_watchlist_entities") or 0) >= 10:
            errs.append("coverage stats appear to mix watchlist entities with active URL sources")
    if int(stats.get("top_signal_cluster_count") or 0) <= 0:
        errs.append("top_signal_clusters must not be empty")
    if stats.get("gdelt_reused_previous_events") and int(stats.get("gdelt_fresh_event_count") or 0) != 0:
        errs.append("GDELT reused previous events but publication labels them fresh")
    if check_external:
        if not TECH_SOURCE_REGISTRY.is_file():
            errs.append("source_registry.json missing")
        else:
            registry = _load_json(TECH_SOURCE_REGISTRY)
            reg_summary = registry.get("summary") or {}
            reg_dt = _parse_dt(registry.get("generated_at_utc"))
            if reg_dt is None:
                errs.append("source_registry generated_at_utc missing or invalid")
            elif (datetime.now(timezone.utc) - reg_dt).total_seconds() > 30 * 3600:
                errs.append("source_registry is older than 30h")
            p0_configured = int(reg_summary.get("p0_configured") or 0)
            p0_checked = int(reg_summary.get("p0_checked") or 0)
            p0_success = int(reg_summary.get("p0_success") or 0)
            p0_failed = int(reg_summary.get("p0_failed") or 0)
            if p0_configured <= 0:
                errs.append("source_registry has no configured P0 sources")
            if p0_checked < p0_configured:
                errs.append("P0 sources were not all checked")
            if p0_configured > 0 and p0_success <= 0 and p0_failed >= p0_configured:
                errs.append("all P0 source methods failed")
            missing_critical = reg_summary.get("missing_critical_entities") or []
            if missing_critical:
                errs.append(f"missing critical entity in source registry: {', '.join(map(str, missing_critical[:12]))}")

    top_clusters = payload.get("top_signal_clusters")
    if not isinstance(top_clusters, list) or not top_clusters:
        errs.append("top_signal_clusters must be a non-empty list")
    else:
        entity_counter: Counter[str] = Counter()
        leon_mentions = 0
        for idx, cluster in enumerate(top_clusters):
            if not str(cluster.get("cluster_id") or "").strip():
                errs.append(f"top_signal_clusters[{idx}].cluster_id missing")
            if not str(cluster.get("cluster_title") or "").strip():
                errs.append(f"top_signal_clusters[{idx}].cluster_title missing")
            for field in ("takeaway", "what_changed", "why_it_matters"):
                _check_public_text(errs, str(cluster.get(field) or ""), f"top_signal_clusters[{idx}].{field}")
            if not isinstance(cluster.get("affected_ecosystem"), list) or not cluster.get("affected_ecosystem"):
                errs.append(f"top_signal_clusters[{idx}].affected_ecosystem missing")
            if not isinstance(cluster.get("links"), list) or not cluster.get("links"):
                errs.append(f"top_signal_clusters[{idx}].links missing")
            event_evidence_count = 0
            for link_idx, link in enumerate(cluster.get("links") or []):
                if str(link.get("raw_source_method") or "") == "manual_signal":
                    errs.append(f"top_signal_clusters[{idx}].links[{link_idx}] manual_signal is not allowed")
                if str(link.get("evidence") or "") == "watchlist_configured_source":
                    errs.append(f"top_signal_clusters[{idx}].links[{link_idx}] watchlist_configured_source is not allowed")
                if str(link.get("content_quality") or "metadata_only") != "metadata_only":
                    event_evidence_count += 1
                strength = str(link.get("match_strength") or "medium")
                if strength not in ALLOWED_MATCH_STRENGTH:
                    errs.append(f"top_signal_clusters[{idx}].links[{link_idx}].match_strength invalid")
            if cluster.get("links") and event_evidence_count == 0:
                errs.append(f"top_signal_clusters[{idx}] must contain at least 1 non-metadata event source")
            for entity in cluster.get("entities") or []:
                entity_counter[str(entity)] += 1
            leon_mentions += str(cluster).lower().count("leon")
        duplicated = [entity for entity, count in entity_counter.items() if entity and count >= 3]
        if duplicated:
            errs.append(f"same entity appears in 3+ top signal clusters: {', '.join(sorted(duplicated))}")
        if leon_mentions > max(2, len(top_clusters)):
            errs.append("top_signal_clusters are too personalized around Leon")

    sections = payload.get("sections")
    if not isinstance(sections, dict):
        return errs + ["sections must be an object"]
    missing = sorted(REQUIRED_SECTION_KEYS - set(sections.keys()))
    if missing:
        errs.append(f"missing sections: {', '.join(missing)}")

    if not isinstance(sections.get("full_link_radar"), list) or not (sections.get("full_link_radar") or []):
        errs.append("full_link_radar must not be empty")

    knowledge = sections.get("ai_knowledge")
    if not isinstance(knowledge, list) or not knowledge:
        errs.append("ai_knowledge must be present")
    else:
        for idx, item in enumerate(knowledge):
            for field in ("concept", "explain_simple", "why_now", "how_to_apply", "best_links"):
                if field not in item:
                    errs.append(f"sections.ai_knowledge[{idx}] missing {field}")
            _check_public_text(errs, str(item.get("concept") or ""), f"sections.ai_knowledge[{idx}].concept")
            _check_public_text(errs, str(item.get("explain_simple") or ""), f"sections.ai_knowledge[{idx}].explain_simple")
            _check_public_text(errs, str(item.get("why_now") or ""), f"sections.ai_knowledge[{idx}].why_now")
            _check_public_text(errs, str(item.get("how_to_apply") or ""), f"sections.ai_knowledge[{idx}].how_to_apply")
            links = item.get("best_links")
            if not isinstance(links, list) or not links:
                errs.append(f"sections.ai_knowledge[{idx}].best_links must be a non-empty list")
            else:
                for link_idx, url in enumerate(links):
                    _check_url(errs, str(url), f"sections.ai_knowledge[{idx}].best_links[{link_idx}]")

    founder = sections.get("founder_ideas_for_leon")
    if not isinstance(founder, list) or not founder:
        errs.append("founder_ideas_for_leon must be present")
    else:
        for idx, item in enumerate(founder):
            for field in ("idea", "based_on", "why_now", "apply_now"):
                if field not in item:
                    errs.append(f"sections.founder_ideas_for_leon[{idx}] missing {field}")
            _check_public_text(errs, str(item.get("idea") or ""), f"sections.founder_ideas_for_leon[{idx}].idea")
            _check_public_text(errs, str(item.get("why_now") or ""), f"sections.founder_ideas_for_leon[{idx}].why_now")
            _check_public_text(errs, str(item.get("apply_now") or ""), f"sections.founder_ideas_for_leon[{idx}].apply_now")

    live_urls = _load_live_url_pool() if check_external else set()
    must_read_community = 0
    domain_counts: Counter[str] = Counter()
    why_prefix_counts: Counter[str] = Counter()
    now = datetime.now(timezone.utc)

    for idx, item in enumerate(must_read or []):
        _check_url(errs, item.get("url"), f"must_read[{idx}].url")
        category = str(item.get("category") or "").strip()
        if category not in ALLOWED_CATEGORIES:
            errs.append(f"must_read[{idx}].category invalid")
        source_type = str(item.get("source_type") or "").strip()
        host = _host(str(item.get("url") or ""))
        domain_counts[host] += 1
        if source_type == "community":
            must_read_community += 1
        if any(part in host for part in COMMUNITY_HINTS) and source_type == "official":
            errs.append(f"must_read[{idx}] forum/community source cannot be official")
        importance = int(item.get("importance") or 0)
        if not 1 <= importance <= 5:
            errs.append(f"must_read[{idx}].importance must be 1-5")
        if importance <= 1 and str(item.get("evidence") or "") != "exploratory":
            errs.append(f"must_read[{idx}].importance=1 requires evidence=exploratory")
        if any(hint in str(item.get("title") or "").lower() for hint in SUPPORT_NOISE_HINTS) and importance >= 4:
            errs.append(f"must_read[{idx}] support noise cannot have importance >= 4")
        for field in ("curation_status", "signal_type", "confidence", "evidence", "time_to_apply", "leon_fit"):
            if not str(item.get(field) or "").strip():
                errs.append(f"must_read[{idx}].{field} must be present")
        if item.get("curation_status") not in {"ai", "fallback"}:
            errs.append(f"must_read[{idx}].curation_status invalid")
        if str(item.get("source_lane") or "normal_web") not in ALLOWED_SOURCE_LANES:
            errs.append(f"must_read[{idx}].source_lane invalid")
        if str(item.get("raw_source_method") or "") == "manual_signal":
            errs.append(f"must_read[{idx}] manual_signal is not allowed")
        if str(item.get("content_quality") or "metadata_only") == "metadata_only":
            errs.append(f"must_read[{idx}] metadata_only is not publishable event evidence")
        if str(item.get("evidence") or "") == "watchlist_configured_source":
            errs.append(f"must_read[{idx}] watchlist_configured_source is not allowed")
        if str(item.get("match_strength") or "medium") not in ALLOWED_MATCH_STRENGTH:
            errs.append(f"must_read[{idx}].match_strength invalid")
        for bool_field in ("official_entity_source", "is_personal_finetune", "is_test_repo"):
            if bool_field in item and not isinstance(item.get(bool_field), bool):
                errs.append(f"must_read[{idx}].{bool_field} must be boolean")
        if source_type == "community" and str(item.get("evidence") or "") != "community-only":
            errs.append(f"must_read[{idx}] community item must use evidence=community-only")
        _check_public_text(errs, str(item.get("why_read") or ""), f"must_read[{idx}].why_read")
        _check_public_text(errs, str(item.get("apply_now") or ""), f"must_read[{idx}].apply_now")
        _check_public_text(errs, str(item.get("leon_fit") or ""), f"must_read[{idx}].leon_fit")
        why_prefix = " ".join(str(item.get("why_read") or "").split()[:6]).lower()
        why_prefix_counts[why_prefix] += 1
        published_at = item.get("published_at")
        dt = _parse_dt(published_at)
        if dt is None:
            errs.append(f"must_read[{idx}] must have verified published_at within 72h")
        elif (now - dt).total_seconds() > WINDOW_HOURS * 3600:
            errs.append(f"must_read[{idx}] is older than 72h")
        if live_urls and str(item.get("url") or "") not in live_urls:
            errs.append(f"must_read[{idx}] URL is not present in live crawl/GDELT inputs")

    main_by_source_type = stats.get("main_by_source_type") or {}
    non_community_main = int(main_by_source_type.get("official") or 0) + int(main_by_source_type.get("independent") or 0)
    community_share = must_read_community / max(1, len(must_read or []))
    if must_read and non_community_main > 0 and community_share > 0.50:
        errs.append("must_read community share must be <= 50% when non-community candidates exist")
    if must_read and non_community_main > 0 and community_share > 0.50 and not stats.get("must_read_quality_warning"):
        errs.append("stats.must_read_quality_warning must explain community share over 50%")
    if must_read and non_community_main == 0 and must_read_community > 5:
        errs.append("must_read community fallback must be <= 5 when non-community is absent")
    over_domain = [domain for domain, count in domain_counts.items() if domain and count > 3]
    if over_domain:
        errs.append(f"a single domain exceeds 3 must_read items: {', '.join(sorted(over_domain))}")
    if not top_clusters and any(count >= 12 for count in why_prefix_counts.values() if count):
        errs.append("at least 5 must_read items share the same why_read structure")

    main_section_names = [
        "ai_models",
        "local_ai_china_ai",
        "ai_tools",
        "automation_mcp_agents",
        "open_source_hot",
        "ai_business_money",
        "industry_impact",
    ]
    for sec_name in main_section_names:
        items = sections.get(sec_name) or []
        if not isinstance(items, list):
            errs.append(f"sections.{sec_name} must be list")
            continue
        for idx, item in enumerate(items):
            _check_url(errs, item.get("url"), f"sections.{sec_name}[{idx}].url")
            category = str(item.get("category") or "").strip()
            if category not in ALLOWED_CATEGORIES:
                errs.append(f"sections.{sec_name}[{idx}].category invalid")
            source_type = str(item.get("source_type") or "").strip()
            if str(item.get("source_lane") or "normal_web") not in ALLOWED_SOURCE_LANES:
                errs.append(f"sections.{sec_name}[{idx}].source_lane invalid")
            if str(item.get("raw_source_method") or "") == "manual_signal":
                errs.append(f"sections.{sec_name}[{idx}] manual_signal is not allowed")
            if str(item.get("content_quality") or "metadata_only") == "metadata_only":
                errs.append(f"sections.{sec_name}[{idx}] metadata_only is not publishable event evidence")
            if str(item.get("evidence") or "") == "watchlist_configured_source":
                errs.append(f"sections.{sec_name}[{idx}] watchlist_configured_source is not allowed")
            if str(item.get("match_strength") or "medium") not in ALLOWED_MATCH_STRENGTH:
                errs.append(f"sections.{sec_name}[{idx}].match_strength invalid")
            host = _host(str(item.get("url") or ""))
            if any(part in host for part in COMMUNITY_HINTS) and source_type == "official":
                errs.append(f"sections.{sec_name}[{idx}] forum/community source cannot be official")
            importance = int(item.get("importance") or 0)
            if not 1 <= importance <= 5:
                errs.append(f"sections.{sec_name}[{idx}].importance must be 1-5")
            if importance <= 1 and str(item.get("evidence") or "") != "exploratory":
                errs.append(f"sections.{sec_name}[{idx}].importance=1 requires evidence=exploratory")
            _check_public_text(errs, str(item.get("why_read") or ""), f"sections.{sec_name}[{idx}].why_read")
            _check_public_text(errs, str(item.get("apply_now") or ""), f"sections.{sec_name}[{idx}].apply_now")
            _check_public_text(errs, str(item.get("why_interesting") or ""), f"sections.{sec_name}[{idx}].why_interesting")
            dt = _parse_dt(item.get("published_at"))
            if dt is None or (now - dt).total_seconds() > WINDOW_HOURS * 3600:
                errs.append(f"sections.{sec_name}[{idx}] must stay within 72h")
            if item.get("time_verified") is not True:
                errs.append(f"sections.{sec_name}[{idx}] must have time_verified=true")
            if live_urls and str(item.get("url") or "") not in live_urls:
                errs.append(f"sections.{sec_name}[{idx}] URL is not present in live crawl/GDELT inputs")
            if any(hint in str(item.get("title") or "").lower() for hint in SUPPORT_NOISE_HINTS) and importance >= 4:
                errs.append(f"sections.{sec_name}[{idx}] support noise cannot have importance >= 4")
            for field in ("curation_status", "signal_type", "confidence", "evidence", "time_to_apply", "leon_fit"):
                if not str(item.get(field) or "").strip():
                    errs.append(f"sections.{sec_name}[{idx}].{field} must be present")

    full_radar = sections.get("full_link_radar") or []
    if isinstance(full_radar, list):
        manual_full_radar = 0
        for idx, item in enumerate(full_radar):
            _check_url(errs, item.get("url"), f"sections.full_link_radar[{idx}].url")
            category = str(item.get("category") or "").strip()
            if category not in ALLOWED_CATEGORIES:
                errs.append(f"sections.full_link_radar[{idx}].category invalid")
            if str(item.get("source_lane") or "") not in ALLOWED_SOURCE_LANES:
                errs.append(f"sections.full_link_radar[{idx}].source_lane invalid")
            quality = str(item.get("content_quality") or "metadata_only")
            if quality not in ALLOWED_CONTENT_QUALITY:
                errs.append(f"sections.full_link_radar[{idx}].content_quality invalid")
            method = str(item.get("raw_source_method") or "")
            if method and method not in ALLOWED_RAW_SOURCE_METHODS:
                errs.append(f"sections.full_link_radar[{idx}].raw_source_method invalid")
            if method == "manual_signal":
                manual_full_radar += 1
            if str(item.get("match_strength") or "medium") not in ALLOWED_MATCH_STRENGTH:
                errs.append(f"sections.full_link_radar[{idx}].match_strength invalid")
            for bool_field in ("official_entity_source", "is_personal_finetune", "is_test_repo"):
                if bool_field in item and not isinstance(item.get(bool_field), bool):
                    errs.append(f"sections.full_link_radar[{idx}].{bool_field} must be boolean")
            if not str(item.get("one_line_reason") or "").strip():
                errs.append(f"sections.full_link_radar[{idx}].one_line_reason missing")
            _check_public_text(errs, str(item.get("why_interesting") or ""), f"sections.full_link_radar[{idx}].why_interesting")
            _check_public_text(errs, str(item.get("use_case") or ""), f"sections.full_link_radar[{idx}].use_case")
            if str(item.get("source_type") or "") == "official" and any(part in _host(str(item.get("url") or "")) for part in COMMUNITY_HINTS):
                errs.append(f"sections.full_link_radar[{idx}] forum/community source cannot be official")
            if live_urls and str(item.get("url") or "") not in live_urls:
                errs.append(f"sections.full_link_radar[{idx}] URL is not present in live crawl/GDELT inputs")
        if int(stats.get("candidate_count") or 0) >= 30 and len(full_radar) < 30:
            errs.append("Full Link Radar below 30 links when enough candidates exist")
        if full_radar and manual_full_radar / max(1, len(full_radar)) > 0.10:
            errs.append("manual_signal share in Full Link Radar must be <= 10%")
    if int(stats.get("manual_signal_count") or 0) > 0 and float(stats.get("manual_signal_share") or 0) > 0.10:
        errs.append("manual_signal share in candidate pool must be <= 10%")

    render_checks = stats.get("render_checks") or {}
    if render_checks.get("knowledge_fields_ready") is not True:
        errs.append("render_checks.knowledge_fields_ready must be true")
    if render_checks.get("founder_fields_ready") is not True:
        errs.append("render_checks.founder_fields_ready must be true")

    if check_external and TECH_GDELT_OUTPUT.is_file():
        gdelt = _load_json(TECH_GDELT_OUTPUT)
        for field in ("raw_event_count", "ai_filtered_event_count", "rejected_non_ai_count", "bytes_status"):
            if field not in gdelt:
                errs.append(f"gdelt_pulse missing {field}")
        for idx, event in enumerate(gdelt.get("events") or []):
            blob = " ".join(
                str(part or "")
                for part in [
                    event.get("title"),
                    event.get("summary"),
                    event.get("primary_url"),
                    " ".join(event.get("source_urls") or []),
                    " ".join(event.get("topic_tags") or []),
                    " ".join(event.get("company_tags") or []),
                    " ".join(event.get("signal_keywords") or []),
                ]
            )
            if THEME_DUMP_RE.search(str(event.get("summary") or "")):
                errs.append(f"gdelt.events[{idx}].summary contains theme dump")
            has_metadata_signal = bool(event.get("signal_keywords")) or bool(event.get("company_tags")) or bool(STRONG_TOPIC_TAGS & set(event.get("topic_tags") or []))
            if not has_metadata_signal and not STRONG_GDELT_RE.search(blob):
                errs.append(f"gdelt.events[{idx}] lacks strong AI/tech signal")
            if not event.get("source_urls"):
                errs.append(f"gdelt.events[{idx}] missing source_urls")

    return errs


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AI Frontier Radar 72h JSON")
    parser.add_argument("--input", type=Path, default=TECH_PUBLICATION_OUTPUT)
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"Missing file: {args.input}", file=sys.stderr)
        return 1
    payload = _load_json(args.input)
    errs = validate(payload)
    if errs:
        for err in errs:
            print(err, file=sys.stderr)
        return 1
    print("OK: AI Frontier Radar 72h valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
