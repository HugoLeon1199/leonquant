#!/usr/bin/env python3
"""Build the standalone public technology & AI publication."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from scripts.tech_common import (
    TECH_GDELT_OUTPUT,
    TECH_NEWS_FOR_AI_CLEAN,
    TECH_PUBLICATION_OUTPUT,
    TECH_PUBLICATION_SCHEMA,
    TECH_PUBLICATION_WEB_OUTPUT,
    canonical_domain,
    dump_json,
    infer_section,
    is_official_host,
    normalize_story_key,
)

ROOT = Path(__file__).resolve().parents[1]

SECTIONS = [
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
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def cluster_clean_articles(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    clusters: list[dict[str, Any]] = []
    for article in articles:
        title = str(article.get("title") or "").strip()
        if not title:
            continue
        key = normalize_story_key(title)
        domain = canonical_domain(str(article.get("url") or ""))
        matched = None
        for cluster in clusters:
            if key and key == cluster["story_key"]:
                matched = cluster
                break
            if similar(title.lower(), cluster["headline"].lower()) >= 0.78:
                matched = cluster
                break
        if matched is None:
            matched = {
                "story_key": key,
                "headline": title,
                "summary": str(article.get("text") or "")[:600].strip(),
                "links": [],
                "source_domains": set(),
                "official_source_present": False,
                "published_values": [],
            }
            clusters.append(matched)
        matched["links"].append(
            {
                "url": str(article.get("url") or ""),
                "title": title,
                "source": str(article.get("source") or domain),
                "published_at": str(article.get("published_at") or ""),
            }
        )
        if domain:
            matched["source_domains"].add(domain)
            if is_official_host(domain):
                matched["official_source_present"] = True
        if str(article.get("published_at") or "").strip():
            matched["published_values"].append(str(article.get("published_at") or "").strip())
    return clusters


def story_from_cluster(cluster: dict[str, Any]) -> dict[str, Any]:
    domains = sorted(cluster["source_domains"])
    source_count = len(cluster["links"])
    independent_domain_count = len(domains)
    official = bool(cluster["official_source_present"])
    is_hot = independent_domain_count >= 2 or (official and independent_domain_count >= 2)
    return {
        "id": normalize_story_key(cluster["headline"])[:80],
        "headline": cluster["headline"],
        "deck": cluster["headline"],
        "summary": cluster["summary"],
        "why_it_matters": cluster["summary"][:240],
        "confirmation_label": "hot" if is_hot else "chua_duoc_xac_nhan_rong",
        "source_count": source_count,
        "independent_domain_count": independent_domain_count,
        "official_source_present": official,
        "freshness_hours": 48,
        "links": cluster["links"][:5],
        "tags": [infer_section(cluster["headline"] + " " + cluster["summary"], fallback="tin_nong")],
    }


def story_from_gdelt(event: dict[str, Any]) -> dict[str, Any]:
    source_count = int(event.get("source_count") or 0)
    independent_domain_count = int(event.get("independent_domain_count") or 0)
    official = bool(event.get("official_source_present"))
    is_hot = independent_domain_count >= 2 or (official and independent_domain_count >= 2)
    links = [
        {
            "url": u,
            "title": event.get("title") or u,
            "source": canonical_domain(u),
            "published_at": str(event.get("reported_at") or ""),
        }
        for u in (event.get("source_urls") or [])[:5]
    ]
    tags = [str(tag) for tag in (event.get("topic_tags") or []) if str(tag).strip()]
    section = tags[0] if tags else infer_section((event.get("title") or "") + " " + (event.get("summary") or ""))
    return {
        "id": str(event.get("event_id") or ""),
        "headline": str(event.get("title") or "").strip(),
        "deck": str(event.get("summary") or "").strip()[:180],
        "summary": str(event.get("summary") or "").strip(),
        "why_it_matters": str(event.get("summary") or "").strip()[:240],
        "confirmation_label": "hot" if is_hot else "chua_duoc_xac_nhan_rong",
        "source_count": source_count,
        "independent_domain_count": independent_domain_count,
        "official_source_present": official,
        "freshness_hours": int(event.get("freshness_hours") or 72),
        "links": links,
        "tags": [section, *tags[1:3]],
    }


def dedupe_stories(stories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: list[dict[str, Any]] = []
    for story in stories:
        headline = str(story.get("headline") or "")
        key = normalize_story_key(headline)
        if any(key and key == normalize_story_key(str(prev.get("headline") or "")) for prev in seen):
            continue
        if any(similar(headline.lower(), str(prev.get("headline") or "").lower()) >= 0.82 for prev in seen):
            continue
        seen.append(story)
        out.append(story)
    return out


def unique_links_by_domain(links: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen_domains: set[str] = set()
    for link in links:
        url = str(link.get("url") or "").strip()
        if not url:
            continue
        domain = canonical_domain(url)
        if not domain or domain in seen_domains:
            continue
        seen_domains.add(domain)
        out.append(link)
        if len(out) >= limit:
            break
    return out


def build_publication(clean_payload: dict[str, Any], gdelt_payload: dict[str, Any]) -> dict[str, Any]:
    clean_articles = clean_payload.get("articles") or []
    crawl_clusters = cluster_clean_articles(clean_articles)
    crawl_stories = [story_from_cluster(cluster) for cluster in crawl_clusters]
    gdelt_stories = [story_from_gdelt(evt) for evt in (gdelt_payload.get("events") or [])]
    stories = dedupe_stories(gdelt_stories + crawl_stories)

    sections: dict[str, list[dict[str, Any]]] = {name: [] for name in SECTIONS}
    source_desk: list[dict[str, Any]] = []
    for story in stories:
        section = infer_section(
            " ".join([story.get("headline") or "", story.get("summary") or "", " ".join(story.get("tags") or [])]),
            fallback="tin_nong",
        )
        sections.setdefault(section, []).append(story)
        for link in story.get("links") or []:
            source_desk.append(link)

    sections["watchlist_24_72h"] = sorted(
        stories,
        key=lambda s: (
            0 if s.get("confirmation_label") == "hot" else 1,
            -int(s.get("independent_domain_count") or 0),
        ),
    )[:8]
    sections["source_desk"] = source_desk[:40]
    sections["tong_quan"] = [
        {
            "id": "tong-quan-1",
            "headline": "Bức tranh công nghệ & AI 24-48h",
            "deck": "Tổng hợp các cụm tin có khả năng hành động hoặc ảnh hưởng thị trường công nghệ.",
            "summary": (
                f"Pipeline tech hiện ghi nhận {len(stories)} cụm chuyện từ nguồn crawl riêng và GDELT tech riêng. "
                f"Các cụm được ưu tiên theo độ phủ nguồn, tín hiệu official-vs-independent và mức độ tươi mới."
            ),
            "why_it_matters": "Trang tech chỉ giữ các câu chuyện có grounding URL rõ ràng và không tự fill nội dung yếu.",
            "confirmation_label": "overview",
            "source_count": len(source_desk),
            "independent_domain_count": len({canonical_domain(x.get('url') or '') for x in source_desk if x.get('url')}),
            "official_source_present": any(is_official_host(x.get("url") or "") for x in source_desk),
            "freshness_hours": 48,
            "links": unique_links_by_domain(source_desk, limit=5),
            "tags": ["tong_quan"],
        }
    ]
    return {
        "schema_version": TECH_PUBLICATION_SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "sections": sections,
        "stats": {
            "story_count": len(stories),
            "crawl_cluster_count": len(crawl_clusters),
            "gdelt_event_count": len(gdelt_payload.get("events") or []),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build tech_publication.json from clean crawl + tech GDELT")
    parser.add_argument("--crawl-input", type=Path, default=TECH_NEWS_FOR_AI_CLEAN)
    parser.add_argument("--gdelt-input", type=Path, default=TECH_GDELT_OUTPUT)
    parser.add_argument("--output", type=Path, default=TECH_PUBLICATION_OUTPUT)
    parser.add_argument("--web-output", type=Path, default=TECH_PUBLICATION_WEB_OUTPUT)
    args = parser.parse_args()

    crawl_payload = load_json(args.crawl_input)
    gdelt_payload = load_json(args.gdelt_input)
    publication = build_publication(crawl_payload, gdelt_payload)
    dump_json(args.output, publication)
    dump_json(args.web_output, publication)
    print(f"Wrote tech publication -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
