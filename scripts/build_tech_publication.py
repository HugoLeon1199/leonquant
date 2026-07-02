#!/usr/bin/env python3
"""Build the standalone public technology & AI publication."""

from __future__ import annotations

import argparse
import json
import re
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

WINDOW_HOURS = 72
MAX_SUMMARY_CHARS = 340
MAX_WHY_CHARS = 220

SECTION_LABELS = {
    "tong_quan": "tong quan cong nghe va AI",
    "tin_nong": "dien bien dang chu y",
    "model_agent_moi": "model va agent moi",
    "cach_dung_ai": "cach ung dung AI",
    "open_source_developer_tools": "cong cu ma nguon mo va developer tools",
    "chip_ha_tang": "chip va ha tang tinh toan",
    "robotics": "robotics va tu dong hoa",
    "cybersecurity": "an ninh mang va an toan AI",
    "chinh_sach_cuoc_dua_toan_cau": "chinh sach va canh tranh toan cau",
    "radar_khu_vuc": "tin hieu khu vuc",
}

WHY_IT_MATTERS_BY_SECTION = {
    "model_agent_moi": "Dien bien nay co the anh huong den lua chon mo hinh, ky vong nang luc va toc do dua tinh nang moi ra thi truong.",
    "cach_dung_ai": "Dien bien nay dang chu y vi no tac dong truc tiep den cach doanh nghiep va doi ky thuat dua AI vao quy trinh thuc te.",
    "open_source_developer_tools": "Dien bien nay can duoc theo doi vi no anh huong truc tiep den cong cu, SDK va nhip trien khai cua doi phat trien.",
    "chip_ha_tang": "Dien bien nay quan trong vi no lien quan den chi phi tinh toan, nguon cung ha tang va toc do mo rong nang luc AI.",
    "robotics": "Dien bien nay dang chu y vi no co the thay doi toc do thuong mai hoa robot, agent vat ly va he thong tu dong.",
    "cybersecurity": "Dien bien nay can duoc theo doi sat vi no anh huong den rui ro bao mat, kha nang phong thu va muc do tin cay cua he thong AI.",
    "chinh_sach_cuoc_dua_toan_cau": "Dien bien nay quan trong vi no co the thay doi quy dinh, huong dau tu va cach cac ben lon canh tranh trong 72 gio toi.",
    "radar_khu_vuc": "Dien bien nay giup bo sung tin hieu ngoai My, qua do theo doi sat hon nhung dich chuyen dang len o cac thi truong khu vuc.",
    "tin_nong": "Dien bien nay dang duoc theo doi vi no co the nhanh chong tac dong den san pham, dau tu hoac ky vong thi truong trong 72 gio toi.",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def sanitize_public_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
    replacements = {
        "pipeline": "he thong",
        "crawler": "nguon tong hop",
        "gdelt": "du lieu doi chieu",
        "gemini": "mo hinh",
        "bigquery": "du lieu doi chieu",
    }
    for raw, repl in replacements.items():
        cleaned = re.sub(raw, repl, cleaned, flags=re.IGNORECASE)
    return cleaned.strip(" -,:;")


def safe_trim(text: str, limit: int) -> str:
    cleaned = sanitize_public_text(text)
    if len(cleaned) <= limit:
        return cleaned
    clipped = cleaned[:limit].rsplit(" ", 1)[0].strip()
    return clipped if clipped else cleaned[:limit].strip()


def canonical_title(text: str) -> str:
    title = safe_trim(str(text or ""), 120)
    title = re.sub(r"\b24\s*-\s*48h\b", "72 gio", title, flags=re.IGNORECASE)
    title = re.sub(r"\b24\s*48h\b", "72 gio", title, flags=re.IGNORECASE)
    return title or "Tin cong nghe va AI"


def detect_language_hint(text: str) -> str:
    hay = str(text or "")
    if re.search(r"[\u4e00-\u9fff]", hay):
        return "zh"
    if re.search(r"[\u3040-\u30ff]", hay):
        return "ja"
    if re.search(r"[\uac00-\ud7af]", hay):
        return "ko"
    return "latin"


def build_summary(
    *,
    headline: str,
    section: str,
    source_count: int,
    independent_domain_count: int,
    official_source_present: bool,
    freshness_hours: int,
    text: str = "",
) -> str:
    section_label = SECTION_LABELS.get(section, "dien bien cong nghe va AI")
    headline_clean = canonical_title(headline)
    lang = detect_language_hint(text or headline)
    detail = (
        "Noi dung goc cho thay nhom tin nay dang tang toc trong 72 gio qua."
        if lang == "latin"
        else "Noi dung goc cho thay day la mot dien bien moi, nhung ban cong khai uu tien tom tat ngan gon de tranh day van ban tho."
    )
    if independent_domain_count >= 2:
        confirm = f"Hien da co {independent_domain_count} nguon doc lap cung nhac den cau chuyen nay."
    elif official_source_present and source_count >= 2:
        confirm = "Tin hieu den tu nguon chinh thuc va da co it nhat mot nguon doc lap theo doi them."
    else:
        confirm = "Hien tin hieu van con hep, nen can cho them xac nhan cheo tu cac bao doc lap."
    summary = " ".join(
        [
            f"Trong 72 gio qua, noi dung xoay quanh '{headline_clean}' noi len trong nhom {section_label}.",
            detail,
            confirm,
            f"Muc do tuoi moi hien o khoang {max(0, min(WINDOW_HOURS, freshness_hours))} gio tinh den luc bien tap.",
        ]
    )
    return safe_trim(summary, MAX_SUMMARY_CHARS)


def build_why_it_matters(section: str, confirmation_label: str) -> str:
    base = WHY_IT_MATTERS_BY_SECTION.get(section, WHY_IT_MATTERS_BY_SECTION["tin_nong"])
    if confirmation_label == "chua_duoc_xac_nhan_rong":
        base = f"{base} Hien cau chuyen nay moi co tin hieu hep, vi vay can theo doi them truoc khi xem la xu huong lon."
    return safe_trim(base, MAX_WHY_CHARS)


def build_deck(headline: str, section: str) -> str:
    section_label = SECTION_LABELS.get(section, "dien bien cong nghe va AI")
    return safe_trim(f"Diem nhanh 72 gio qua trong nhom {section_label}: {canonical_title(headline)}.", 150)


def freshness_from_values(values: list[str]) -> int:
    parsed: list[datetime] = []
    for value in values:
        raw = str(value or "").strip()
        if not raw:
            continue
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        parsed.append(dt.astimezone(timezone.utc))
    if not parsed:
        return WINDOW_HOURS
    return max(0, min(WINDOW_HOURS, int((datetime.now(timezone.utc) - max(parsed)).total_seconds() // 3600)))


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
        raw_text = str(article.get("text") or "").strip()
        if matched is None:
            matched = {
                "story_key": key,
                "headline": title,
                "raw_text": raw_text,
                "links": [],
                "source_domains": set(),
                "official_source_present": False,
                "published_values": [],
            }
            clusters.append(matched)
        elif len(raw_text) > len(str(matched.get("raw_text") or "")):
            matched["raw_text"] = raw_text
        matched["links"].append(
            {
                "url": str(article.get("url") or ""),
                "title": canonical_title(title),
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
    confirmation_label = (
        "hot" if independent_domain_count >= 2 or (official and independent_domain_count >= 2) else "chua_duoc_xac_nhan_rong"
    )
    section = infer_section(cluster["headline"] + " " + str(cluster.get("raw_text") or ""), fallback="tin_nong")
    fresh_hours = freshness_from_values(cluster["published_values"])
    return {
        "id": normalize_story_key(cluster["headline"])[:80],
        "headline": canonical_title(cluster["headline"]),
        "deck": build_deck(cluster["headline"], section),
        "summary": build_summary(
            headline=cluster["headline"],
            section=section,
            source_count=source_count,
            independent_domain_count=independent_domain_count,
            official_source_present=official,
            freshness_hours=fresh_hours,
            text=str(cluster.get("raw_text") or ""),
        ),
        "why_it_matters": build_why_it_matters(section, confirmation_label),
        "confirmation_label": confirmation_label,
        "source_count": source_count,
        "independent_domain_count": independent_domain_count,
        "official_source_present": official,
        "freshness_hours": fresh_hours,
        "links": cluster["links"][:5],
        "tags": [section],
    }


def story_from_gdelt(event: dict[str, Any]) -> dict[str, Any]:
    source_count = int(event.get("source_count") or 0)
    independent_domain_count = int(event.get("independent_domain_count") or 0)
    official = bool(event.get("official_source_present"))
    confirmation_label = (
        "hot" if independent_domain_count >= 2 or (official and independent_domain_count >= 2) else "chua_duoc_xac_nhan_rong"
    )
    links = [
        {
            "url": u,
            "title": canonical_title(event.get("title") or u),
            "source": canonical_domain(u),
            "published_at": str(event.get("reported_at") or ""),
        }
        for u in (event.get("source_urls") or [])[:5]
    ]
    tags = [str(tag) for tag in (event.get("topic_tags") or []) if str(tag).strip()]
    section = tags[0] if tags else infer_section((event.get("title") or "") + " " + (event.get("summary") or ""))
    fresh_hours = int(event.get("freshness_hours") or WINDOW_HOURS)
    return {
        "id": str(event.get("event_id") or ""),
        "headline": canonical_title(str(event.get("title") or "").strip()),
        "deck": build_deck(str(event.get("title") or "").strip(), section),
        "summary": build_summary(
            headline=str(event.get("title") or "").strip(),
            section=section,
            source_count=source_count,
            independent_domain_count=independent_domain_count,
            official_source_present=official,
            freshness_hours=fresh_hours,
            text=str(event.get("summary") or ""),
        ),
        "why_it_matters": build_why_it_matters(section, confirmation_label),
        "confirmation_label": confirmation_label,
        "source_count": source_count,
        "independent_domain_count": independent_domain_count,
        "official_source_present": official,
        "freshness_hours": fresh_hours,
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
            "headline": "Cong nghe va AI 72 gio qua",
            "deck": "Tong hop 72 gio qua tu nhung cau chuyen co link nguon ro rang va do moi du de theo doi.",
            "summary": safe_trim(
                "Ban 72 gio nay uu tien nhung cau chuyen co lien ket nguon ro rang, do tuoi moi cao va tin hieu xac nhan hop ly. "
                f"Hien co {len(stories)} cau chuyen duoc dua vao ban cong khai, tap trung vao model moi, cong cu phat trien, chip ha tang va cac dich chuyen chinh sach. "
                "Tin chi co mot nguon se duoc gan nhan can theo doi them.",
                MAX_SUMMARY_CHARS,
            ),
            "why_it_matters": safe_trim(
                "Ban tong hop nay giup doc nhanh nhip cong nghe va AI trong 72 gio qua ma van giu duoc link nguon de tu kiem tra lai khi can.",
                MAX_WHY_CHARS,
            ),
            "confirmation_label": "overview",
            "source_count": len(source_desk),
            "independent_domain_count": len({canonical_domain(x.get('url') or '') for x in source_desk if x.get('url')}),
            "official_source_present": any(is_official_host(x.get("url") or "") for x in source_desk),
            "freshness_hours": WINDOW_HOURS,
            "links": unique_links_by_domain(source_desk, limit=5),
            "tags": ["tong_quan"],
        }
    ]
    return {
        "schema_version": TECH_PUBLICATION_SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "window_hours": WINDOW_HOURS,
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
