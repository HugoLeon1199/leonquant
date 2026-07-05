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
    TECH_GDELT_OUTPUT,
    TECH_NEWS_FOR_AI_CLEAN,
    TECH_PUBLICATION_OUTPUT,
    TECH_PUBLICATION_WEB_OUTPUT,
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
MAX_COMMUNITY_MUST_READ = 3
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


def build_candidate(
    *,
    origin: str,
    title: str,
    url: str,
    source: str,
    excerpt: str,
    published_at: Any,
    source_count: int = 1,
) -> dict[str, Any] | None:
    clean_url = str(url or "").strip()
    clean_title = trim_text(title, 220)
    if not clean_url.startswith("http") or not clean_title:
        return None
    kind = source_type(source, clean_url)
    category = infer_category(clean_title, excerpt, clean_url)
    return {
        "id": f"{origin}:{canonical_domain(clean_url)}:{abs(hash(clean_url))}",
        "origin": origin,
        "title": clean_title,
        "url": clean_url,
        "source": normalize_source(source, clean_url),
        "domain": canonical_domain(clean_url),
        "excerpt": extract_excerpt(excerpt),
        "published_at": str(published_at or "").strip(),
        "time_verified": parse_dt(published_at) is not None,
        "within_window": within_window(published_at),
        "freshness_hours": int(age_hours(published_at) or WINDOW_HOURS),
        "source_type": kind,
        "source_count": max(1, int(source_count or 1)),
        "heuristic_category": category,
        "heuristic_noise_reason": heuristic_noise_reason(clean_title, excerpt, clean_url),
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


def build_full_radar_item(candidate: dict[str, Any], curated: dict[str, Any] | None) -> dict[str, Any]:
    title = curated.get("translated_title") if curated else candidate["title"]
    why_interesting = curated.get("why_read") if curated else fallback_why_read(candidate)
    use_case = curated.get("apply_now") if curated else fallback_apply_now(candidate)
    category = curated.get("category") if curated else candidate["heuristic_category"]
    return {
        "title": trim_text(title, 220),
        "url": candidate["url"],
        "source": candidate["source"],
        "published_at": candidate["published_at"],
        "category": category,
        "why_interesting": trim_text(why_interesting, 220),
        "use_case": trim_text(use_case, 220),
        "source_type": candidate["source_type"],
        "source_count": candidate["source_count"],
        "time_verified": bool(candidate["time_verified"]),
        "tags": [CATEGORY_TO_SECTION.get(category, "ai_tools"), candidate["source_type"]],
    }


def build_main_item(candidate: dict[str, Any], curated: dict[str, Any]) -> dict[str, Any]:
    category = curated["category"]
    section = CATEGORY_TO_SECTION.get(category, "ai_tools")
    importance = curated["importance"]
    if candidate["source_type"] == "community" and importance > 3 and not is_strong_community_item(candidate, curated):
        importance = 3
    return {
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
        "score": round(candidate["preliminary_score"] + curated["relevance"] * 10 + importance * 4, 2),
    }


def pick_must_read(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    per_domain: Counter[str] = Counter()
    per_source_type: Counter[str] = Counter()
    chosen: list[dict[str, Any]] = []
    chosen_keys: set[str] = set()
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        by_category[item["category"]].append(item)

    def can_take(item: dict[str, Any]) -> bool:
        if item["url"] in chosen_keys:
            return False
        if per_domain[item["domain"]] >= MAX_DOMAIN_PER_MUST_READ:
            return False
        if item["source_type"] == "community" and per_source_type["community"] >= MAX_COMMUNITY_MUST_READ:
            return False
        return True

    for category in PRIORITY_CATEGORIES:
        for item in by_category.get(category, []):
            if can_take(item):
                chosen.append(item)
                chosen_keys.add(item["url"])
                per_domain[item["domain"]] += 1
                per_source_type[item["source_type"]] += 1
                break

    for item in items:
        if len(chosen) >= MAX_MUST_READ:
            break
        if can_take(item):
            chosen.append(item)
            chosen_keys.add(item["url"])
            per_domain[item["domain"]] += 1
            per_source_type[item["source_type"]] += 1

    return chosen[:MAX_MUST_READ]


def build_executive_summary(must_read: list[dict[str, Any]], stats: dict[str, Any]) -> list[str]:
    category_counts = Counter(item["category"] for item in must_read)
    source_counts = Counter(item["source_type"] for item in must_read)
    top_categories = ", ".join(category for category, _ in category_counts.most_common(3))
    lines = [
        f"Trong 72 giờ qua, radar giữ lại {len(must_read)} bài đáng đọc nhất từ {stats['candidate_count']} candidate live sau khi loại {stats['noise_filtered_count']} tín hiệu nhiễu.",
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


def build_publication(clean_payload: dict[str, Any], gdelt_payload: dict[str, Any]) -> dict[str, Any]:
    candidates = dedupe_candidates(
        build_candidates_from_clean(clean_payload) + build_candidates_from_gdelt(gdelt_payload)
    )
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
    for candidate in eligible_for_curator:
        curated = curated_map.get(candidate["id"])
        if not curated:
            continue
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
        curated_main_items.append(build_main_item(candidate, curated))

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

    source_type_counts = Counter(item["source_type"] for item in must_read)
    category_counts = Counter(item["category"] for item in must_read)
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
        "gemini_success_count": gemini_stats["success"],
        "gemini_fallback_count": gemini_stats["fallback"],
        "full_link_radar_count": len(full_link_radar),
        "render_checks": {
            "knowledge_fields_ready": True,
            "founder_fields_ready": True,
        },
    }

    idea_seed = must_read or curated_main_items or build_seed_items_from_candidates(full_radar_pool)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "window_hours": WINDOW_HOURS,
        "executive_summary": build_executive_summary(must_read, stats),
        "must_read": [
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
                "source_type": item["source_type"],
                "published_at": item["published_at"],
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
