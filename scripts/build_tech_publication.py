#!/usr/bin/env python3
"""Build the standalone AI Frontier Radar 72h publication."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.tech_common import (
    TECH_GDELT_OUTPUT,
    TECH_NEWS_FOR_AI_CLEAN,
    TECH_PUBLICATION_OUTPUT,
    TECH_PUBLICATION_WEB_OUTPUT,
    TECH_VALIDATION_JSON,
    canonical_domain,
    dump_json,
    is_official_host,
)

SCHEMA_VERSION = "ai-frontier-radar-72h-v1"
WINDOW_HOURS = 72
MAX_LINKS = 150
MIN_MUST_READ = 10

RADAR_SECTIONS = {
    "ai_models": "AI Models",
    "local_ai_china_ai": "Local AI / China AI",
    "ai_tools": "AI Tools",
    "automation_mcp_agents": "Automation / MCP / Agents",
    "open_source_hot": "Open Source Hot",
    "ai_business_money": "AI Business & Money",
    "industry_impact": "Industry Impact",
    "ai_knowledge": "AI Knowledge",
    "founder_ideas_for_leon": "Founder Ideas for Leon",
    "full_link_radar": "Full Link Radar",
}

MUST_READ_CATEGORIES = {
    "ai_models": "model",
    "local_ai_china_ai": "local_ai",
    "ai_tools": "tool",
    "automation_mcp_agents": "automation",
    "open_source_hot": "opensource",
    "ai_business_money": "business",
    "industry_impact": "industry",
    "ai_knowledge": "knowledge",
}

FORBIDDEN_PUBLIC_TERMS = ("pipeline", "crawler", "gdelt", "gemini", "bigquery")
OPEN_SOURCE_HINTS = ("github", "open source", "open-source", "repo", "framework", "sdk", "ollama", "llama.cpp", "vllm", "sglang")
AUTOMATION_HINTS = ("mcp", "agent", "automation", "workflow", "langgraph", "crewai", "openhands", "n8n", "make", "zapier", "cursor", "claude code")
LOCAL_CHINA_HINTS = ("ollama", "lm studio", "openwebui", "llama.cpp", "vllm", "sglang", "qwen", "deepseek", "kimi", "minimax", "glm", "doubao", "china", "chinese")
MODEL_HINTS = ("model", "llm", "gpt", "claude", "llama", "deepseek", "qwen", "mistral", "copilot", "reasoning", "multimodal")
TOOL_HINTS = ("tool", "editor", "coding", "video", "image", "voice", "office", "marketing", "sql", "spreadsheet")
BUSINESS_HINTS = ("startup", "funding", "revenue", "saas", "agency", "pricing", "monetize", "business", "market", "enterprise")
INDUSTRY_HINTS = ("finance", "education", "health", "healthcare", "law", "robotics", "ecommerce", "gaming", "media", "marketing")
KNOWLEDGE_HINTS = ("guide", "how to", "best practices", "architecture", "benchmark", "concept", "tutorial", "model card")
FOUNDER_AREAS = (
    "video automation",
    "coding workflow",
    "local AI stack",
    "AI automation service",
    "AI content system",
    "MCP tools",
    "open-source integration",
    "agent workflow",
    "SaaS validation",
    "AI research habit",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def clean_text(text: str) -> str:
    out = re.sub(r"\s+", " ", str(text or "")).strip()
    replacements = {
        "pipeline": "he thong",
        "crawler": "nguon tong hop",
        "gdelt": "du lieu doi chieu",
        "gemini": "mo hinh",
        "bigquery": "du lieu doi chieu",
    }
    for raw, repl in replacements.items():
        out = re.sub(raw, repl, out, flags=re.IGNORECASE)
    return out.strip(" -,:;")


def trim_sentence(text: str, limit: int) -> str:
    text = clean_text(text)
    if len(text) <= limit:
        return text
    clipped = text[:limit]
    for sep in (". ", "! ", "? ", "; "):
        pos = clipped.rfind(sep)
        if pos > limit * 0.55:
            return clipped[: pos + 1].strip()
    if " " in clipped:
        clipped = clipped.rsplit(" ", 1)[0]
    return clipped.strip()


def detect_language(text: str) -> str:
    hay = str(text or "")
    if re.search(r"[\u4e00-\u9fff]", hay):
        return "zh"
    if re.search(r"[\u3040-\u30ff]", hay):
        return "ja"
    if re.search(r"[\uac00-\ud7af]", hay):
        return "ko"
    return "latin"


def parse_dt(value: Any) -> datetime | None:
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


def freshness_hours(published_at: Any) -> int:
    dt = parse_dt(published_at)
    if dt is None:
        return WINDOW_HOURS
    return max(0, min(WINDOW_HOURS, int((datetime.now(timezone.utc) - dt).total_seconds() // 3600)))


def source_type(source: str, url: str) -> str:
    host = canonical_domain(url) or str(source or "").strip().lower()
    if is_official_host(host):
        return "official"
    if any(part in host for part in ("discuss.", "forum.", "forums.", "community.", "news.ycombinator", "lobste.rs", "github.com", "stackoverflow.com")):
        return "community"
    return "independent"


def infer_section(title: str, text: str, url: str = "") -> str:
    hay = f"{title} {text} {url}".lower()
    if any(hint in hay for hint in LOCAL_CHINA_HINTS):
        return "local_ai_china_ai"
    if any(hint in hay for hint in AUTOMATION_HINTS):
        return "automation_mcp_agents"
    if any(hint in hay for hint in OPEN_SOURCE_HINTS):
        return "open_source_hot"
    if any(hint in hay for hint in TOOL_HINTS):
        return "ai_tools"
    if any(hint in hay for hint in BUSINESS_HINTS):
        return "ai_business_money"
    if any(hint in hay for hint in INDUSTRY_HINTS):
        return "industry_impact"
    if any(hint in hay for hint in KNOWLEDGE_HINTS):
        return "ai_knowledge"
    if any(hint in hay for hint in MODEL_HINTS):
        return "ai_models"
    return "ai_tools"


def novelty_score(title: str) -> int:
    hay = title.lower()
    return 2 if any(word in hay for word in ("launch", "release", "new", "open", "top", "first", "preview")) else 1


def applicability_score(section: str) -> int:
    return {
        "local_ai_china_ai": 5,
        "automation_mcp_agents": 5,
        "ai_tools": 5,
        "open_source_hot": 4,
        "ai_models": 4,
        "ai_business_money": 4,
        "industry_impact": 3,
        "ai_knowledge": 3,
    }.get(section, 2)


def source_quality_score(kind: str) -> int:
    return {"official": 5, "independent": 4, "community": 3}.get(kind, 2)


def community_signal_score(kind: str, title: str, url: str) -> int:
    hay = f"{title} {url}".lower()
    score = 1
    if kind == "community":
        score += 1
    if "github.com" in hay or "huggingface" in hay:
        score += 1
    return min(score, 3)


def category_priority_score(section: str) -> int:
    return {
        "local_ai_china_ai": 5,
        "automation_mcp_agents": 5,
        "ai_tools": 5,
        "open_source_hot": 5,
        "ai_models": 4,
        "ai_business_money": 4,
        "ai_knowledge": 4,
        "industry_impact": 3,
    }.get(section, 2)


def compose_summary(title: str, section: str, published_at: Any, kind: str, body: str) -> str:
    label = RADAR_SECTIONS.get(section, section)
    age = freshness_hours(published_at)
    lang = detect_language(body or title)
    clue = (
        "Tin nay co nhieu goi y de mo link doc sau va test nhanh."
        if section in {"local_ai_china_ai", "automation_mcp_agents", "ai_tools", "open_source_hot"}
        else "Tin nay nen duoc doc nhanh de cap nhat trend va quyet dinh uu tien hoc them."
    )
    if lang != "latin":
        clue = "Nguon goc khong dung tieng Anh nen ban radar uu tien tom gon de Leon mo link va doc sau neu can."
    source_note = {
        "official": "Nguon goc nghieng ve thong bao chinh thuc.",
        "community": "Nguon goc nghieng ve trao doi cong dong va dau hieu su dung thuc te.",
        "independent": "Nguon goc nghieng ve bao hoac blog doc lap.",
    }.get(kind, "Nguon goc la mot tin hieu can doi chieu them.")
    summary = (
        f"Trong 72 gio qua, cau chuyen '{clean_text(title)}' noi len trong nhom {label}. "
        f"{source_note} {clue} Moc tuoi moi hien o khoang {age} gio."
    )
    return trim_sentence(summary, 280)


def compose_why_read(section: str, title: str) -> str:
    text = {
        "ai_models": f"Nen doc de xem mo hinh nao thuc su moi, co kha nang thu ngay, va co anh huong den lua chon stack sau '{clean_text(title)}'.",
        "local_ai_china_ai": f"Nen doc de tim stack local/free hoac tin hieu AI Trung Quoc co the mang ve test nhanh sau '{clean_text(title)}'.",
        "ai_tools": f"Nen doc de xem cong cu nao co the dua thang vao cong viec sau '{clean_text(title)}'.",
        "automation_mcp_agents": f"Nen doc de copy workflow agent, MCP hoac automation tu '{clean_text(title)}'.",
        "open_source_hot": f"Nen doc de xem repo/tool nao dang duoc chu y va co kha nang fork hoac tich hop sau '{clean_text(title)}'.",
        "ai_business_money": f"Nen doc de tim goc doanh thu, SaaS hoac dich vu co the hoc theo sau '{clean_text(title)}'.",
        "industry_impact": f"Nen doc de biet AI dang lam rung chuyen nganh nao qua '{clean_text(title)}'.",
        "ai_knowledge": f"Nen doc de lay khung kien thuc hoac ngon ngu moi can nam sau '{clean_text(title)}'.",
    }.get(section, f"Nen doc de biet vi sao '{clean_text(title)}' dang duoc nhac den trong 72 gio qua.")
    return trim_sentence(text, 190)


def compose_apply_now(section: str, title: str) -> str:
    text = {
        "ai_models": "Mo link de danh dau model can thu, so sanh voi stack hien tai, va ghi lai use case hop nhat cho Leon.",
        "local_ai_china_ai": "Kiem tra co the chay tren local stack cua Leon khong, co can Ollama, LM Studio hay vLLM khong.",
        "ai_tools": "Thu xem cong cu nay giai quyet duoc nut that nao trong coding, video, content, marketing hay SQL.",
        "automation_mcp_agents": "Xem co workflow nao copy duoc vao Cursor, Claude Code, n8n hay mot repo noi bo ngay tuan nay.",
        "open_source_hot": "Danh dau repo can fork, xem demo, doc README va note nhanh cach tich hop.",
        "ai_business_money": "Tim xem no mo ra dich vu, SaaS mini hay quy trinh ban duoc cho Leon khong.",
        "industry_impact": "Dung de nhin xem khach hang/nganh nao co the bi AI day nhanh va mo ra co hoi moi.",
        "ai_knowledge": "Doc nhanh de rut ra mot khung kien thuc moi va note vao danh sach can hoc.",
    }.get(section, f"Mo link '{clean_text(title)}' de xem co y nao copy duoc vao cong viec hay quyet dinh cua Leon.")
    return trim_sentence(text, 180)


def compose_use_case(section: str, title: str) -> str:
    return compose_apply_now(section, title)


def classify_must_read_category(section: str) -> str:
    return MUST_READ_CATEGORIES.get(section, "tool")


def score_candidate(section: str, kind: str, published_at: Any, title: str, url: str) -> int:
    fresh = max(1, 6 - min(5, freshness_hours(published_at) // 12))
    return (
        fresh
        + source_quality_score(kind)
        + category_priority_score(section)
        + applicability_score(section)
        + novelty_score(title)
        + community_signal_score(kind, title, url)
    )


def build_item(
    *,
    title: str,
    url: str,
    source: str,
    published_at: Any,
    section: str,
    body: str,
    kind: str,
    score: int,
) -> dict[str, Any]:
    return {
        "title": clean_text(title) or "Untitled link",
        "url": str(url).strip(),
        "source": str(source).strip() or canonical_domain(url),
        "published_at": str(published_at or ""),
        "category": classify_must_read_category(section),
        "importance": max(1, min(5, 1 + score // 5)),
        "why_read": compose_why_read(section, title),
        "apply_now": compose_apply_now(section, title),
        "why_interesting": compose_summary(title, section, published_at, kind, body),
        "use_case": compose_use_case(section, title),
        "source_count": 1,
        "tags": [section, kind],
        "score": score,
    }


def build_items_from_clean(clean_payload: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for article in clean_payload.get("articles") or []:
        title = str(article.get("title") or "").strip()
        url = str(article.get("url") or "").strip()
        if not title or not url.startswith("http"):
            continue
        body = str(article.get("text") or "").strip()
        section = infer_section(title, body, url)
        kind = source_type(str(article.get("source") or ""), url)
        score = score_candidate(section, kind, article.get("published_at"), title, url)
        out.append(
            build_item(
                title=title,
                url=url,
                source=str(article.get("source") or canonical_domain(url)),
                published_at=article.get("published_at"),
                section=section,
                body=body,
                kind=kind,
                score=score,
            )
        )
    return out


def build_items_from_gdelt(gdelt_payload: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for event in gdelt_payload.get("events") or []:
        url = str(event.get("primary_url") or "").strip()
        title = str(event.get("title") or "").strip()
        if not url.startswith("http") or not title:
            continue
        body = str(event.get("summary") or "").strip()
        section = infer_section(title, body, url)
        kind = "official" if event.get("official_source_present") else "independent"
        score = score_candidate(section, kind, event.get("reported_at"), title, url) + 2
        item = build_item(
            title=title,
            url=url,
            source=canonical_domain(url),
            published_at=event.get("reported_at"),
            section=section,
            body=body,
            kind=kind,
            score=score,
        )
        item["source_count"] = max(1, int(event.get("source_count") or 1))
        item["importance"] = max(item["importance"], 3)
        out.append(item)
    return out


def build_items_from_validation_samples() -> list[dict[str, Any]]:
    if not TECH_VALIDATION_JSON.is_file():
        return []
    payload = load_json(TECH_VALIDATION_JSON)
    out: list[dict[str, Any]] = []
    for source in payload.get("sources") or []:
        source_name = str(source.get("name") or source.get("domain") or "")
        for sample in source.get("article_samples") or []:
            if not sample.get("extract_ok"):
                continue
            if not sample.get("looks_tech"):
                continue
            if int(sample.get("content_length") or 0) < 500:
                continue
            url = str(sample.get("url") or "").strip()
            title = str(sample.get("title") or "").strip()
            if not url.startswith("http") or not title:
                continue
            section = infer_section(title, source_name, url)
            kind = source_type(source_name, url)
            score = score_candidate(section, kind, sample.get("published_at"), title, url)
            out.append(
                build_item(
                    title=title,
                    url=url,
                    source=source_name or canonical_domain(url),
                    published_at=sample.get("published_at"),
                    section=section,
                    body=source_name,
                    kind=kind,
                    score=score,
                )
            )
    return out


def dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for item in sorted(items, key=lambda row: (-int(row.get("score") or 0), row.get("title") or "")):
        url = str(item.get("url") or "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        out.append(item)
    return out


def section_items(items: list[dict[str, Any]], section: str, limit: int) -> list[dict[str, Any]]:
    filtered = [item for item in items if section in (item.get("tags") or [])]
    return filtered[:limit]


def build_executive_summary(items: list[dict[str, Any]]) -> list[str]:
    top = items[:5]
    lines = [
        f"72 gio qua noi bat nhat la {len(top)} huong can mo link doc ngay, trong do local AI, tool dung ngay va open-source chiem uu the."
    ]
    if any("local_ai_china_ai" in (item.get("tags") or []) for item in top):
        lines.append("Local AI va China AI dang la nhom co kha nang copy nhanh nhat vao stack thu nghiem cua Leon.")
    if any("automation_mcp_agents" in (item.get("tags") or []) for item in top):
        lines.append("Nhip automation, MCP va agent van la vung co nhieu workflow co the copy sang coding, content va van hanh.")
    lines.append("Radar nay uu tien link de mo doc sau, thay vi viet lai bai dai.")
    return lines


def build_must_read(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    must_read = []
    for item in items:
        if len(must_read) >= 25:
            break
        must_read.append(
            {
                "title": item["title"],
                "url": item["url"],
                "source": item["source"],
                "category": item["category"],
                "importance": item["importance"],
                "why_read": item["why_read"],
                "apply_now": item["apply_now"],
                "tags": item["tags"],
                "source_count": item["source_count"],
            }
        )
    return must_read


def build_knowledge(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    concepts = [
        ("MCP la gi va vi sao dang hot", "MCP giup model noi duoc voi cong cu va nguon du lieu co cau truc thay vi chi chat thuong.", "Nhip agent va automation dang day manh nhu cau ket noi cong cu an toan.", "Thu xem workflow nao cua Leon can mo them cong cu qua MCP."),
        ("Khi nao nen uu tien local AI", "Local AI hop khi can tiet kiem chi phi, giu du lieu noi bo va lap quy trinh thu nghiem nhanh.", "72 gio qua nhom local stack va model free dang tang mat do tin tuc va huong dan.", "Lap mot bo test nho cho Ollama, Open WebUI hoac vLLM voi use case coding va note-taking."),
        ("Open-source hot khac gi repo tang star", "Repo dang hot nen co demo, use case ro va duoc cong dong nhac den vi giai quyet viec that.", "Founder de bi ngop neu chi nhin star, trong khi repo co use case moi la thu copy duoc.", "Khi gap repo dang hot, doc README, demo va note ngay cach tich hop vao quy trinh cua Leon."),
        ("Agent workflow nen danh gia theo gi", "Nen nhin vao kha nang lap lai, do on dinh, cach go cong cu va chi phi van hanh.", "Nhip MCP, automation va coding agent dang thay doi rat nhanh.", "Moi workflow moi hay tra loi 3 cau hoi: copy duoc khong, do duoc khong, ban duoc khong."),
    ]
    best_links = [item["url"] for item in items[:6]]
    out = []
    for concept, explain, why_now, how_to_apply in concepts:
        out.append(
            {
                "concept": concept,
                "explain_simple": explain,
                "why_now": why_now,
                "best_links": best_links[:3],
                "how_to_apply": how_to_apply,
                "source_count": max(1, len(best_links[:3])),
            }
        )
    return out


def build_founder_ideas(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ideas = []
    section_map = {
        "local_ai_china_ai": "Dung mot stack local AI de test nhanh cac use case coding, research va content ma khong phu thuoc cloud.",
        "automation_mcp_agents": "Chon 1 workflow agent co the copy vao coding hoac content, roi do lai thoi gian tiet kiem duoc.",
        "open_source_hot": "Moi tuan fork 1 repo open-source dung voi bai toan thuc te cua Leon thay vi chi luu bookmark.",
        "ai_tools": "Lap bang xep hang cong cu theo tieu chi: vao viec nhanh, de ban dich vu, de dong goi thanh SaaS mini.",
        "ai_business_money": "Theo doi nhom AI business de tim mot dich vu automation co the ban duoc trong 2-4 tuan toi.",
        "industry_impact": "Dung radar nganh de chon 1 nganh dang bi AI day nhanh va nghien cuu bai toan co the ban san pham.",
        "ai_models": "So sanh 2-3 model moi theo bai toan cua Leon de khong bi cuon theo hype chung.",
    }
    picked: set[str] = set()
    for item in items:
        section = next((tag for tag in item.get("tags") or [] if tag in section_map), None)
        if not section or section in picked:
            continue
        picked.add(section)
        ideas.append(
            {
                "idea": section_map[section],
                "based_on": item["title"],
                "apply_now": item["apply_now"],
                "why_now": item["why_interesting"],
                "source_count": item["source_count"],
                "tags": [section],
            }
        )
    while len(ideas) < 10:
        area = FOUNDER_AREAS[len(ideas) % len(FOUNDER_AREAS)]
        ideas.append(
            {
                "idea": f"Tao mot sprint nho cho {area} va chi giu thu giup Leon hoc nhanh hoac kiem tien nhanh hon.",
                "based_on": "Tong hop 72h",
                "apply_now": "Mo 3 link lien quan nhat trong radar, viet note 10 dong, chon 1 thu de test trong 48 gio.",
                "why_now": "Radar hien tai cho thay co qua nhieu y hay; can rut ve thanh bai test nho de tao dong luc.",
                "source_count": 1,
                "tags": ["founder_ideas_for_leon"],
            }
        )
    return ideas[:20]


def build_publication(clean_payload: dict[str, Any], gdelt_payload: dict[str, Any]) -> dict[str, Any]:
    items = build_items_from_clean(clean_payload)
    items.extend(build_items_from_gdelt(gdelt_payload))
    items.extend(build_items_from_validation_samples())
    ranked = dedupe_items(items)[:MAX_LINKS]

    must_read = build_must_read(ranked)
    if len(must_read) < MIN_MUST_READ:
        must_read = ranked[:MIN_MUST_READ]

    sections = {
        "ai_models": section_items(ranked, "ai_models", 20),
        "local_ai_china_ai": section_items(ranked, "local_ai_china_ai", 20),
        "ai_tools": section_items(ranked, "ai_tools", 20),
        "automation_mcp_agents": section_items(ranked, "automation_mcp_agents", 20),
        "open_source_hot": section_items(ranked, "open_source_hot", 20),
        "ai_business_money": section_items(ranked, "ai_business_money", 20),
        "industry_impact": section_items(ranked, "industry_impact", 20),
        "ai_knowledge": build_knowledge(ranked),
        "founder_ideas_for_leon": build_founder_ideas(ranked),
        "full_link_radar": [
            {
                "title": item["title"],
                "url": item["url"],
                "source": item["source"],
                "published_at": item["published_at"],
                "category": item["category"],
                "why_interesting": item["why_interesting"],
                "use_case": item["use_case"],
                "source_count": item["source_count"],
                "tags": item["tags"],
            }
            for item in ranked
        ],
    }

    top_apply_now = [item["apply_now"] for item in must_read[:6]]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "window_hours": WINDOW_HOURS,
        "executive_summary": build_executive_summary(ranked),
        "must_read": must_read,
        "sections": sections,
        "stats": {
            "story_count": len(build_items_from_clean(clean_payload)),
            "gdelt_event_count": len(gdelt_payload.get("events") or []),
            "link_radar_count": len(sections["full_link_radar"]),
            "must_read_count": len(must_read),
            "local_ai_china_ai_count": len(sections["local_ai_china_ai"]),
            "open_source_hot_count": len(sections["open_source_hot"]),
            "automation_mcp_agents_count": len(sections["automation_mcp_agents"]),
            "ai_knowledge_count": len(sections["ai_knowledge"]),
            "founder_ideas_count": len(sections["founder_ideas_for_leon"]),
            "apply_now_count": len(top_apply_now),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build AI Frontier Radar 72h from tech inputs")
    parser.add_argument("--crawl-input", type=Path, default=TECH_NEWS_FOR_AI_CLEAN)
    parser.add_argument("--gdelt-input", type=Path, default=TECH_GDELT_OUTPUT)
    parser.add_argument("--output", type=Path, default=TECH_PUBLICATION_OUTPUT)
    parser.add_argument("--web-output", type=Path, default=TECH_PUBLICATION_WEB_OUTPUT)
    args = parser.parse_args()

    crawl_payload = load_json(args.crawl_input)
    gdelt_payload = load_json(args.gdelt_input) if args.gdelt_input.is_file() else {"events": []}
    publication = build_publication(crawl_payload, gdelt_payload)
    dump_json(args.output, publication)
    dump_json(args.web_output, publication)
    print(f"Wrote AI Frontier Radar 72h -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
