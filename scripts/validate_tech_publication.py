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

from scripts.tech_common import TECH_GDELT_OUTPUT, TECH_NEWS_FOR_AI_CLEAN, TECH_PUBLICATION_OUTPUT

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
ACCENT_RE = re.compile(
    r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩ"
    r"òóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]",
    re.IGNORECASE,
)
COMMUNITY_HINTS = ("discuss.", "forum.", "forums.", "community.", "news.ycombinator.com", "lobste.rs", "stackoverflow.com")
SUPPORT_NOISE_HINTS = ("coredump", "crc fault", "camera init fail", "driver install", "installation issue", "not usable")
MAX_TEXT = 320


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
    return urls


def validate(payload: dict) -> list[str]:
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

    must_read = payload.get("must_read")
    if not isinstance(must_read, list):
        errs.append("must_read must be a list")

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

    live_urls = _load_live_url_pool()
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
        if any(hint in str(item.get("title") or "").lower() for hint in SUPPORT_NOISE_HINTS) and importance >= 4:
            errs.append(f"must_read[{idx}] support noise cannot have importance >= 4")
        _check_public_text(errs, str(item.get("why_read") or ""), f"must_read[{idx}].why_read")
        _check_public_text(errs, str(item.get("apply_now") or ""), f"must_read[{idx}].apply_now")
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

    if must_read and must_read_community / max(1, len(must_read)) > 0.30:
        errs.append("must_read community share must be <= 30%")
    over_domain = [domain for domain, count in domain_counts.items() if domain and count > 3]
    if over_domain:
        errs.append(f"a single domain exceeds 3 must_read items: {', '.join(sorted(over_domain))}")
    if any(count >= 5 for count in why_prefix_counts.values() if count):
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
            host = _host(str(item.get("url") or ""))
            if any(part in host for part in COMMUNITY_HINTS) and source_type == "official":
                errs.append(f"sections.{sec_name}[{idx}] forum/community source cannot be official")
            importance = int(item.get("importance") or 0)
            if not 1 <= importance <= 5:
                errs.append(f"sections.{sec_name}[{idx}].importance must be 1-5")
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

    full_radar = sections.get("full_link_radar") or []
    if isinstance(full_radar, list):
        for idx, item in enumerate(full_radar):
            _check_url(errs, item.get("url"), f"sections.full_link_radar[{idx}].url")
            category = str(item.get("category") or "").strip()
            if category not in ALLOWED_CATEGORIES:
                errs.append(f"sections.full_link_radar[{idx}].category invalid")
            _check_public_text(errs, str(item.get("why_interesting") or ""), f"sections.full_link_radar[{idx}].why_interesting")
            _check_public_text(errs, str(item.get("use_case") or ""), f"sections.full_link_radar[{idx}].use_case")
            if str(item.get("source_type") or "") == "official" and any(part in _host(str(item.get("url") or "")) for part in COMMUNITY_HINTS):
                errs.append(f"sections.full_link_radar[{idx}] forum/community source cannot be official")
            if live_urls and str(item.get("url") or "") not in live_urls:
                errs.append(f"sections.full_link_radar[{idx}] URL is not present in live crawl/GDELT inputs")

    stats = payload.get("stats") or {}
    render_checks = stats.get("render_checks") or {}
    if render_checks.get("knowledge_fields_ready") is not True:
        errs.append("render_checks.knowledge_fields_ready must be true")
    if render_checks.get("founder_fields_ready") is not True:
        errs.append("render_checks.founder_fields_ready must be true")

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
