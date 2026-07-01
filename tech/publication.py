#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tech.common import (
    GDELT_JSON, NEWS_CLEAN, PUBLICATION_JSON, PUBLICATION_SCHEMA, WINDOW_HOURS,
    canonical_url, dump_json, freshness_hours, host_from_url, hot_rule,
    infer_section, load_json, looks_tech, sanitize_public_text, source_type, story_id,
)

SECTIONS = [
    "tong_quan", "tin_nong", "model_agent_moi", "cach_dung_ai",
    "open_source_developer_tools", "chip_ha_tang", "robotics", "cybersecurity",
    "chinh_sach_cuoc_dua_toan_cau", "radar_khu_vuc", "watchlist_24_72h",
]


def title_key(text: str) -> str:
    cleaned = re.sub(r"[^0-9a-zA-Z\u00c0-\u024f\u0400-\u04ff\u0600-\u06ff\u3040-\u30ff\u3400-\u9fff]+", " ", str(text).lower())
    return " ".join(x for x in cleaned.split() if len(x) > 2)[:180]


def similar(a: str, b: str) -> bool:
    ka, kb = title_key(a), title_key(b)
    if not ka or not kb:
        return False
    if ka == kb:
        return True
    return SequenceMatcher(None, ka, kb).ratio() >= 0.79


def make_link(url: str, title: str, published_at: str = "") -> dict[str, str]:
    return {
        "url": canonical_url(url),
        "title": str(title or "").strip(),
        "domain": host_from_url(url),
        "source_type": source_type(url),
        "published_at": str(published_at or "").strip(),
    }


def add_link(story: dict[str, Any], link: dict[str, str]) -> None:
    if not link["url"] or not link["domain"]:
        return
    if any(x.get("domain") == link["domain"] for x in story["links"]):
        return
    story["links"].append(link)


def crawl_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for article in payload.get("articles") or []:
        title = str(article.get("title") or "").strip()
        text = str(article.get("text") or "").strip()
        url = str(article.get("url") or "").strip()
        if not title or not url or not looks_tech(title + " " + text):
            continue
        story = {
            "headline_raw": title,
            "excerpt": text[:1200],
            "links": [],
            "section_hint": infer_section(title + " " + text),
        }
        add_link(story, make_link(url, title, str(article.get("published_at") or "")))
        out.append(story)
    return out


def event_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for event in payload.get("events") or []:
        title = str(event.get("title") or "").strip()
        excerpt = str(event.get("raw_summary") or "").strip()
        if not title:
            continue
        story = {
            "headline_raw": title,
            "excerpt": excerpt[:1200],
            "links": [],
            "section_hint": str(event.get("section") or infer_section(title + " " + excerpt)),
        }
        for url in event.get("source_urls") or []:
            add_link(story, make_link(str(url), title, str(event.get("reported_at") or "")))
        if story["links"]:
            out.append(story)
    return out


def merge_candidates(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for item in items:
        target = next((x for x in merged if similar(item["headline_raw"], x["headline_raw"])), None)
        if target is None:
            target = {
                "headline_raw": item["headline_raw"],
                "excerpt": item["excerpt"],
                "links": [],
                "section_hint": item["section_hint"],
            }
            merged.append(target)
        if len(item.get("excerpt") or "") > len(target.get("excerpt") or ""):
            target["excerpt"] = item["excerpt"]
        for link in item["links"]:
            add_link(target, link)
    return merged


def finalize_metrics(story: dict[str, Any]) -> dict[str, Any]:
    links = story["links"]
    types = [x["source_type"] for x in links]
    is_hot, independent_count, official_present, community_count = hot_rule(types)
    published = [x.get("published_at") for x in links]
    story.update({
        "id": story_id(story["headline_raw"]),
        "source_count": len(links),
        "independent_domain_count": independent_count,
        "official_source_present": official_present,
        "community_domain_count": community_count,
        "confirmation_label": "hot" if is_hot else "chua_duoc_xac_nhan_rong",
        "freshness_hours": freshness_hours(published),
    })
    return story


def extract_json(text: str) -> Any:
    raw = str(text or "").strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.I | re.S)
    start = raw.find("[")
    end = raw.rfind("]")
    if start < 0 or end < start:
        raise ValueError("No JSON array in model response")
    return json.loads(raw[start:end + 1])


