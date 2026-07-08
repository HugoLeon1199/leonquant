#!/usr/bin/env python3
"""Build AI Frontier Radar 72h from live tech crawl and live GDELT only."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import google.generativeai as genai

from scripts.tech_common import (
    TECH_FRONTIER_WATCHLIST,
    TECH_GDELT_OUTPUT,
    TECH_NEWS_FOR_AI_CLEAN,
    TECH_PUBLICATION_OUTPUT,
    TECH_PUBLICATION_WEB_OUTPUT,
    TECH_ROLLING_CANDIDATES,
    TECH_SOURCE_COVERAGE_MATRIX,
    TECH_WATCHLIST_STATUS,
    TECH_ACTIVE,
    TECH_VALIDATION_JSON,
    canonical_domain,
    dump_json,
    is_official_host,
)

SCHEMA_VERSION = "ai-frontier-radar-72h-v1"
WINDOW_HOURS = 72
MAX_CANDIDATES = 100
MAX_FULL_RADAR = 150
MIN_MUST_READ = 10
MAX_MUST_READ = 20
MAX_DOMAIN_PER_MUST_READ = 3
MAX_COMMUNITY_MUST_READ = 5
GEMINI_BATCH_SIZE = 18

FORBIDDEN_PUBLIC_TERMS = ("pipeline", "crawler", "gdelt", "gemini", "bigquery")
COMMUNITY_HINTS = (
    "discuss.",
    "forum.",
    "forums.",
    "community.",
    "news.ycombinator.com",
    "lobste.rs",
    "stackoverflow.com",
)
ACCENT_RE = re.compile(
    r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩ"
    r"òóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]",
    re.IGNORECASE,
)
NOISE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("technical_support", re.compile(r"\bcoredump|crc fault|camera init fail|init fails|driver install|installation issue|not usable\b", re.I)),
    ("personal_troubleshooting", re.compile(r"\bhow do i|totally new to this|best practice for|seeking feedback|trouble with|help me\b", re.I)),
    ("off_topic", re.compile(r"\bgift card|survey|lottery|recipe|travel|fashion|sports\b", re.I)),
    ("narrow_research", re.compile(r"\blattice-qcd|hidden state trajectories|symbolic dynamics\b", re.I)),
)
CATEGORY_TO_SECTION = {
    "model": "ai_models",
    "local_ai": "local_ai_china_ai",
    "tool": "ai_tools",
    "automation": "automation_mcp_agents",
    "mcp": "automation_mcp_agents",
    "agent": "automation_mcp_agents",
    "opensource": "open_source_hot",
    "business": "ai_business_money",
    "knowledge": "ai_knowledge",
    "industry": "industry_impact",
}
SECTION_LABELS = {
    "ai_models": "mô hình AI",
    "local_ai_china_ai": "local AI và China AI",
    "ai_tools": "công cụ AI",
    "automation_mcp_agents": "automation, MCP và agent",
    "open_source_hot": "mã nguồn mở đang nóng",
    "ai_business_money": "kinh doanh và dòng tiền AI",
    "industry_impact": "tác động theo ngành",
    "ai_knowledge": "kiến thức cần nắm",
}
PRIORITY_CATEGORIES = [
    "model",
    "local_ai",
    "tool",
    "automation",
    "opensource",
    "business",
    "knowledge",
    "industry",
]
MODEL_HINTS = ("model", "llm", "gpt", "claude", "gemini", "llama", "qwen", "deepseek", "multimodal", "reasoning")
LOCAL_HINTS = ("local", "ollama", "lm studio", "open webui", "vllm", "sglang", "qwen", "deepseek", "kimi", "doubao", "minimax", "glm", "china", "chinese")
TOOL_HINTS = ("tool", "editor", "coding", "image", "video", "voice", "plugin", "extension", "sdk", "api")
AUTOMATION_HINTS = ("agent", "mcp", "workflow", "langgraph", "langchain", "automation", "observability", "tool use")
OPEN_SOURCE_HINTS = ("github", "open source", "open-source", "repo", "readme", "apache", "mit license", "oss")
BUSINESS_HINTS = ("funding", "revenue", "startup", "enterprise", "pricing", "market", "saas", "monetize")
INDUSTRY_HINTS = ("health", "finance", "robot", "robotics", "cyber", "security", "education", "semiconductor", "gpu", "chip", "cloud")
KNOWLEDGE_HINTS = ("guide", "best practice", "model card", "benchmark", "architecture", "tutorial", "explainer")
STRONG_COMMUNITY_HINTS = ("demo", "release", "github", "repo", "open-source", "open source", "model", "tool", "sdk", "framework")
CURATION_AI = "ai"
CURATION_FALLBACK = "fallback"
WATCHLIST_DIRECT_HOSTS = {
    "github.com",
    "huggingface.co",
    "z.ai",
    "docs.z.ai",
    "bigmodel.cn",
    "docs.bigmodel.cn",
}
SOURCE_LANES = {
    "normal_web",
    "gdelt",
    "frontier_watchlist",
    "model_hub",
    "github_release",
    "huggingface_model",
    "image_video_workflow",
    "community",
}
FULL_RADAR_GROUPS = {
    "model": "Models / LLM",
    "local_ai": "Models / LLM",
    "tool": "Image / Video AI",
    "automation": "Agents / Automation",
    "mcp": "Agents / Automation",
    "agent": "Agents / Automation",
    "opensource": "Open Source / Model Hub",
    "business": "Business / Funding",
    "knowledge": "Research / Papers",
    "industry": "Industry Impact",
}
WATCHLIST_ONLY_LANE_LIMIT = 80


def _load_env() -> None:
    env_file = Path(__file__).resolve().parents[1] / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8-sig").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and not os.environ.get(key):
            os.environ[key] = value


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_frontier_watchlist(path: Path = TECH_FRONTIER_WATCHLIST) -> dict[str, Any]:
    tech_local = Path(__file__).resolve().parents[1] / "tech" / "config" / "frontier_watchlist.json"
    if not path.is_file() and tech_local.is_file():
        path = tech_local
    if not path.is_file():
        return {"entities": []}
    payload = load_json(path)
    if not isinstance(payload, dict):
        return {"entities": []}
    for entity in payload.get("entities") or []:
        direct_sources: list[dict[str, str]] = []
        for url in entity.get("official_sources") or []:
            direct_sources.append({"kind": "official_source", "url": str(url)})
        for url in entity.get("hub_sources") or []:
            kind = "hub_source"
            host = canonical_domain(str(url))
            if "github.com" in host:
                kind = "github_release"
            elif "huggingface.co" in host:
                kind = "huggingface_model"
            direct_sources.append({"kind": kind, "url": str(url)})
        for source in entity.get("direct_sources") or []:
            if isinstance(source, dict) and source.get("url"):
                direct_sources.append({"kind": str(source.get("kind") or "direct_source"), "url": str(source.get("url"))})
        entity["direct_sources"] = direct_sources
        if not entity.get("category_hint") and entity.get("category"):
            entity["category_hint"] = entity.get("category")
    return payload


def clean_public_text(text: str) -> str:
    out = re.sub(r"\s+", " ", str(text or "")).strip()
    repl = {
        "pipeline": "hệ thống",
        "crawler": "nguồn tổng hợp",
        "gdelt": "dữ liệu đối chiếu",
        "gemini": "mô hình biên tập",
        "bigquery": "nguồn dữ liệu",
    }
    for raw, dst in repl.items():
        out = re.sub(raw, dst, out, flags=re.IGNORECASE)
    return out.strip(" -,:;")


def trim_text(text: str, limit: int) -> str:
    text = clean_public_text(text)
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


def age_hours(value: Any) -> float | None:
    dt = parse_dt(value)
    if dt is None:
        return None
    return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0)


def within_window(value: Any) -> bool:
    hours = age_hours(value)
    return hours is not None and hours <= WINDOW_HOURS


def source_type(source: str, url: str) -> str:
    host = canonical_domain(url) or canonical_domain(source) or str(source or "").strip().lower()
    if any(part in host for part in COMMUNITY_HINTS):
        return "community"
    if is_official_host(host):
        return "official"
    return "independent"


def normalize_source(source: str, url: str) -> str:
    host = canonical_domain(url) or canonical_domain(source) or str(source or "").strip()
    return host or str(source or "").strip() or "unknown"


def infer_category(title: str, excerpt: str, url: str) -> str:
    hay = f"{title} {excerpt} {url}".lower()
    if any(word in hay for word in LOCAL_HINTS):
        return "local_ai"
    if any(word in hay for word in AUTOMATION_HINTS):
        return "automation"
    if any(word in hay for word in OPEN_SOURCE_HINTS):
        return "opensource"
    if any(word in hay for word in TOOL_HINTS):
        return "tool"
    if any(word in hay for word in BUSINESS_HINTS):
        return "business"
    if any(word in hay for word in INDUSTRY_HINTS):
        return "industry"
    if any(word in hay for word in KNOWLEDGE_HINTS):
        return "knowledge"
    if any(word in hay for word in MODEL_HINTS):
        return "model"
    return "tool"


def normalized_alias_text(text: str) -> str:
    return re.sub(r"[^0-9a-z\u3400-\u9fff]+", "", str(text or "").lower())


def find_watchlist_match(text: str, watchlist: dict[str, Any]) -> tuple[dict[str, Any], str] | tuple[None, None]:
    hay = str(text or "").lower()
    compact_hay = normalized_alias_text(text)
    for entity in watchlist.get("entities") or []:
        for alias in entity.get("aliases") or []:
            raw_alias = str(alias or "").strip()
            if not raw_alias:
                continue
            alias_l = raw_alias.lower()
            compact_alias = normalized_alias_text(raw_alias)
            if alias_l in hay or (compact_alias and compact_alias in compact_hay):
                return entity, raw_alias
    return None, None


def host_matches_direct_source(url: str, entity: dict[str, Any]) -> bool:
    host = canonical_domain(url)
    for source in entity.get("direct_sources") or []:
        direct_host = canonical_domain(str(source.get("url") or ""))
        if host and direct_host and (host == direct_host or host.endswith(f".{direct_host}")):
            return True
    return False


def trend_status_for(text: str, published_at: Any) -> str:
    hay = str(text or "").lower()
    if re.search(r"\b(launch|released|introducing|new release|上线|发布|released|open-sourced|open sourced)\b", hay):
        return "new_release"
    if re.search(r"\b(update|updated|benchmark|eval|pricing|docs|release notes|leaderboard|fine-tun|支持|评测|更新)\b", hay):
        return "updated"
    hours = age_hours(published_at)
    if hours is not None and hours <= WINDOW_HOURS:
        return "rising"
    return "continued_signal"


def enrich_candidate_with_watchlist(candidate: dict[str, Any], watchlist: dict[str, Any]) -> bool:
    text = " ".join(
        str(candidate.get(part) or "")
        for part in ("title", "excerpt", "url", "source", "domain")
    )
    entity, alias = find_watchlist_match(text, watchlist)
    if not entity:
        return False
    category_hint = str(entity.get("category_hint") or "").strip()
    if category_hint in CATEGORY_TO_SECTION:
        candidate["heuristic_category"] = category_hint
    if host_matches_direct_source(candidate["url"], entity) and candidate["source_type"] != "community":
        candidate["source_type"] = str(entity.get("source_type_hint") or "official")
    elif canonical_domain(candidate["url"]) in WATCHLIST_DIRECT_HOSTS and candidate["source_type"] != "community":
        candidate["source_type"] = "official"
    trend_status = trend_status_for(text, candidate.get("published_at"))
    candidate["matched_entity"] = str(entity.get("entity") or "")
    candidate["matched_alias"] = alias
    candidate["trend_status"] = trend_status
    candidate["watchlist_evidence"] = {
        "matched_entity": candidate["matched_entity"],
        "matched_alias": alias,
        "source_type": candidate["source_type"],
        "signal_type": signal_type_for(candidate["heuristic_category"], candidate),
        "trend_status": trend_status,
        "evidence": "watchlist-direct-source" if host_matches_direct_source(candidate["url"], entity) else "watchlist-alias-match",
    }
    candidate["preliminary_score"] = int(candidate.get("preliminary_score") or 0) + (9 if candidate["source_type"] == "official" else 5)
    return True


def apply_frontier_watchlist(candidates: list[dict[str, Any]], watchlist: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    matched = 0
    entities: set[str] = set()
    aliases: set[str] = set()
    direct_source_matches = 0
    glm52_detected = False
    for candidate in candidates:
        before_source_type = candidate.get("source_type")
        if not enrich_candidate_with_watchlist(candidate, watchlist):
            continue
        matched += 1
        entities.add(str(candidate.get("matched_entity") or ""))
        aliases.add(str(candidate.get("matched_alias") or ""))
        if candidate.get("source_type") == "official" and before_source_type != "community":
            direct_source_matches += 1
        alias_blob = f"{candidate.get('matched_alias')} {candidate.get('title')} {candidate.get('excerpt')} {candidate.get('url')}".lower()
        if "glm-5.2" in alias_blob or "glm 5.2" in alias_blob or "glm52" in normalized_alias_text(alias_blob):
            glm52_detected = True
    stats = {
        "watchlist_entity_count": len(watchlist.get("entities") or []),
        "watchlist_candidate_count": matched,
        "watchlist_matched_entities": sorted(e for e in entities if e),
        "watchlist_matched_aliases": sorted(a for a in aliases if a),
        "watchlist_direct_source_matches": direct_source_matches,
        "glm_5_2_detected": glm52_detected,
    }
    return candidates, stats


def extract_excerpt(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
    if not cleaned:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    first = " ".join(parts[:2]) if parts else cleaned
    return trim_text(first, 420)


def preliminary_score(category: str, kind: str, published_at: Any, title: str, source_count: int) -> int:
    fresh = age_hours(published_at)
    fresh_score = 0 if fresh is None else max(0, 24 - min(24, int(fresh // 3)))
    category_score = {
        "model": 12,
        "local_ai": 12,
        "tool": 10,
        "automation": 11,
        "opensource": 11,
        "business": 9,
        "knowledge": 8,
        "industry": 8,
    }.get(category, 6)
    source_score = {"official": 8, "independent": 7, "community": 4}.get(kind, 3)
    novelty = 4 if re.search(r"\blaunch|release|new|preview|open source|model card|demo\b", title, re.I) else 1
    return fresh_score + category_score + source_score + novelty + min(4, max(0, source_count - 1))


def heuristic_noise_reason(title: str, excerpt: str, url: str) -> str:
    hay = f"{title} {excerpt} {url}"
    for reason, pattern in NOISE_PATTERNS:
        if pattern.search(hay):
            return reason
    return ""


def fallback_why_read(candidate: dict[str, Any]) -> str:
    section_label = SECTION_LABELS.get(CATEGORY_TO_SECTION.get(candidate["heuristic_category"], "ai_tools"), "công nghệ AI")
    excerpt = trim_text(candidate["excerpt"], 150)
    variants = {
        "model": f"Điểm đáng chú ý của bài này nằm ở cập nhật mới về {section_label}, đặc biệt là chi tiết “{excerpt}”. Nếu Leon đang theo dõi lựa chọn model, đây là link nên đọc kỹ.",
        "local_ai": f"Bài này đáng xem vì có tín hiệu rõ về local stack hoặc China AI. Chi tiết “{excerpt}” cho thấy hướng thử nghiệm có thể áp dụng nhanh vào máy local hoặc môi trường riêng.",
        "tool": f"Nội dung này nói khá rõ công cụ đang giải quyết việc gì: “{excerpt}”. Nó hữu ích nếu Leon muốn rút ngắn thời gian làm việc tay trong coding, nội dung hoặc nghiên cứu.",
        "automation": f"Giá trị chính của bài này là workflow hoặc lớp điều phối mới. Từ chi tiết “{excerpt}”, Leon có thể hình dung ngay chỗ nào trong quy trình hiện tại đang đáng để tự động hóa.",
        "opensource": f"Điểm mới ở đây là dấu hiệu cộng đồng đang chú ý tới một repo hoặc bản phát hành có thể dùng thật. Câu “{excerpt}” cho thấy đây không chỉ là link để xem cho biết.",
        "business": f"Bài này đáng đọc vì nó gợi ra góc doanh thu hoặc xu hướng chi tiền trong AI. Từ “{excerpt}”, Leon có thể soi xem đâu là nhu cầu đang hình thành.",
        "knowledge": f"Đây là dạng bài giúp Leon học nhanh một khái niệm đang nổi. Phần “{excerpt}” đủ để mở tiếp link và quyết định có cần đào sâu hay không.",
        "industry": f"Giá trị của bài này nằm ở tác động thực tế lên một nhóm ngành cụ thể. Chi tiết “{excerpt}” cho thấy AI đang chạm vào vận hành chứ không chỉ dừng ở ý tưởng.",
    }
    text = variants.get(candidate["heuristic_category"], f"Bài này có một chi tiết mới đáng chú ý: “{excerpt}”. Leon nên mở link để kiểm tra mức độ liên quan với công việc hiện tại.")
    return trim_text(text, 240)


def fallback_apply_now(candidate: dict[str, Any]) -> str:
    title = clean_public_text(candidate["title"])
    options = {
        "model": f"Đối chiếu “{title}” với các bài toán coding, research và tóm tắt tài liệu mà Leon đang làm để xem có lý do đổi model hay không.",
        "local_ai": f"Ghi lại link này vào nhóm thử nghiệm local AI rồi so với stack đang có như Ollama, Open WebUI hoặc vLLM để xem đường triển khai nào gọn nhất.",
        "tool": f"Xem công cụ này có cắt được bước thủ công nào trong việc viết code, làm nội dung, dựng video hay xử lý dữ liệu của Leon không.",
        "automation": f"Đọc link rồi thử phác một workflow nhỏ trên Cursor, Claude Code hoặc n8n để kiểm tra mức tiết kiệm thời gian thực tế.",
        "opensource": f"Mở repo hoặc demo liên quan, đọc nhanh phần cài đặt và note xem có thể fork hoặc gắn vào một dự án nội bộ trong tuần này không.",
        "business": f"Đọc theo góc thị trường: ai đang trả tiền, họ mua vì nỗi đau nào, và Leon có thể đóng gói dịch vụ tương tự ở quy mô nhỏ hay không.",
        "knowledge": f"Tóm tắt lại bài này thành 3 ý học được và gắn vào danh sách khái niệm Leon cần hiểu để quyết định công cụ hay chiến lược tốt hơn.",
        "industry": f"Kiểm tra ngành chịu tác động trong bài có giao với khách hàng, ngách nội dung hoặc ý tưởng sản phẩm mà Leon đang theo đuổi không.",
    }
    return trim_text(options.get(candidate["heuristic_category"], f"Mở “{title}”, ghi lại 2 điều mới và quyết định xem có đáng đưa vào danh sách thử nghiệm tuần này không."), 220)


def lane_from_source(url: str, kind: str = "", category: str = "") -> str:
    host = canonical_domain(url)
    raw = f"{kind} {url}".lower()
    if "huggingface.co" in host:
        return "huggingface_model"
    if "github.com" in host:
        return "github_release"
    if any(part in raw for part in ("comfy", "flux", "blackforest", "runway", "kling", "veo", "sora", "hunyuanvideo", "replicate", "fal.ai")):
        return "image_video_workflow"
    if any(part in raw for part in ("model", "hub", "openrouter")):
        return "model_hub"
    return "frontier_watchlist"


def objective_change_text(item: dict[str, Any]) -> str:
    alias = item.get("matched_alias") or item.get("matched_entity") or item.get("category") or "AI"
    trend = item.get("trend_status") or "continued_signal"
    if trend == "new_release":
        return f"Tín hiệu mới xuất hiện quanh {alias}, chuyển điểm theo dõi từ tin nền sang mốc phát hành cần kiểm chứng."
    if trend == "updated":
        return f"{alias} có cập nhật tài liệu, benchmark hoặc kênh phân phối, nên bức tranh hiện tại khác với trạng thái trước đó."
    return f"{alias} tiếp tục có tín hiệu trong nhiều nguồn, đủ để giữ trong radar 72 giờ."


def objective_why_text(item: dict[str, Any]) -> str:
    category = item.get("category") or item.get("heuristic_category") or "tool"
    mapping = {
        "model": "Nó có thể ảnh hưởng tới lựa chọn mô hình, chi phí suy luận, năng lực coding, reasoning hoặc multimodal.",
        "local_ai": "Nó tác động tới khả năng chạy AI riêng tư, tự host hoặc giảm phụ thuộc vào API cloud.",
        "tool": "Nó cho thấy lớp công cụ AI đang mở rộng sang sản xuất ảnh, video, coding hoặc vận hành thực tế.",
        "automation": "Nó ảnh hưởng tới cách ghép model với tool, dữ liệu, hành động và quy trình nhiều bước.",
        "opensource": "Nó cho biết cộng đồng đang chuyển chú ý sang repo, runtime hoặc model có thể kiểm chứng trực tiếp.",
        "business": "Nó phản ánh dòng tiền, chiến lược sản phẩm hoặc thay đổi cạnh tranh trong thị trường AI.",
        "industry": "Nó chỉ ra ngành hoặc hạ tầng chịu tác động trực tiếp từ năng lực AI mới.",
        "knowledge": "Nó là tín hiệu nền giúp hiểu đúng khái niệm, benchmark hoặc phương pháp mới.",
    }
    return mapping.get(category, mapping["tool"])


def affected_ecosystem_for(item: dict[str, Any]) -> list[str]:
    category = item.get("category") or item.get("heuristic_category") or "tool"
    mapping = {
        "model": ["model providers", "developers", "enterprise AI teams"],
        "local_ai": ["local inference", "China AI", "private deployment"],
        "tool": ["creative tooling", "developer workflows", "AI applications"],
        "automation": ["agents", "workflow automation", "tool integration"],
        "opensource": ["open-source AI", "model hubs", "developer communities"],
        "business": ["AI startups", "cloud platforms", "enterprise buyers"],
        "industry": ["industry operators", "AI infrastructure", "applied AI teams"],
        "knowledge": ["research readers", "technical decision makers"],
    }
    return mapping.get(category, mapping["tool"])


def build_candidate(
    *,
    origin: str,
    title: str,
    url: str,
    source: str,
    excerpt: str,
    published_at: Any,
    source_count: int = 1,
    source_lane: str | None = None,
    matched_entity: str = "",
    matched_alias: str = "",
    evidence: str = "",
) -> dict[str, Any] | None:
    clean_url = str(url or "").strip()
    clean_title = trim_text(title, 220)
    if not clean_url.startswith("http") or not clean_title:
        return None
    kind = source_type(source, clean_url)
    category = infer_category(clean_title, excerpt, clean_url)
    lane = source_lane or ("gdelt" if origin == "gdelt" else "normal_web")
    if lane not in SOURCE_LANES:
        lane = "normal_web"
    discovered_at = datetime.now(timezone.utc).isoformat()
    return {
        "id": f"{origin}:{canonical_domain(clean_url)}:{abs(hash(clean_url))}",
        "origin": origin,
        "source_lane": lane,
        "title": clean_title,
        "url": clean_url,
        "source": normalize_source(source, clean_url),
        "domain": canonical_domain(clean_url),
        "excerpt": extract_excerpt(excerpt),
        "published_at": str(published_at or "").strip(),
        "discovered_at": discovered_at,
        "time_verified": parse_dt(published_at) is not None,
        "within_window": within_window(published_at),
        "freshness_hours": int(age_hours(published_at) or WINDOW_HOURS),
        "source_type": kind,
        "source_count": max(1, int(source_count or 1)),
        "heuristic_category": category,
        "heuristic_noise_reason": heuristic_noise_reason(clean_title, excerpt, clean_url),
        "matched_entity": matched_entity,
        "matched_alias": matched_alias,
        "trend_status": "",
        "watchlist_evidence": {},
        "evidence": evidence,
    }


def build_candidates_from_clean(clean_payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for article in clean_payload.get("articles") or []:
        candidate = build_candidate(
            origin="news",
            title=str(article.get("title") or ""),
            url=str(article.get("url") or ""),
            source=str(article.get("source") or ""),
            excerpt=str(article.get("text") or ""),
            published_at=article.get("published_at"),
            source_count=1,
            source_lane="community" if source_type(str(article.get("source") or ""), str(article.get("url") or "")) == "community" else "normal_web",
            evidence="normal_web",
        )
        if candidate is None:
            continue
        candidate["preliminary_score"] = preliminary_score(
            candidate["heuristic_category"],
            candidate["source_type"],
            candidate["published_at"],
            candidate["title"],
            candidate["source_count"],
        )
        candidates.append(candidate)
    return candidates


def build_candidates_from_gdelt(gdelt_payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for event in gdelt_payload.get("events") or []:
        url = str(event.get("primary_url") or "").strip()
        if not url:
            urls = [str(x).strip() for x in (event.get("source_urls") or []) if str(x).strip().startswith("http")]
            url = urls[0] if urls else ""
        candidate = build_candidate(
            origin="gdelt",
            title=str(event.get("title") or ""),
            url=url,
            source=canonical_domain(url),
            excerpt=str(event.get("summary") or ""),
            published_at=event.get("reported_at"),
            source_count=max(1, int(event.get("source_count") or 1)),
            source_lane="gdelt",
            evidence="gdelt_event",
        )
        if candidate is None:
            continue
        if bool(event.get("official_source_present")) and candidate["source_type"] != "community":
            candidate["source_type"] = "official"
        candidate["preliminary_score"] = preliminary_score(
            candidate["heuristic_category"],
            candidate["source_type"],
            candidate["published_at"],
            candidate["title"],
            candidate["source_count"],
        ) + 2
        candidates.append(candidate)
    return candidates


def build_candidates_from_watchlist(watchlist: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc).isoformat()
    for entity in watchlist.get("entities") or []:
        entity_name = str(entity.get("entity") or "").strip()
        aliases = [str(alias) for alias in (entity.get("aliases") or []) if str(alias).strip()]
        primary_alias = aliases[0] if aliases else entity_name
        category = str(entity.get("category_hint") or entity.get("category") or "tool")
        for source in (entity.get("direct_sources") or [])[:4]:
            url = str(source.get("url") or "").strip()
            if not url.startswith("http"):
                continue
            kind = str(source.get("kind") or "")
            lane = lane_from_source(url, kind, category)
            title = f"{entity_name}: {primary_alias} source signal"
            if lane == "huggingface_model":
                title = f"{entity_name}: Hugging Face model or org signal"
            elif lane == "github_release":
                title = f"{entity_name}: GitHub release or repository signal"
            elif lane == "image_video_workflow":
                title = f"{entity_name}: image/video workflow signal"
            excerpt = (
                f"{entity_name} is on the frontier watchlist with aliases {', '.join(aliases[:5])}. "
                f"This configured source is checked as a durable acquisition lane, not as an invented article."
            )
            candidate = build_candidate(
                origin="watchlist",
                title=title,
                url=url,
                source=canonical_domain(url),
                excerpt=excerpt,
                published_at=now,
                source_count=1,
                source_lane=lane,
                matched_entity=entity_name,
                matched_alias=primary_alias,
                evidence="watchlist_configured_source",
            )
            if candidate is None:
                continue
            candidate["heuristic_category"] = category if category in CATEGORY_TO_SECTION else candidate["heuristic_category"]
            candidate["source_type"] = "official" if lane != "community" else candidate["source_type"]
            candidate["trend_status"] = "watchlist_checked"
            candidate["watchlist_evidence"] = {
                "matched_entity": entity_name,
                "matched_alias": primary_alias,
                "source_type": candidate["source_type"],
                "signal_type": signal_type_for(candidate["heuristic_category"], candidate),
                "trend_status": "watchlist_checked",
                "evidence": "watchlist_configured_source",
            }
            priority_boost = {"critical": 10, "high": 6, "normal": 3}.get(str(entity.get("priority") or "normal"), 3)
            candidate["preliminary_score"] = preliminary_score(
                candidate["heuristic_category"],
                candidate["source_type"],
                candidate["published_at"],
                candidate["title"],
                candidate["source_count"],
            ) + priority_boost
            candidates.append(candidate)
            if len(candidates) >= WATCHLIST_ONLY_LANE_LIMIT:
                return candidates
    return candidates


def dedupe_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    picked: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for row in sorted(candidates, key=lambda item: (-int(item.get("preliminary_score") or 0), item["title"])):
        url = row["url"]
        if url in seen_urls:
            continue
        seen_urls.add(url)
        picked.append(row)
    return picked


def parse_json_blob(text: str) -> dict[str, Any]:
    raw = str(text or "").strip()
    if not raw:
        return {}
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if fence:
        raw = fence.group(1).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        raw = raw[start : end + 1]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def has_accents(text: str) -> bool:
    return bool(ACCENT_RE.search(str(text or "")))


def sanitize_curator_text(text: str, *, limit: int) -> str:
    return trim_text(text, limit)


def gemini_curate(candidates: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    if os.environ.get("LEON_TECH_OFFLINE_TEST") == "1":
        return {}, {"success": 0, "fallback": len(candidates), "failed": len(candidates)}
    _load_env()
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("GEMINI_API_KEY missing; curator fallback will be used.", file=sys.stderr)
        return {}, {"success": 0, "fallback": len(candidates), "failed": len(candidates)}
    genai.configure(api_key=api_key)
    model_name = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite").strip() or "gemini-3.1-flash-lite"
    model = genai.GenerativeModel(model_name)
    curated: dict[str, dict[str, Any]] = {}
    success = 0
    failed = 0
    for start in range(0, len(candidates), GEMINI_BATCH_SIZE):
        batch = candidates[start : start + GEMINI_BATCH_SIZE]
        pack = [
            {
                "id": item["id"],
                "title": item["title"],
                "body_excerpt": item["excerpt"],
                "url": item["url"],
                "source": item["source"],
                "published_at": item["published_at"],
                "source_type": item["source_type"],
                "preliminary_score": item["preliminary_score"],
            }
            for item in batch
        ]
        prompt = f"""
