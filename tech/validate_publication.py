#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tech.common import (
    FORBIDDEN_PUBLIC_TERMS, GDELT_JSON, NEWS_CLEAN, PUBLICATION_JSON,
    PUBLICATION_SCHEMA, WINDOW_HOURS, canonical_url, hot_rule, load_json,
)

REQUIRED_SECTIONS = {
    "tong_quan", "tin_nong", "model_agent_moi", "cach_dung_ai",
    "open_source_developer_tools", "chip_ha_tang", "robotics", "cybersecurity",
    "chinh_sach_cuoc_dua_toan_cau", "radar_khu_vuc", "watchlist_24_72h",
}


def allowed_urls(crawl: dict, events: dict) -> set[str]:
    urls = {
        canonical_url(str(x.get("url") or ""))
        for x in crawl.get("articles") or []
    }
    for event in events.get("events") or []:
        urls.update(canonical_url(str(url)) for url in event.get("source_urls") or [])
    return {url for url in urls if url}


def validate(publication: dict, crawl: dict, events: dict) -> list[str]:
    errors: list[str] = []
    if publication.get("schema_version") != PUBLICATION_SCHEMA:
        errors.append(f"schema_version must be {PUBLICATION_SCHEMA}")
    if int(publication.get("window_hours") or 0) != WINDOW_HOURS:
        errors.append("window_hours must be 72")
    sections = publication.get("sections")
    if not isinstance(sections, dict):
        return errors + ["sections must be an object"]
    missing = REQUIRED_SECTIONS - set(sections)
    if missing:
        errors.append("missing sections: " + ", ".join(sorted(missing)))
    grounded = allowed_urls(crawl, events)
    seen_ids: set[str] = set()
    for section, items in sections.items():
        if not isinstance(items, list):
            errors.append(f"sections.{section} must be a list")
            continue
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"sections.{section}[{index}] must be an object")
                continue
            story_id = str(item.get("id") or "")
            if section != "watchlist_24_72h" and story_id:
                if story_id in seen_ids:
                    errors.append(f"duplicate story id: {story_id}")
                seen_ids.add(story_id)
            public_text = " ".join(str(item.get(key) or "") for key in ("headline", "summary", "why_it_matters", "practical_use")).lower()
            for term in FORBIDDEN_PUBLIC_TERMS:
                if term.lower() in public_text:
                    errors.append(f"sections.{section}[{index}] exposes internal term: {term}")
            if section == "tong_quan":
                continue
            links = item.get("links") or []
            if not links:
                errors.append(f"sections.{section}[{index}] has no source links")
                continue
            domains: set[str] = set()
            types: list[str] = []
            for link in links:
                url = canonical_url(str(link.get("url") or ""))
                domain = str(link.get("domain") or "")
                if not url or url not in grounded:
                    errors.append(f"sections.{section}[{index}] has ungrounded URL")
                if domain in domains:
                    errors.append(f"sections.{section}[{index}] repeats domain {domain}")
                domains.add(domain)
                types.append(str(link.get("source_type") or ""))
            is_hot, independent_count, official_present, community_count = hot_rule(types)
            label = str(item.get("confirmation_label") or "")
            if label == "hot" and not is_hot:
                errors.append(f"sections.{section}[{index}] violates hot rule")
            if int(item.get("independent_domain_count") or 0) != independent_count:
                errors.append(f"sections.{section}[{index}] independent count mismatch")
            if bool(item.get("official_source_present")) != official_present:
                errors.append(f"sections.{section}[{index}] official flag mismatch")
            if int(item.get("community_domain_count") or 0) != community_count:
                errors.append(f"sections.{section}[{index}] community count mismatch")
            if int(item.get("freshness_hours") or WINDOW_HOURS) > WINDOW_HOURS:
                errors.append(f"sections.{section}[{index}] is older than 72 hours")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=PUBLICATION_JSON)
    parser.add_argument("--crawl-input", type=Path, default=NEWS_CLEAN)
    parser.add_argument("--event-input", type=Path, default=GDELT_JSON)
    args = parser.parse_args()
    publication = load_json(args.input, {})
    errors = validate(publication, load_json(args.crawl_input, {}), load_json(args.event_input, {}))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("OK: 72-hour technology publication is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