def gemini_edit(stories: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return {}
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
        model = genai.GenerativeModel(model_name)
        packets = [
            {
                "id": x["id"],
                "title": x["headline_raw"],
                "excerpt": x["excerpt"][:700],
                "section_hint": x["section_hint"],
                "source_types": [link["source_type"] for link in x["links"]],
            }
            for x in stories[:30]
        ]
        prompt = """
Bạn là biên tập viên báo Công nghệ & AI tiếng Việt. Chỉ dùng dữ liệu được cung cấp.
Trả về JSON array, mỗi phần tử đúng các trường:
id, headline, summary, why_it_matters, practical_use, section.
Không tạo URL, số liệu, tên sản phẩm hoặc kết luận ngoài nguồn. Không nhắc cách thu thập dữ liệu.
Headline rõ và ngắn. Summary 2-4 câu. practical_use chỉ viết khi nguồn thật sự cho thấy cách ứng dụng; nếu không thì để chuỗi rỗng.
section chỉ được chọn một trong: tin_nong, model_agent_moi, cach_dung_ai, open_source_developer_tools, chip_ha_tang, robotics, cybersecurity, chinh_sach_cuoc_dua_toan_cau, radar_khu_vuc.
Dữ liệu:
""" + json.dumps(packets, ensure_ascii=False)
        response = model.generate_content(prompt)
        rows = extract_json(getattr(response, "text", ""))
        return {str(x.get("id")): x for x in rows if isinstance(x, dict) and x.get("id")}
    except Exception as exc:
        print(f"Editorial fallback used: {exc}", file=sys.stderr)
        return {}


def fallback_summary(text: str) -> str:
    clean = sanitize_public_text(re.sub(r"\s+", " ", str(text or "")))
    return clean[:520].rstrip(" ,;:-")


def build_publication(crawl: dict[str, Any], gdelt: dict[str, Any]) -> dict[str, Any]:
    merged = merge_candidates(event_candidates(gdelt) + crawl_candidates(crawl))
    stories = [finalize_metrics(x) for x in merged if x.get("links")]
    stories.sort(key=lambda x: (
        0 if x["confirmation_label"] == "hot" else 1,
        -x["independent_domain_count"],
        x["freshness_hours"],
        -x["source_count"],
    ))
    stories = stories[:40]
    edits = gemini_edit(stories)
    sections: dict[str, list[dict[str, Any]]] = {name: [] for name in SECTIONS}
    for story in stories:
        edit = edits.get(story["id"], {})
        headline = sanitize_public_text(edit.get("headline") or story["headline_raw"])
        summary = sanitize_public_text(edit.get("summary") or fallback_summary(story["excerpt"]))
        why = sanitize_public_text(edit.get("why_it_matters") or summary[:260])
        practical = sanitize_public_text(edit.get("practical_use") or "")
        section = str(edit.get("section") or story["section_hint"])
        if section not in sections or section in {"tong_quan", "watchlist_24_72h"}:
            section = story["section_hint"] if story["section_hint"] in sections else "tin_nong"
        public = {
            "id": story["id"],
            "headline": headline,
            "summary": summary,
            "why_it_matters": why,
            "practical_use": practical,
            "confirmation_label": story["confirmation_label"],
            "source_count": story["source_count"],
            "independent_domain_count": story["independent_domain_count"],
            "official_source_present": story["official_source_present"],
            "community_domain_count": story["community_domain_count"],
            "freshness_hours": story["freshness_hours"],
            "links": story["links"][:6],
        }
        sections[section].append(public)

    all_public = [item for name in SECTIONS for item in sections[name] if name not in {"tong_quan", "watchlist_24_72h"}]
    sections["watchlist_24_72h"] = all_public[:8]
    sections["tong_quan"] = [{
        "id": "overview-72h",
        "headline": "Công nghệ và AI trong 72 giờ gần nhất",
        "summary": f"Bản tin chọn lọc {len(all_public)} diễn biến đáng chú ý, ưu tiên phát minh, sản phẩm, mã nguồn, hạ tầng và chính sách có nguồn xác nhận rõ ràng.",
        "why_it_matters": "Các tín hiệu cộng đồng được dùng để phát hiện chủ đề, nhưng không thay thế xác nhận từ báo độc lập hoặc nguồn chính thức.",
        "practical_use": "",
        "confirmation_label": "overview",
        "source_count": sum(x["source_count"] for x in all_public),
        "independent_domain_count": len({link["domain"] for x in all_public for link in x["links"] if link["source_type"] == "independent_news"}),
        "official_source_present": any(x["official_source_present"] for x in all_public),
        "community_domain_count": len({link["domain"] for x in all_public for link in x["links"] if link["source_type"] == "community"}),
        "freshness_hours": 72,
        "links": [],
    }]
    return {
        "schema_version": PUBLICATION_SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "window_hours": WINDOW_HOURS,
        "sections": sections,
        "stats": {
            "story_count": len(all_public),
            "crawl_article_count": len(crawl.get("articles") or []),
            "event_count": len(gdelt.get("events") or []),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--crawl-input", type=Path, default=NEWS_CLEAN)
    parser.add_argument("--event-input", type=Path, default=GDELT_JSON)
    parser.add_argument("--output", type=Path, default=PUBLICATION_JSON)
    args = parser.parse_args()
    crawl = load_json(args.crawl_input, {})
    events = load_json(args.event_input, {})
    publication = build_publication(crawl, events)
    if publication["stats"]["story_count"] <= 0:
        raise SystemExit("No grounded technology stories were produced.")
    dump_json(args.output, publication)
    print(f"Wrote {publication['stats']['story_count']} stories to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