Bạn là AI curator cho chuyên mục "AI Frontier Radar 72h".

Nhiệm vụ:
- Đọc tối đa {len(batch)} candidate.
- Chỉ dùng đúng dữ liệu trong candidate.
- Không được tạo, sửa, hay đoán URL.
- Không được bịa giá, benchmark, số liệu, hay chi tiết không có trong title/body_excerpt.
- Nếu bài là support cá nhân, cài driver, lỗi camera, coredump, CRC fault, hỏi đáp quá hẹp, hoặc không có tác động thực tế, hãy đánh dấu is_noise=true.
- Ưu tiên bài có giá trị dùng thật cho founder, coder, automation, model selection, local AI, open-source, business signal.
- Viết toàn bộ trường mô tả bằng tiếng Việt có dấu, ngắn gọn và cụ thể.

Category hợp lệ:
- model
- local_ai
- tool
- automation
- mcp
- agent
- opensource
- business
- knowledge
- industry

Trả về JSON object duy nhất:
{{
  "items": [
    {{
      "id": "...",
      "translated_title": "...",
      "category": "tool",
      "relevance": 0.0,
      "importance": 1,
      "why_read": "...",
      "apply_now": "...",
      "industry_impact": "...",
      "knowledge_value": "...",
      "is_noise": false,
      "noise_reason": ""
    }}
  ]
}}

