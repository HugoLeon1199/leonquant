#!/usr/bin/env python3
"""Shared helpers for the standalone tech/AI pipeline."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
REPORTS_DIR = ROOT / "reports"
TECH_TIERS_DIR = CONFIG_DIR / "tech_tiers"

TECH_CATALOG = CONFIG_DIR / "tech_sources_catalog.txt"
TECH_ACTIVE = CONFIG_DIR / "tech_sources_active.txt"
TECH_DISABLED = CONFIG_DIR / "tech_disabled_sources.txt"
TECH_TIERS_MANIFEST = CONFIG_DIR / "tech_tiers_manifest.json"
TECH_VALIDATION_JSON = REPORTS_DIR / "tech_source_validation.json"
TECH_VALIDATION_MD = REPORTS_DIR / "tech_source_validation.md"

TECH_NEWS_TODAY = ROOT / "tech_news_output_today.json"
TECH_NEWS_ALL = ROOT / "tech_news_output_all.json"
TECH_NEWS_FOR_AI = ROOT / "tech_news_for_ai.json"
TECH_NEWS_FOR_AI_CLEAN = ROOT / "tech_news_for_ai_clean.json"

TECH_GDELT_OUTPUT = ROOT / "tech_gdelt_pulse.json"
TECH_GDELT_WEB_OUTPUT = ROOT / "web" / "tech_gdelt_pulse.json"
TECH_PUBLICATION_OUTPUT = ROOT / "tech_publication.json"
TECH_PUBLICATION_WEB_OUTPUT = ROOT / "web" / "tech_publication.json"

TECH_PUBLICATION_SCHEMA = "tech-newsroom-v1"
TECH_GDELT_SCHEMA = "tech-gdelt-pulse-v1"

PASS_STATUSES = {"PASS_RSS", "PASS_SITEMAP", "PASS_HTML", "PASS_FORUM_RSS"}
RECHECK_STATUSES = {
    "SOFT_PASS",
    "BLOCKED",
    "PAYWALL",
    "CAPTCHA",
    "JS_ONLY",
    "DEAD_URL",
    "NO_ARTICLE_LINKS",
    "ARTICLE_EXTRACTION_FAILED",
    "NO_RECENT_CONTENT",
    "OFF_TOPIC",
}
ACTIVE_TIER_FILE_BY_STATUS = {
    "PASS_RSS": "01_pass_rss.txt",
    "PASS_SITEMAP": "02_pass_sitemap.txt",
    "PASS_HTML": "03_pass_html.txt",
    "PASS_FORUM_RSS": "04_pass_forum_rss.txt",
}

OFFICIAL_HOST_HINTS = {
    "openai.com",
    "anthropic.com",
    "deepmind.google",
    "blog.google",
    "ai.meta.com",
    "microsoft.com",
    "blogs.microsoft.com",
    "blogs.nvidia.com",
    "developer.nvidia.com",
    "huggingface.co",
    "github.blog",
    "aws.amazon.com",
    "cloud.google.com",
    "azure.microsoft.com",
    "ibm.com",
    "databricks.com",
    "blog.cloudflare.com",
    "mistral.ai",
    "cohere.com",
    "stability.ai",
    "riscv.org",
    "redhat.com",
    "docker.com",
    "security.googleblog.com",
    "unit42.paloaltonetworks.com",
}

TECH_TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "model_agent_moi": (
        "model",
        "llm",
        "agent",
        "gpt",
        "claude",
        "gemini",
        "llama",
        "deepseek",
        "qwen",
        "mistral",
        "reasoning",
        "multimodal",
    ),
    "cach_dung_ai": (
        "copilot",
        "workflow",
        "adoption",
        "use case",
        "productivity",
        "implementation",
        "deployment",
        "enterprise ai",
    ),
    "open_source_developer_tools": (
        "open source",
        "open-source",
        "github",
        "pytorch",
        "tensorflow",
        "docker",
        "kubernetes",
        "langchain",
        "llamaindex",
        "developer",
        "sdk",
        "framework",
    ),
    "chip_ha_tang": (
        "gpu",
        "chip",
        "semiconductor",
        "hbm",
        "datacenter",
        "data center",
        "server",
        "cloud",
        "tsmc",
        "asml",
        "nvidia",
        "amd",
        "intel",
        "broadcom",
        "arm",
        "coreweave",
    ),
    "robotics": (
        "robot",
        "robotics",
        "humanoid",
        "embodied",
        "drone",
        "autonomous",
        "robotaxi",
    ),
    "cybersecurity": (
        "cyber",
        "security",
        "ransomware",
        "breach",
        "vulnerability",
        "zero-day",
        "prompt injection",
        "deepfake",
    ),
    "chinh_sach_cuoc_dua_toan_cau": (
        "regulation",
        "policy",
        "governance",
        "copyright",
        "export control",
        "sanction",
        "ai act",
        "sovereign",
        "antitrust",
    ),
    "radar_khu_vuc": (
        "china",
        "japan",
        "korea",
        "taiwan",
        "india",
        "arabia",
        "africa",
        "russia",
        "europe",
        "asia",
    ),
}

MULTILINGUAL_TECH_HINTS = (
    "人工智能",
    "生成式",
    "大语言模型",
    "多模态",
    "芯片",
    "半导体",
    "量子",
    "网络安全",
    "人工知能",
    "生成ai",
    "半導体",
    "量子コンピュータ",
    "인공지능",
    "반도체",
    "양자",
    "искусственный интеллект",
    "полупроводник",
    "кибер",
    "الذكاء الاصطناعي",
    "أشباه الموصلات",
    "الأمن السيبراني",
)

GENERIC_TECH_HINTS = tuple(
    {
        kw
        for kws in TECH_TOPIC_KEYWORDS.values()
        for kw in kws
    }
) + MULTILINGUAL_TECH_HINTS


def parse_catalog(path: Path = TECH_CATALOG) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    pending_name = ""
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            note = line.lstrip("#").strip()
            if re.match(r"^\d+\.\s+", note):
                pending_name = re.sub(r"^\d+\.\s*", "", note).strip()
            continue
        entries.append({"name": pending_name or host_from_url(line), "url": line})
        pending_name = ""
    return entries


def host_from_url(url: str) -> str:
    host = (urlparse(str(url).strip()).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def canonical_domain(url: str) -> str:
    return host_from_url(url)


def is_official_host(url_or_host: str) -> bool:
    host = host_from_url(url_or_host) or str(url_or_host).strip().lower()
    return any(host == hint or host.endswith(f".{hint}") for hint in OFFICIAL_HOST_HINTS)


def normalize_story_key(text: str) -> str:
    lower = re.sub(r"https?://\S+", " ", str(text or "").lower())
    lower = re.sub(r"[^0-9a-z\u00c0-\u024f\u0400-\u04ff\u0600-\u06ff\u3040-\u30ff\u3400-\u9fff]+", " ", lower)
    tokens = [tok for tok in lower.split() if len(tok) > 2]
    return " ".join(tokens[:12])


def text_looks_tech(text: str) -> bool:
    hay = str(text or "").lower()
    return any(kw.lower() in hay for kw in GENERIC_TECH_HINTS)


def infer_section(text: str, *, fallback: str = "tin_nong") -> str:
    hay = str(text or "").lower()
    for section, keywords in TECH_TOPIC_KEYWORDS.items():
        if any(kw in hay for kw in keywords):
            return section
    return fallback


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def dump_json(path: Path, payload: Any) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validation_report_is_ready(path: Path = TECH_VALIDATION_JSON) -> tuple[bool, str]:
    if not path.is_file():
        return False, f"Missing validation report: {path}"
    try:
        payload = load_json(path)
    except Exception as exc:  # noqa: BLE001
        return False, f"Invalid validation report JSON: {exc}"
    meta = payload.get("validation_meta") or {}
    if not meta.get("report_valid"):
        return False, "Validation report exists but report_valid=false"
    if int(meta.get("active_source_count") or 0) <= 0:
        return False, "Validation report has no active sources"
    return True, ""

