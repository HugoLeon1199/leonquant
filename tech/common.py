#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

ROOT = Path(__file__).resolve().parents[1]
TECH_ROOT = Path(__file__).resolve().parent
CONFIG_DIR = TECH_ROOT / "config"
REPORTS_DIR = TECH_ROOT / "reports"
DATA_DIR = TECH_ROOT / "data"
TIERS_DIR = CONFIG_DIR / "tiers"
CATALOG = ROOT / "config" / "tech_sources_catalog.txt"
ACTIVE = CONFIG_DIR / "sources_active.txt"
DISABLED = CONFIG_DIR / "sources_disabled.txt"
TIERS_MANIFEST = CONFIG_DIR / "tiers_manifest.json"
VALIDATION_JSON = REPORTS_DIR / "source_validation.json"
VALIDATION_MD = REPORTS_DIR / "source_validation.md"
VALIDATION_DB = REPORTS_DIR / "source_validation.duckdb"
NEWS_RAW = DATA_DIR / "news_for_ai.json"
NEWS_CLEAN = DATA_DIR / "news_for_ai_clean.json"
GDELT_JSON = DATA_DIR / "gdelt_pulse.json"
PUBLICATION_JSON = DATA_DIR / "publication.json"
WINDOW_HOURS = 72
PUBLICATION_SCHEMA = "ai-frontier-radar-72h-v1"
GDELT_SCHEMA = "tech-gdelt-72h-v1"
VALIDATION_SCHEMA = "tech-source-validation-72h-v1"
PASS_STATUSES = {"PASS_RSS", "PASS_SITEMAP", "PASS_HTML", "PASS_FORUM_RSS"}
FORBIDDEN_PUBLIC_TERMS = ("gdelt", "crawler", "pipeline tech", "bigquery bytes", "gemini biên tập")

OFFICIAL_HOSTS = {
    "openai.com", "anthropic.com", "deepmind.google", "blog.google", "ai.meta.com",
    "microsoft.com", "blogs.microsoft.com", "blogs.nvidia.com", "developer.nvidia.com",
    "huggingface.co", "github.blog", "aws.amazon.com", "cloud.google.com",
    "azure.microsoft.com", "ibm.com", "databricks.com", "blog.cloudflare.com",
    "mistral.ai", "cohere.com", "stability.ai", "redhat.com", "docker.com",
}
COMMUNITY_HINTS = (
    "community.", "forum.", "forums.", "discuss.", "stackoverflow.com",
    "news.ycombinator.com", "lobste.rs", "github.com",
)
TECH_HINTS = (
    "artificial intelligence", "generative ai", "large language model", "llm",
    "machine learning", "deep learning", "openai", "anthropic", "claude", "gemini",
    "llama", "deepseek", "qwen", "mistral", "copilot", "gpu", "semiconductor",
    "chip", "data center", "cloud", "security", "robotics", "autonomous", "quantum",
    "open source", "open-source", "github", "人工智能", "人工知能", "인공지능",
)
SECTION_HINTS = {
    "model_agent_moi": ("model", "llm", "agent", "gpt", "claude", "gemini", "llama", "deepseek", "qwen"),
    "cach_dung_ai": ("workflow", "use case", "productivity", "deployment", "copilot", "automation"),
    "open_source_developer_tools": ("open source", "open-source", "github", "sdk", "framework", "developer", "docker"),
    "chip_ha_tang": ("gpu", "chip", "semiconductor", "hbm", "data center", "cloud", "server", "tsmc", "asml"),
    "robotics": ("robot", "robotics", "humanoid", "drone", "robotaxi", "autonomous"),
    "cybersecurity": ("cyber", "security", "breach", "vulnerability", "deepfake"),
    "chinh_sach_cuoc_dua_toan_cau": ("regulation", "policy", "copyright", "export control", "sanction", "ai act", "antitrust"),
    "radar_khu_vuc": ("china", "japan", "korea", "taiwan", "india", "russia", "arab", "africa", "europe", "asia"),
}


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def dump_json(path: Path, payload: Any) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def host_from_url(url: str) -> str:
    host = (urlparse(str(url or "")).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def canonical_url(url: str) -> str:
    p = urlparse(str(url or "").strip())
    if not p.scheme or not p.netloc:
        return ""
    host = p.netloc.lower().removeprefix("www.")
    path = re.sub(r"/+", "/", p.path or "/")
    if path != "/":
        path = path.rstrip("/")
    return urlunparse((p.scheme.lower(), host, path, "", p.query, ""))


def source_type(url_or_host: str) -> str:
    host = host_from_url(url_or_host) or str(url_or_host).lower().strip()
    if any(x in host for x in COMMUNITY_HINTS):
        return "community"
    if any(host == x or host.endswith("." + x) for x in OFFICIAL_HOSTS):
        return "official"
    return "independent_news"


def parse_catalog(path: Path = CATALOG) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    name = ""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            note = line.lstrip("#").strip()
            if re.match(r"^\d+\.\s+", note):
                name = re.sub(r"^\d+\.\s*", "", note).strip()
            continue
        rows.append({"name": name or host_from_url(line), "url": line, "domain": host_from_url(line), "source_type": source_type(line)})
        name = ""
    return rows


def looks_tech(text: str) -> bool:
    hay = str(text or "").lower()
    return any(x.lower() in hay for x in TECH_HINTS)


def infer_section(text: str, fallback: str = "tin_nong") -> str:
    hay = str(text or "").lower()
    for section, words in SECTION_HINTS.items():
        if any(word in hay for word in words):
            return section
    return fallback


def parse_datetime(value: Any) -> datetime | None:
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


def freshness_hours(values: list[Any], default: int = WINDOW_HOURS) -> int:
    dts = [x for x in (parse_datetime(v) for v in values) if x]
    if not dts:
        return default
    return max(0, min(default, int((datetime.now(timezone.utc) - max(dts)).total_seconds() // 3600)))


def story_id(text: str) -> str:
    return hashlib.sha1(str(text).encode("utf-8", errors="ignore")).hexdigest()[:16]


def hot_rule(types: list[str]) -> tuple[bool, int, bool, int]:
    independent = sum(1 for x in types if x == "independent_news")
    official = any(x == "official" for x in types)
    community = sum(1 for x in types if x == "community")
    return independent >= 2 or (official and independent >= 1), independent, official, community


def sanitize_public_text(text: str) -> str:
    out = re.sub(r"\s+", " ", str(text or "")).strip()
    for term in FORBIDDEN_PUBLIC_TERMS:
        out = re.sub(re.escape(term), "nguồn tin", out, flags=re.I)
    return out