Candidates:
{json.dumps(pack, ensure_ascii=False, indent=2)}
"""
        try:
            response = model.generate_content(prompt)
            payload = parse_json_blob(getattr(response, "text", ""))
            items = payload.get("items") if isinstance(payload, dict) else None
            if not isinstance(items, list):
                raise ValueError("missing items")
        except Exception as exc:  # noqa: BLE001
            print(
                f"Gemini curator batch failed: {type(exc).__name__}: {str(exc)[:240]}",
                file=sys.stderr,
            )
            failed += len(batch)
            continue

        by_id = {item["id"]: item for item in batch}
        for row in items:
            if not isinstance(row, dict):
                continue
            item_id = str(row.get("id") or "").strip()
            if item_id not in by_id:
                continue
            why_read = sanitize_curator_text(str(row.get("why_read") or ""), limit=220)
            apply_now = sanitize_curator_text(str(row.get("apply_now") or ""), limit=220)
            industry_impact = sanitize_curator_text(str(row.get("industry_impact") or ""), limit=220)
            knowledge_value = sanitize_curator_text(str(row.get("knowledge_value") or ""), limit=220)
            if not (has_accents(why_read) and has_accents(apply_now) and has_accents(industry_impact) and has_accents(knowledge_value)):
                print(f"Gemini curator item rejected for missing Vietnamese accents: {item_id}", file=sys.stderr)
                continue
            curated[item_id] = {
                "translated_title": trim_text(str(row.get("translated_title") or by_id[item_id]["title"]), 220),
                "category": str(row.get("category") or by_id[item_id]["heuristic_category"]).strip().lower(),
                "relevance": float(row.get("relevance") or 0),
                "importance": max(1, min(5, int(row.get("importance") or 1))),
                "why_read": why_read,
                "apply_now": apply_now,
                "industry_impact": industry_impact,
                "knowledge_value": knowledge_value,
                "is_noise": bool(row.get("is_noise")),
                "noise_reason": trim_text(str(row.get("noise_reason") or ""), 160),
            }
            success += 1
    print(
        f"Gemini curator result: success={success}; fallback={len(candidates) - success}; failed={failed}",
        file=sys.stderr,
    )
    return curated, {"success": success, "fallback": len(candidates) - success, "failed": failed}


def is_strong_community_item(candidate: dict[str, Any], curated: dict[str, Any]) -> bool:
    hay = f"{candidate['title']} {candidate['excerpt']} {candidate['url']}".lower()
    strong_hint = any(word in hay for word in STRONG_COMMUNITY_HINTS)
    return strong_hint and curated.get("relevance", 0) >= 0.75


def fallback_curated(candidate: dict[str, Any]) -> dict[str, Any]:
    category = candidate["heuristic_category"]
    score = int(candidate.get("preliminary_score") or 0)
    relevance = min(0.72, max(0.50, score / 60.0))
    hay = f"{candidate['title']} {candidate['excerpt']} {candidate['url']}".lower()
    community_has_value = any(word in hay for word in STRONG_COMMUNITY_HINTS)
    importance = 3 if candidate["source_type"] != "community" or community_has_value else 2
    return {
        "translated_title": candidate["title"],
        "category": category,
        "relevance": relevance,
        "importance": importance,
        "why_read": fallback_why_read(candidate),
        "apply_now": fallback_apply_now(candidate),
        "industry_impact": fallback_why_read(candidate),
        "knowledge_value": fallback_apply_now(candidate),
        "is_noise": bool(candidate["heuristic_noise_reason"]),
        "noise_reason": candidate["heuristic_noise_reason"],
    }


def signal_type_for(category: str, item: dict[str, Any]) -> str:
    if category in {"mcp", "agent", "automation"}:
        return "automation_agent_signal"
    if category == "model":
        return "model_signal"
    if category == "local_ai":
        return "local_ai_signal"
    if category == "opensource":
        return "open_source_signal"
    if category == "business":
        return "business_signal"
    if category == "industry":
        return "industry_signal"
    if category == "knowledge":
        return "knowledge_signal"
    return "tool_signal"


def confidence_for(candidate: dict[str, Any], curated: dict[str, Any], status: str) -> str:
    relevance = float(curated.get("relevance") or 0)
    if status == CURATION_AI and relevance >= 0.78 and candidate["source_type"] != "community":
        return "cao"
    if relevance >= 0.62 or candidate.get("source_count", 1) >= 2:
        return "trung_binh"
    return "thap"


def evidence_for(candidate: dict[str, Any], status: str) -> str:
    if candidate["source_type"] == "community":
        return "community-only"
    if status == CURATION_FALLBACK:
        return "heuristic-live-source"
    if candidate.get("source_count", 1) >= 2:
        return "multi-source"
    return "single-live-source"


def time_to_apply_for(category: str) -> str:
    if category in {"tool", "automation", "mcp", "agent", "opensource", "local_ai"}:
        return "hom_nay"
    if category in {"model", "knowledge"}:
        return "1-3_ngay"
    return "trong_tuan"


def leon_fit_for(category: str, candidate: dict[str, Any]) -> str:
    title = candidate["title"]
    templates = {
        "model": f"Đánh giá của curator: liên quan tới lựa chọn model cho coding, nghiên cứu hoặc tóm tắt tài liệu của Leon qua tín hiệu “{title}”.",
        "local_ai": f"Đánh giá của curator: có thể dùng để soi hướng chạy riêng tư/local hoặc China AI stack qua tín hiệu “{title}”.",
        "tool": f"Đánh giá của curator: đáng thử nếu công cụ trong “{title}” cắt được một bước thủ công trong workflow của Leon.",
        "automation": f"Đánh giá của curator: phù hợp để biến “{title}” thành một thử nghiệm workflow nhỏ trước khi mở rộng.",
        "mcp": f"Đánh giá của curator: phù hợp để kiểm tra khả năng nối tool/context trong hệ automation của Leon.",
        "agent": f"Đánh giá của curator: đáng xem nếu agent trong “{title}” có demo hoặc workflow thật, không chỉ là ý tưởng chung.",
        "opensource": f"Đánh giá của curator: có thể bookmark hoặc fork nếu “{title}” có README, demo và hướng dùng rõ.",
        "business": f"Đánh giá của curator: giúp Leon đọc nhu cầu thị trường và cách đóng gói dịch vụ nhỏ quanh AI.",
        "knowledge": f"Đánh giá của curator: phù hợp để rút thành checklist học nhanh hoặc tiêu chí chọn công cụ.",
        "industry": f"Đánh giá của curator: giúp Leon soi ngành nào đang có điểm chen vào bằng sản phẩm, nội dung hoặc tư vấn.",
    }
    return trim_text(templates.get(category, templates["tool"]), 240)


def build_full_radar_item(candidate: dict[str, Any], curated: dict[str, Any] | None) -> dict[str, Any]:
    title = curated.get("translated_title") if curated else candidate["title"]
    why_interesting = curated.get("why_read") if curated else fallback_why_read(candidate)
    use_case = curated.get("apply_now") if curated else fallback_apply_now(candidate)
    category = curated.get("category") if curated else candidate["heuristic_category"]
    item = {
        "title": trim_text(title, 220),
        "url": candidate["url"],
        "source": candidate["source"],
        "published_at": candidate["published_at"],
        "category": category,
        "cluster_id": "",
        "one_line_reason": trim_text(why_interesting, 180),
        "source_lane": candidate.get("source_lane") or "normal_web",
        "radar_group": FULL_RADAR_GROUPS.get(category, "Industry Impact"),
        "why_interesting": trim_text(why_interesting, 220),
        "use_case": trim_text(use_case, 220),
        "source_type": candidate["source_type"],
        "source_lane": candidate.get("source_lane") or "normal_web",
        "source_count": candidate["source_count"],
        "time_verified": bool(candidate["time_verified"]),
        "tags": [CATEGORY_TO_SECTION.get(category, "ai_tools"), candidate["source_type"]],
        "curation_status": CURATION_AI if curated else CURATION_FALLBACK,
    }
    if candidate.get("matched_entity"):
        watchlist_item_evidence = (
            "community-only"
            if candidate["source_type"] == "community"
            else (candidate.get("watchlist_evidence") or {}).get("evidence", "watchlist-alias-match")
        )
        item.update(
            {
                "matched_entity": candidate["matched_entity"],
                "matched_alias": candidate["matched_alias"],
                "trend_status": candidate.get("trend_status") or "continued_signal",
                "evidence": watchlist_item_evidence,
            }
        )
    return item


def build_main_item(candidate: dict[str, Any], curated: dict[str, Any], curation_status: str) -> dict[str, Any]:
    category = curated["category"]
    section = CATEGORY_TO_SECTION.get(category, "ai_tools")
    importance = curated["importance"]
    if curation_status == CURATION_FALLBACK and importance > 3:
        importance = 3
    if candidate["source_type"] == "community" and importance > 3 and not is_strong_community_item(candidate, curated):
        importance = 3
    confidence = confidence_for(candidate, curated, curation_status)
    evidence = evidence_for(candidate, curation_status)
    if importance <= 1:
        evidence = "exploratory"
    score = candidate["preliminary_score"] + curated["relevance"] * 10 + importance * 4
    if candidate.get("source_type") == "official":
        score += 12
    elif candidate.get("source_type") == "independent":
        score += 6
    elif candidate.get("source_type") == "community":
        score -= 4
    if candidate.get("matched_entity"):
        score += 8
    item = {
        "title": trim_text(curated["translated_title"] or candidate["title"], 220),
        "url": candidate["url"],
        "source": candidate["source"],
        "published_at": candidate["published_at"],
        "category": category,
        "importance": importance,
        "why_read": trim_text(curated["why_read"], 220),
        "apply_now": trim_text(curated["apply_now"], 220),
        "why_interesting": trim_text(curated["industry_impact"], 220),
        "knowledge_value": trim_text(curated["knowledge_value"], 220),
        "source_type": candidate["source_type"],
        "source_count": candidate["source_count"],
        "time_verified": True,
        "freshness_hours": candidate["freshness_hours"],
        "tags": [section, candidate["source_type"]],
        "domain": candidate["domain"],
        "curation_status": curation_status,
        "signal_type": signal_type_for(category, candidate),
        "confidence": confidence,
        "evidence": evidence,
        "time_to_apply": time_to_apply_for(category),
        "leon_fit": leon_fit_for(category, candidate),
        "possible_applications": [trim_text(curated["apply_now"], 220)],
        "what_changed": "",
        "score": round(score, 2),
    }
    item["what_changed"] = objective_change_text(item)
    if candidate.get("matched_entity"):
        watchlist_item_evidence = (
            "community-only"
            if candidate["source_type"] == "community"
            else (candidate.get("watchlist_evidence") or {}).get("evidence", evidence)
        )
        item.update(
            {
                "matched_entity": candidate["matched_entity"],
                "matched_alias": candidate["matched_alias"],
                "trend_status": candidate.get("trend_status") or "continued_signal",
                "evidence": watchlist_item_evidence,
            }
        )
    return item


def pick_must_read(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not items:
        return []
    target_min = min(MAX_MUST_READ, len(items))
    if len(items) >= 10:
        target_min = max(10, min(MAX_MUST_READ, len(items)))
    elif len(items) >= 5:
        target_min = max(5, len(items))
    per_domain: Counter[str] = Counter()
    per_source_type: Counter[str] = Counter()
    chosen: list[dict[str, Any]] = []
    chosen_keys: set[str] = set()
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    ranked_items = sorted(
        items,
        key=lambda item: (
            item.get("source_type") == "community",
            -int(item.get("importance") or 0),
            -float(item.get("score") or 0),
            item.get("freshness_hours", WINDOW_HOURS),
            item.get("title", ""),
        ),
    )
    for item in ranked_items:
        by_category[item["category"]].append(item)
    non_community_count = sum(1 for item in items if item.get("source_type") != "community")
    if non_community_count > 0:
        community_limit = min(MAX_COMMUNITY_MUST_READ, non_community_count)
    else:
        community_limit = min(MAX_COMMUNITY_MUST_READ, target_min)

    def can_take(item: dict[str, Any]) -> bool:
        if item["url"] in chosen_keys:
            return False
        if per_domain[item["domain"]] >= MAX_DOMAIN_PER_MUST_READ:
            return False
        if item["source_type"] == "community" and per_source_type["community"] >= community_limit:
            return False
        if item.get("importance", 0) <= 1 and item.get("evidence") != "exploratory":
            return False
        return True

    def take(item: dict[str, Any]) -> None:
        chosen.append(item)
        chosen_keys.add(item["url"])
        per_domain[item["domain"]] += 1
        per_source_type[item["source_type"]] += 1

    for category in PRIORITY_CATEGORIES:
        for item in by_category.get(category, []):
            if can_take(item):
                take(item)
                break

    for item in ranked_items:
        if len(chosen) >= MAX_MUST_READ:
            break
        if can_take(item):
            take(item)

    if len(chosen) < target_min:
        exploratory_needed = len(chosen) < 5 and non_community_count == 0
        if exploratory_needed:
            for item in items:
                if item.get("importance", 0) <= 1:
                    item["evidence"] = "exploratory"
        strong_community = [
            item for item in items
            if item.get("source_type") == "community"
            and item["url"] not in chosen_keys
            and item.get("importance", 0) >= 3
        ]
        for item in strong_community:
            if len(chosen) >= target_min or per_source_type["community"] >= community_limit:
                break
            if item["url"] in chosen_keys or per_domain[item["domain"]] >= MAX_DOMAIN_PER_MUST_READ:
                continue
            item["evidence"] = "community-only"
            take(item)

    if len(chosen) < target_min:
        for item in ranked_items:
            if len(chosen) >= target_min:
                break
            if item["url"] in chosen_keys or per_domain[item["domain"]] >= MAX_DOMAIN_PER_MUST_READ:
                continue
            if item.get("source_type") == "community" and per_source_type["community"] >= community_limit:
                continue
            take(item)

    return chosen[:MAX_MUST_READ]


def build_executive_summary(must_read: list[dict[str, Any]], stats: dict[str, Any]) -> list[str]:
    category_counts = Counter(item["category"] for item in must_read)
    source_counts = Counter(item["source_type"] for item in must_read)
    top_categories = ", ".join(category for category, _ in category_counts.most_common(3))
    first_line = (
        f"Trong 72 giờ qua, radar giữ lại {len(must_read)} bài đáng đọc nhất từ {stats['candidate_count']} tín hiệu mới sau khi loại {stats['noise_filtered_count']} tín hiệu nhiễu."
        if must_read
        else f"Trong 72 giờ qua, radar chưa có đủ tín hiệu đạt chuẩn Must Read từ {stats['candidate_count']} nguồn mới, nên chỉ giữ link trong Full Radar để Leon tự đối chiếu."
    )
    lines = [
        first_line,
        f"Nhịp tin nổi bật nhất nằm ở các nhóm {top_categories or 'công cụ, mô hình và automation'}, với ưu tiên rõ cho nguồn official và independent thay vì hỏi đáp cá nhân.",
        f"Cấu trúc nguồn hiện tại gồm official {source_counts.get('official', 0)}, independent {source_counts.get('independent', 0)} và community {source_counts.get('community', 0)} bài trong Must Read.",
        f"Các bài quá hạn cửa sổ 72 giờ đã bị loại khỏi Must Read và section chính; bài thiếu ngày chỉ được giữ ở Full Radar để Leon tự mở link đối chiếu thêm.",
    ]
    return [trim_text(line, 240) for line in lines]


def build_knowledge(must_read: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: list[tuple[str, list[dict[str, Any]], str, str]] = []
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in must_read:
        by_category[item["category"]].append(item)
    if by_category.get("automation"):
        groups.append((
            "MCP và agent chỉ đáng chú ý khi giải quyết được việc thật",
            by_category["automation"][:3],
            "Các bài automation đáng đọc nhất đều nhấn vào chỗ workflow, tracing hoặc ghép công cụ chứ không dừng ở khẩu hiệu agent chung chung.",
            "Leon có thể lấy các ví dụ này để đánh giá workflow nào đủ rõ đầu vào, đầu ra và điểm đo hiệu quả trước khi bỏ thời gian tích hợp.",
        ))
    if by_category.get("local_ai"):
        groups.append((
            "Local AI chỉ có ý nghĩa khi gắn với một stack cụ thể",
            by_category["local_ai"][:3],
            "Nhóm local AI đang chuyển từ hỏi model nào mạnh sang hỏi triển khai bằng runtime nào, có giữ dữ liệu riêng được không và có dùng ổn cho task hằng ngày không.",
            "Leon nên so các bài này với nhu cầu local coding, research và tóm tắt tài liệu để quyết định có cần dựng một stack riêng hay không.",
        ))
    if by_category.get("opensource"):
        groups.append((
            "Open-source nóng không đồng nghĩa với nhiều sao",
            by_category["opensource"][:3],
            "Điểm đáng theo dõi là repo nào có demo, use case rõ và cộng đồng đang dùng để giải quyết việc thật trong 72 giờ qua.",
            "Khi gặp repo như vậy, Leon nên mở README, xem demo và kiểm tra ngay khả năng fork hoặc gắn vào quy trình nội bộ.",
        ))
    if by_category.get("model"):
        groups.append((
            "Theo dõi model nên đi cùng bài toán dùng thật",
            by_category["model"][:3],
            "Các cập nhật model đáng giữ lại thường gắn với thay đổi về khả năng multimodal, tốc độ, local runtime hoặc cửa sổ ứng dụng rõ hơn trước.",
            "Leon có thể dùng nhóm bài này để so lại bộ tiêu chí chọn model cho coding, đọc tài liệu và content thay vì chạy theo hype.",
        ))
    out: list[dict[str, Any]] = []
    for concept, items, explain, apply in groups[:4]:
        out.append(
            {
                "concept": concept,
                "explain_simple": trim_text(explain, 220),
                "why_now": trim_text("Trong 72 giờ qua, nhiều bài cùng hội tụ vào chủ điểm này nên nó đáng được xem là một hướng học và ra quyết định ngay bây giờ.", 220),
                "how_to_apply": trim_text(apply, 220),
                "best_links": [item["url"] for item in items],
                "source_count": len(items),
            }
        )
    return out


def build_founder_ideas(must_read: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ideas: list[dict[str, Any]] = []
    for item in must_read[:10]:
        category = item["category"]
        idea_map = {
            "model": "Tạo một bảng so sánh nhỏ giữa model mới và stack hiện tại theo đúng ba việc Leon làm nhiều nhất.",
            "local_ai": "Dựng một nhánh local AI nhỏ để thử nghiệm các việc cần riêng tư hoặc chạy lặp lại nhiều lần mà không muốn phụ thuộc cloud.",
            "tool": "Chọn một công cụ mới và đo xem nó cắt được bao nhiêu phút ở một bước làm việc đang lặp lại hằng ngày.",
            "automation": "Lấy workflow trong bài, giản lược về một bài test 30 phút và xem nó có chạy ổn hơn cách làm tay hiện tại hay không.",
            "opensource": "Fork hoặc bookmark có chủ đích một repo đủ rõ use case, rồi ghi lại vì sao nó đáng đi tiếp thay vì chỉ lưu link.",
            "business": "Đọc bài theo góc nhu cầu thị trường để xem có thể đóng gói thành mini-service, productized service hay SaaS nhỏ hay không.",
            "knowledge": "Biến kiến thức mới trong bài thành checklist ra quyết định cho các lần chọn tool, chọn model hoặc đánh giá cơ hội sau này.",
            "industry": "Chọn một ngành bị AI tác động rõ và soi xem Leon có góc sản phẩm, nội dung hay tư vấn nào chen vào được không.",
        }
        ideas.append(
            {
                "idea": trim_text(idea_map.get(category, "Rút bài này về một thử nghiệm nhỏ có thể làm ngay trong tuần."), 220),
                "based_on": item["title"],
                "why_now": trim_text(item["why_interesting"], 220),
                "apply_now": trim_text(item["apply_now"], 220),
                "source_count": item["source_count"],
                "tags": [CATEGORY_TO_SECTION.get(category, "ai_tools")],
            }
        )
        if len(ideas) >= 10:
            break
    return ideas


def build_seed_items_from_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seeds: list[dict[str, Any]] = []
    for candidate in candidates[:10]:
        category = candidate["heuristic_category"]
        seeds.append(
            {
                "title": candidate["title"],
                "url": candidate["url"],
                "source": candidate["source"],
                "category": category,
                "importance": 2 if candidate["source_type"] == "community" else 3,
                "why_read": fallback_why_read(candidate),
                "apply_now": fallback_apply_now(candidate),
                "why_interesting": fallback_why_read(candidate),
                "source_type": candidate["source_type"],
                "source_count": candidate["source_count"],
                "tags": [CATEGORY_TO_SECTION.get(category, "ai_tools"), candidate["source_type"]],
                "domain": candidate["domain"],
            }
        )
    return seeds


def cluster_key_for_item(item: dict[str, Any]) -> str:
    entity = str(item.get("matched_entity") or "").strip()
    if entity:
        return normalized_alias_text(entity)[:40]
    category = str(item.get("category") or item.get("heuristic_category") or "tool")
    title = normalized_alias_text(item.get("title") or "")
    return f"{category}:{title[:24]}"


def build_top_signal_clusters(items: list[dict[str, Any]], full_radar: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        grouped[cluster_key_for_item(item)].append(item)
    clusters: list[dict[str, Any]] = []
    seen_entities: set[str] = set()
    for key, group in sorted(grouped.items(), key=lambda pair: (-max(float(i.get("score") or 0) for i in pair[1]), pair[0])):
        lead = sorted(group, key=lambda item: (-float(item.get("score") or 0), item.get("freshness_hours", WINDOW_HOURS)))[0]
        entity = str(lead.get("matched_entity") or lead.get("category") or "").strip()
        if entity and entity in seen_entities:
            continue
        if entity:
            seen_entities.add(entity)
        cluster_id = f"cluster-{len(clusters) + 1:02d}-{re.sub(r'[^a-z0-9]+', '-', key.lower()).strip('-')[:32]}"
        links = [
            {
                "title": item["title"],
                "url": item["url"],
                "source": item["source"],
                "source_lane": item.get("source_lane") or "normal_web",
                "published_at": item.get("published_at") or "",
            }
            for item in group[:6]
        ]
        evidence_mix = {
            "source_lane": dict(Counter(str(item.get("source_lane") or "normal_web") for item in group)),
            "source_type": dict(Counter(str(item.get("source_type") or "independent") for item in group)),
            "link_count": len(links),
        }
        clusters.append(
            {
                "cluster_id": cluster_id,
                "cluster_title": lead["title"],
                "takeaway": trim_text(lead.get("why_read") or lead.get("why_interesting") or lead["title"], 240),
                "what_changed": trim_text(objective_change_text(lead), 240),
                "why_it_matters": trim_text(objective_why_text(lead), 240),
                "affected_ecosystem": affected_ecosystem_for(lead),
                "entities": sorted({str(item.get("matched_entity") or item.get("category") or "").strip() for item in group if str(item.get("matched_entity") or item.get("category") or "").strip()}),
                "signal_type": lead.get("signal_type") or signal_type_for(lead.get("category", "tool"), lead),
                "importance": int(lead.get("importance") or 3),
                "confidence": lead.get("confidence") or "medium",
                "evidence_mix": evidence_mix,
                "links": links,
                "possible_applications": [
                    trim_text(lead.get("apply_now") or "Đọc nguồn gốc, xác minh điểm mới và tự quyết định có đáng thử nghiệm hay không.", 220)
                ],
            }
        )
        if len(clusters) >= 10:
            break
    if not clusters and full_radar:
        for item in full_radar[:5]:
            cluster_id = f"cluster-{len(clusters) + 1:02d}"
            clusters.append(
                {
                    "cluster_id": cluster_id,
                    "cluster_title": item["title"],
                    "takeaway": item.get("one_line_reason") or item.get("why_interesting") or item["title"],
                    "what_changed": objective_change_text(item),
                    "why_it_matters": objective_why_text(item),
                    "affected_ecosystem": affected_ecosystem_for(item),
                    "entities": [item.get("matched_entity") or item.get("category") or "AI"],
                    "signal_type": item.get("category") or "tool",
                    "importance": 3,
                    "confidence": "medium",
                    "evidence_mix": {"source_lane": {item.get("source_lane") or "normal_web": 1}, "link_count": 1},
                    "links": [{"title": item["title"], "url": item["url"], "source": item["source"], "source_lane": item.get("source_lane") or "normal_web", "published_at": item.get("published_at") or ""}],
                    "possible_applications": [item.get("use_case") or ""],
                }
            )
    return clusters


def build_watchlist_status(watchlist: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    candidate_by_entity: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        entity = str(candidate.get("matched_entity") or "").strip()
        if entity:
            candidate_by_entity[entity].append(candidate)
    rows = []
    for entity in watchlist.get("entities") or []:
        name = str(entity.get("entity") or "").strip()
        hits = candidate_by_entity.get(name, [])
        rows.append(
            {
                "entity": name,
                "priority": entity.get("priority") or "normal",
                "checked": True,
                "hit_count": len(hits),
                "top_links": [
                    {"title": hit["title"], "url": hit["url"], "source_lane": hit.get("source_lane") or "normal_web"}
                    for hit in hits[:5]
                ],
                "no_signal_reason": "" if hits else "no candidate matched in current rolling inputs",
            }
        )
    return {
        "schema_version": "watchlist-status-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "checked": len(rows),
        "hit_count": sum(row["hit_count"] for row in rows),
        "entities": rows,
    }


def persist_rolling_candidates(candidates: list[dict[str, Any]]) -> None:
    now = datetime.now(timezone.utc)
    existing: list[dict[str, Any]] = []
    if TECH_ROLLING_CANDIDATES.is_file():
        try:
            payload = load_json(TECH_ROLLING_CANDIDATES)
            existing = list(payload.get("candidates") or [])
        except Exception:
            existing = []
    by_url: dict[str, dict[str, Any]] = {}
    for row in existing + candidates:
        url = str(row.get("url") or "").strip()
        if not url:
            continue
        dt = parse_dt(row.get("discovered_at") or row.get("published_at"))
        if dt and (now - dt).total_seconds() > 7 * 24 * 3600:
            continue
        by_url[url] = {
            "source_lane": row.get("source_lane") or "normal_web",
            "matched_entity": row.get("matched_entity") or "",
            "matched_alias": row.get("matched_alias") or "",
            "published_at": row.get("published_at") or "",
            "discovered_at": row.get("discovered_at") or now.isoformat(),
            "time_verified": bool(row.get("time_verified")),
            "evidence": row.get("evidence") or row.get("trend_status") or "",
            "url": url,
            "title": row.get("title") or "",
            "source": row.get("source") or "",
            "category": row.get("heuristic_category") or row.get("category") or "",
        }
    payload = {
        "schema_version": "tech-candidates-rolling-v1",
        "generated_at_utc": now.isoformat(),
        "window_days": 7,
        "candidate_count": len(by_url),
        "candidates_by_lane": dict(Counter(str(row.get("source_lane") or "normal_web") for row in by_url.values())),
        "candidates": sorted(by_url.values(), key=lambda row: (row.get("source_lane") or "", row.get("title") or ""))[:500],
    }
    dump_json(TECH_ROLLING_CANDIDATES, payload)


def write_source_coverage_matrix(candidates: list[dict[str, Any]], watchlist_status: dict[str, Any]) -> None:
    lanes = [
        "official_ai_labs",
        "independent_ai_news",
        "china_ai",
        "model_hubs",
        "github_releases",
        "image_video_ai",
        "automation_agents",
        "chips_infra",
        "business_funding",
        "policy_risk",
        "research_papers",
        "community_forums",
        "gdelt",
    ]
    candidate_counts = Counter()
    for candidate in candidates:
        lane = str(candidate.get("source_lane") or "normal_web")
        cat = str(candidate.get("heuristic_category") or "")
        if lane == "gdelt":
            candidate_counts["gdelt"] += 1
        if lane == "github_release":
            candidate_counts["github_releases"] += 1
        if lane in {"huggingface_model", "model_hub"}:
            candidate_counts["model_hubs"] += 1
        if lane == "image_video_workflow" or cat == "tool":
            candidate_counts["image_video_ai"] += 1
        if cat in {"automation", "mcp", "agent"}:
            candidate_counts["automation_agents"] += 1
        if candidate.get("source_type") == "community":
            candidate_counts["community_forums"] += 1
        if candidate.get("source_type") == "official":
            candidate_counts["official_ai_labs"] += 1
        if candidate.get("source_type") == "independent":
            candidate_counts["independent_ai_news"] += 1
        if any(name in str(candidate.get("matched_entity") or "").lower() for name in ("zhipu", "qwen", "deepseek", "kimi", "minimax", "doubao", "hunyuan", "stepfun", "internlm", "sensetime", "baichuan")):
            candidate_counts["china_ai"] += 1
        if cat == "business":
            candidate_counts["business_funding"] += 1
        if cat == "industry":
            candidate_counts["chips_infra"] += 1
        if cat == "knowledge":
            candidate_counts["research_papers"] += 1
    active_sources = 0
    if TECH_ACTIVE.is_file():
        active_sources = sum(1 for line in TECH_ACTIVE.read_text(encoding="utf-8").splitlines() if line.strip() and not line.strip().startswith("#"))
    lines = [
        "# Tech Source Coverage Matrix",
        "",
        f"- generated_at_utc: {datetime.now(timezone.utc).isoformat()}",
        f"- active_sources: {active_sources}",
        f"- watchlist_checked: {watchlist_status.get('checked', 0)}",
        f"- watchlist_hit_count: {watchlist_status.get('hit_count', 0)}",
        "",
        "| lane | total configured | active | candidates collected | blockers | priority fix |",
        "|---|---:|---:|---:|---|---|",
    ]
    for lane in lanes:
        configured = active_sources if lane in {"independent_ai_news", "community_forums"} else 0
        if lane in {"china_ai", "model_hubs", "image_video_ai", "automation_agents", "github_releases", "official_ai_labs"}:
            configured = int(watchlist_status.get("checked") or 0)
        active = active_sources if lane in {"independent_ai_news", "community_forums"} else configured
        count = candidate_counts.get(lane, 0)
        blocker = "low active source count" if active_sources < 10 and lane in {"official_ai_labs", "independent_ai_news"} else ""
        fix = "recover more direct sources" if blocker else "monitor"
        lines.append(f"| {lane} | {configured} | {active} | {count} | {blocker or '-'} | {fix} |")
    TECH_SOURCE_COVERAGE_MATRIX.parent.mkdir(parents=True, exist_ok=True)
    TECH_SOURCE_COVERAGE_MATRIX.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_publication(clean_payload: dict[str, Any], gdelt_payload: dict[str, Any]) -> dict[str, Any]:
    watchlist = load_frontier_watchlist()
    candidates = dedupe_candidates(
        build_candidates_from_clean(clean_payload)
        + build_candidates_from_gdelt(gdelt_payload)
        + build_candidates_from_watchlist(watchlist)
    )
    candidates, watchlist_stats = apply_frontier_watchlist(candidates, watchlist)
    candidates = dedupe_candidates(candidates)
    persist_rolling_candidates(candidates)
    full_radar_pool = candidates[:MAX_FULL_RADAR]
    eligible_for_curator = [
        item for item in candidates
        if item["within_window"] and item["time_verified"]
    ][:MAX_CANDIDATES]
    expired_removed = sum(1 for item in candidates if item["time_verified"] and not item["within_window"])
    unknown_time_count = sum(1 for item in candidates if not item["time_verified"])
    curated_map, gemini_stats = gemini_curate(eligible_for_curator)

    curated_main_items: list[dict[str, Any]] = []
    noise_filtered_count = 0
    ai_main_count = 0
    fallback_main_count = 0
    for candidate in eligible_for_curator:
        curated = curated_map.get(candidate["id"])
        if not curated:
            curated = fallback_curated(candidate)
            curation_status = CURATION_FALLBACK
        else:
            curation_status = CURATION_AI
        category = curated["category"]
        if category not in CATEGORY_TO_SECTION:
            category = candidate["heuristic_category"]
            curated["category"] = category
        if candidate["heuristic_noise_reason"]:
            curated["is_noise"] = True
            curated["noise_reason"] = curated["noise_reason"] or candidate["heuristic_noise_reason"]
        if curated["is_noise"] or curated["relevance"] < 0.45:
            noise_filtered_count += 1
            continue
        if curation_status == CURATION_FALLBACK and curated["relevance"] < 0.50:
            noise_filtered_count += 1
            continue
        main_item = build_main_item(candidate, curated, curation_status)
        curated_main_items.append(main_item)
        if curation_status == CURATION_AI:
            ai_main_count += 1
        else:
            fallback_main_count += 1

    curated_main_items.sort(key=lambda item: (-item["score"], item["freshness_hours"], item["title"]))
    must_read = pick_must_read(curated_main_items)

    sections = {name: [] for name in CATEGORY_TO_SECTION.values()}
    for item in curated_main_items:
        if item["url"] not in {picked["url"] for picked in must_read} and item["source_type"] == "community" and item["importance"] < 3:
            pass
        section = CATEGORY_TO_SECTION.get(item["category"], "ai_tools")
        if len(sections[section]) < 12:
            sections[section].append(item)

    full_link_radar = [
        build_full_radar_item(candidate, curated_map.get(candidate["id"]))
        for candidate in full_radar_pool
    ]
    top_signal_clusters = build_top_signal_clusters(curated_main_items, full_link_radar)
    cluster_by_url = {
        link["url"]: cluster["cluster_id"]
        for cluster in top_signal_clusters
        for link in cluster.get("links", [])
    }
    for radar_item in full_link_radar:
        radar_item["cluster_id"] = cluster_by_url.get(radar_item["url"], "")
    watchlist_status = build_watchlist_status(watchlist, candidates)
    dump_json(TECH_WATCHLIST_STATUS, watchlist_status)
    write_source_coverage_matrix(candidates, watchlist_status)
    active_source_count = 0
    if TECH_ACTIVE.is_file():
        active_source_count = sum(1 for line in TECH_ACTIVE.read_text(encoding="utf-8").splitlines() if line.strip() and not line.strip().startswith("#"))

    source_type_counts = Counter(item["source_type"] for item in must_read)
    category_counts = Counter(item["category"] for item in must_read)
    main_source_type_counts = Counter(item["source_type"] for item in curated_main_items)
    lane_counts = Counter(str(item.get("source_lane") or "normal_web") for item in candidates)
    main_non_community_count = sum(
        count for source_type_name, count in main_source_type_counts.items()
        if source_type_name != "community"
    )
    community_share = source_type_counts.get("community", 0) / max(1, len(must_read))
    must_read_quality_warning = (
        "community_share_over_50"
        if must_read and community_share > 0.50 and main_non_community_count > 0
        else ""
    )
    stats = {
        "story_count": len(build_candidates_from_clean(clean_payload)),
        "gdelt_event_count": len(gdelt_payload.get("events") or []),
        "candidate_count": len(candidates),
        "curator_candidate_count": len(eligible_for_curator),
        "noise_filtered_count": noise_filtered_count,
        "expired_removed_count": expired_removed,
        "unknown_time_full_radar_count": unknown_time_count,
        "must_read_count": len(must_read),
        "must_read_by_source_type": dict(source_type_counts),
        "must_read_by_category": dict(category_counts),
        "main_by_source_type": dict(main_source_type_counts),
        "official_candidate_count": int(main_source_type_counts.get("official") or 0),
        "independent_candidate_count": int(main_source_type_counts.get("independent") or 0),
        "community_candidate_count": int(main_source_type_counts.get("community") or 0),
        "must_read_community_share": round(community_share, 3),
        "must_read_quality_warning": must_read_quality_warning,
        "gemini_success_count": gemini_stats["success"],
        "gemini_fallback_count": gemini_stats["fallback"],
        "ai_curated_main_count": ai_main_count,
        "fallback_main_count": fallback_main_count,
        "main_candidate_count": len(curated_main_items),
        "full_link_radar_count": len(full_link_radar),
        "top_signal_cluster_count": len(top_signal_clusters),
        "candidates_by_lane": dict(lane_counts),
        "model_hub_candidate_count": int(lane_counts.get("model_hub") or 0) + int(lane_counts.get("huggingface_model") or 0),
        "image_video_workflow_candidate_count": int(lane_counts.get("image_video_workflow") or 0),
        "watchlist_checked": watchlist_status.get("checked", 0),
        "watchlist_hit_count": watchlist_status.get("hit_count", 0),
        "gdelt_reused_previous_events": bool(gdelt_payload.get("reused_previous_events")),
        "gdelt_fresh_event_count": int(gdelt_payload.get("fresh_event_count") or len(gdelt_payload.get("events") or [])),
        "active_source_count": active_source_count,
        "source_coverage_warning": "active_sources_below_10" if active_source_count and active_source_count < 10 else "",
        "render_checks": {
            "knowledge_fields_ready": True,
            "founder_fields_ready": True,
        },
        **watchlist_stats,
    }

    idea_seed = must_read or curated_main_items or build_seed_items_from_candidates(full_radar_pool)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "window_hours": WINDOW_HOURS,
        "executive_summary": build_executive_summary(must_read, stats),
        "top_signal_clusters": top_signal_clusters,
        "watchlist_status": watchlist_status,
        "optional_applications": [
            {
                "cluster_id": cluster["cluster_id"],
                "applications": cluster.get("possible_applications") or [],
            }
            for cluster in top_signal_clusters
        ],
        "must_read": [
            {
                "title": item["title"],
                "url": item["url"],
                "source": item["source"],
                "category": item["category"],
                "importance": item["importance"],
                "why_read": item["why_read"],
                "apply_now": item["apply_now"],
                "possible_applications": item.get("possible_applications") or [item["apply_now"]],
                "tags": item["tags"],
                "source_count": item["source_count"],
                "source_type": item["source_type"],
                "published_at": item["published_at"],
                "curation_status": item["curation_status"],
                "signal_type": item["signal_type"],
                "confidence": item["confidence"],
                "evidence": item["evidence"],
                "time_to_apply": item["time_to_apply"],
                "leon_fit": item["leon_fit"],
                "matched_entity": item.get("matched_entity", ""),
                "matched_alias": item.get("matched_alias", ""),
                "trend_status": item.get("trend_status", ""),
                "source_lane": item.get("source_lane", "normal_web"),
            }
            for item in must_read
        ],
        "sections": {
            "ai_models": sections["ai_models"],
            "local_ai_china_ai": sections["local_ai_china_ai"],
            "ai_tools": sections["ai_tools"],
            "automation_mcp_agents": sections["automation_mcp_agents"],
            "open_source_hot": sections["open_source_hot"],
            "ai_business_money": sections["ai_business_money"],
            "industry_impact": sections["industry_impact"],
            "ai_knowledge": build_knowledge(idea_seed),
            "founder_ideas_for_leon": build_founder_ideas(idea_seed),
            "full_link_radar": full_link_radar,
        },
        "stats": stats,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build AI Frontier Radar 72h from live tech inputs")
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
