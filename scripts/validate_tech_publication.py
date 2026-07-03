#!/usr/bin/env python3
"""Validate AI Frontier Radar 72h publication."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

from scripts.tech_common import TECH_PUBLICATION_OUTPUT

SCHEMA_VERSION = "ai-frontier-radar-72h-v1"
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
MAX_SHORT_TEXT = 320


def _host(url: str) -> str:
    host = (urlparse(str(url or "")).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def _check_public_text(errs: list[str], text: str, field_name: str) -> None:
    lowered = str(text or "").lower()
    for term in FORBIDDEN_TERMS:
        if term in lowered:
            errs.append(f"{field_name} contains forbidden term: {term}")
            break


def _check_url(errs: list[str], url: str, field_name: str) -> None:
    if not str(url or "").startswith("http"):
        errs.append(f"{field_name} must be a real URL")


def validate(payload: dict) -> list[str]:
    errs: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        errs.append(f"schema_version must be {SCHEMA_VERSION}")
    if int(payload.get("window_hours") or 0) != 72:
        errs.append("window_hours must equal 72")

    executive_summary = payload.get("executive_summary")
    if not isinstance(executive_summary, list) or not executive_summary:
        errs.append("executive_summary must be a non-empty list")
    else:
        for idx, line in enumerate(executive_summary):
            _check_public_text(errs, str(line), f"executive_summary[{idx}]")

    must_read = payload.get("must_read")
    if not isinstance(must_read, list) or len(must_read) < 10:
        errs.append("must_read must have at least 10 items")

    sections = payload.get("sections")
    if not isinstance(sections, dict):
        return errs + ["sections must be an object"]
    missing = sorted(REQUIRED_SECTION_KEYS - set(sections.keys()))
    if missing:
        errs.append(f"missing sections: {', '.join(missing)}")

    full_link_radar = sections.get("full_link_radar")
    if not isinstance(full_link_radar, list) or len(full_link_radar) < 30:
        errs.append("full_link_radar must have at least 30 items")

    if not isinstance(sections.get("ai_knowledge"), list) or not sections.get("ai_knowledge"):
        errs.append("ai_knowledge must be present")
    if not isinstance(sections.get("founder_ideas_for_leon"), list) or not sections.get("founder_ideas_for_leon"):
        errs.append("founder_ideas_for_leon must be present")

    seen_urls: dict[str, int] = {}
    for idx, item in enumerate(must_read or []):
        if not isinstance(item, dict):
            errs.append(f"must_read[{idx}] must be object")
            continue
        _check_url(errs, item.get("url"), f"must_read[{idx}].url")
        category = str(item.get("category") or "").strip()
        if category not in ALLOWED_CATEGORIES:
            errs.append(f"must_read[{idx}].category invalid")
        if int(item.get("source_count") or 0) <= 0:
            errs.append(f"must_read[{idx}].source_count must be > 0")
        for field in ("title", "why_read", "apply_now"):
            text = str(item.get(field) or "")
            if field != "title" and len(text) > MAX_SHORT_TEXT:
                errs.append(f"must_read[{idx}].{field} too long")
            _check_public_text(errs, text, f"must_read[{idx}].{field}")
        url = str(item.get("url") or "")
        seen_urls[url] = seen_urls.get(url, 0) + 1

    for sec_name, items in sections.items():
        if not isinstance(items, list):
            errs.append(f"sections.{sec_name} must be list")
            continue
        if sec_name == "ai_knowledge":
            for idx, item in enumerate(items):
                if int(item.get("source_count") or 0) <= 0:
                    errs.append(f"sections.ai_knowledge[{idx}].source_count must be > 0")
                for field in ("concept", "explain_simple", "why_now", "how_to_apply"):
                    _check_public_text(errs, str(item.get(field) or ""), f"sections.ai_knowledge[{idx}].{field}")
            continue
        if sec_name == "founder_ideas_for_leon":
            for idx, item in enumerate(items):
                if int(item.get("source_count") or 0) <= 0:
                    errs.append(f"sections.founder_ideas_for_leon[{idx}].source_count must be > 0")
                for field in ("idea", "apply_now", "why_now"):
                    _check_public_text(errs, str(item.get(field) or ""), f"sections.founder_ideas_for_leon[{idx}].{field}")
            continue
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                errs.append(f"sections.{sec_name}[{idx}] must be object")
                continue
            if sec_name == "full_link_radar":
                _check_url(errs, item.get("url"), f"sections.{sec_name}[{idx}].url")
                category = str(item.get("category") or "").strip()
                if category not in ALLOWED_CATEGORIES:
                    errs.append(f"sections.{sec_name}[{idx}].category invalid")
                if int(item.get("source_count") or 0) <= 0:
                    errs.append(f"sections.{sec_name}[{idx}].source_count must be > 0")
                for field in ("title", "why_interesting", "use_case"):
                    text = str(item.get(field) or "")
                    if field != "title" and len(text) > MAX_SHORT_TEXT:
                        errs.append(f"sections.{sec_name}[{idx}].{field} too long")
                    _check_public_text(errs, text, f"sections.{sec_name}[{idx}].{field}")
                url = str(item.get("url") or "")
                seen_urls[url] = seen_urls.get(url, 0) + 1
            else:
                for field in ("title", "why_read", "apply_now", "why_interesting"):
                    text = str(item.get(field) or "")
                    if field != "title" and len(text) > MAX_SHORT_TEXT:
                        errs.append(f"sections.{sec_name}[{idx}].{field} too long")
                    _check_public_text(errs, text, f"sections.{sec_name}[{idx}].{field}")
                _check_url(errs, item.get("url"), f"sections.{sec_name}[{idx}].url")
                if int(item.get("source_count") or 0) <= 0:
                    errs.append(f"sections.{sec_name}[{idx}].source_count must be > 0")

    duplicate_urls = [url for url, count in seen_urls.items() if url and count > 3]
    if duplicate_urls:
        errs.append(f"too many duplicate URLs: {len(duplicate_urls)}")

    return errs


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AI Frontier Radar 72h JSON")
    parser.add_argument("--input", type=Path, default=TECH_PUBLICATION_OUTPUT)
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"Missing file: {args.input}", file=sys.stderr)
        return 1
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    errs = validate(payload)
    if errs:
        for err in errs:
            print(err, file=sys.stderr)
        return 1
    print("OK: AI Frontier Radar 72h valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
