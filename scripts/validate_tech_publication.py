#!/usr/bin/env python3
"""Validate the standalone tech publication artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from scripts.tech_common import TECH_PUBLICATION_OUTPUT, TECH_PUBLICATION_SCHEMA

REQUIRED_SECTIONS = {
    "tong_quan",
    "tin_nong",
    "model_agent_moi",
    "cach_dung_ai",
    "open_source_developer_tools",
    "chip_ha_tang",
    "robotics",
    "cybersecurity",
    "chinh_sach_cuoc_dua_toan_cau",
    "radar_khu_vuc",
    "watchlist_24_72h",
    "source_desk",
}


def _host(url: str) -> str:
    host = (urlparse(str(url or "")).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def validate(payload: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    if payload.get("schema_version") != TECH_PUBLICATION_SCHEMA:
        errs.append(f"schema_version must be {TECH_PUBLICATION_SCHEMA}")
    sections = payload.get("sections")
    if not isinstance(sections, dict):
        return ["sections must be an object"]
    missing = sorted(REQUIRED_SECTIONS - set(sections.keys()))
    if missing:
        errs.append(f"missing sections: {', '.join(missing)}")

    seen_story_ids: set[str] = set()
    for sec_name, items in sections.items():
        if sec_name == "source_desk":
            continue
        if not isinstance(items, list):
            errs.append(f"sections.{sec_name} must be a list")
            continue
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                errs.append(f"sections.{sec_name}[{idx}] must be object")
                continue
            story_id = str(item.get("id") or "").strip()
            if story_id and sec_name != "watchlist_24_72h":
                if story_id in seen_story_ids:
                    errs.append(f"duplicate story id: {story_id}")
                seen_story_ids.add(story_id)
            links = item.get("links") or []
            if not isinstance(links, list):
                errs.append(f"sections.{sec_name}[{idx}].links must be list")
                continue
            seen_domains: set[str] = set()
            for link_idx, link in enumerate(links):
                if not isinstance(link, dict):
                    errs.append(f"sections.{sec_name}[{idx}].links[{link_idx}] must be object")
                    continue
                url = str(link.get("url") or "").strip()
                if not url.startswith("http"):
                    errs.append(f"sections.{sec_name}[{idx}].links[{link_idx}] invalid url")
                host = _host(url)
                if host in seen_domains:
                    errs.append(f"sections.{sec_name}[{idx}] duplicate source domain {host}")
                if host:
                    seen_domains.add(host)
            source_count = int(item.get("source_count") or 0)
            domain_count = int(item.get("independent_domain_count") or 0)
            label = str(item.get("confirmation_label") or "")
            official = bool(item.get("official_source_present"))
            if label == "hot" and not (domain_count >= 2 or (official and domain_count >= 2)):
                errs.append(f"sections.{sec_name}[{idx}] hot label violates confirmation rule")
            if label == "chua_duoc_xac_nhan_rong" and source_count < 1:
                errs.append(f"sections.{sec_name}[{idx}] unconfirmed story needs at least one source")
    return errs


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate tech publication JSON")
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
    print("OK: tech publication valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
