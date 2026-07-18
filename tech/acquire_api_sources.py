#!/usr/bin/env python3
"""Acquire API-first tech radar candidates from HF, GitHub, arXiv and JSON APIs."""

from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("LEON_TECH_BASE_DIR", str(ROOT / "tech"))

from scripts.tech_common import (  # noqa: E402
    TECH_ACTIVE,
    TECH_API_CANDIDATES,
    TECH_FRONTIER_WATCHLIST,
    TECH_SOURCE_REGISTRY,
    TECH_SOURCE_PROFILES,
    TECH_VALIDATION_JSON,
    canonical_domain,
    dump_json,
    load_json,
)

HF_SEARCH_ALIASES = [
    "GLM",
    "Zhipu",
    "zai-org",
    "Qwen",
    "DeepSeek",
    "Kimi",
    "MiniMax",
    "Hunyuan",
    "Flux",
    "Black Forest Labs",
    "ComfyUI",
    "Runway",
    "video generation",
    "text-to-image",
]
GITHUB_REPOS = [
    "huggingface/transformers",
    "huggingface/diffusers",
    "pytorch/pytorch",
    "ggml-org/llama.cpp",
    "ollama/ollama",
    "comfyanonymous/ComfyUI",
    "langchain-ai/langgraph",
    "run-llama/llama_index",
    "All-Hands-AI/OpenHands",
    "vllm-project/vllm",
    "sgl-project/sglang",
]
GITHUB_ORGS = [
    "QwenLM",
    "deepseek-ai",
    "zai-org",
    "Tencent-Hunyuan",
    "InternLM",
    "modelcontextprotocol",
]
ARXIV_CATEGORIES = ("cs.AI", "cs.CL", "cs.LG", "cs.CV", "cs.RO")
ARXIV_TOPIC_QUERY = '(LLM OR agent OR multimodal OR diffusion OR "video generation" OR "text-to-image" OR MCP OR "reasoning model")'
API_METHODS = {"api", "github_api", "hf_api", "arxiv_api", "gdelt"}
PROFILE_FETCH_METHODS = {"rss", "atom", "sitemap", "json_ld", "changelog_snapshot", "metadata"}
CRITICAL_ENTITIES = {
    "OpenAI",
    "Anthropic",
    "Google AI",
    "Google DeepMind",
    "Gemini developer updates",
    "Meta AI/Llama",
    "Mistral",
    "Microsoft Research",
    "Azure AI",
    "AWS ML/Bedrock",
    "Apple ML",
    "NVIDIA",
    "AMD",
    "Intel",
    "Arm",
    "NIST AI",
    "EU AI Office",
    "CISA",
}
WEAK_MATCH_EVIDENCE = "weak_metadata_match"
NOISY_REPO_RE = re.compile(r"(?:^|[-_/])(test|demo-test|random|myawesomemodel)(?:$|[-_/])|uncensored|abliterated", re.I)
PERSONAL_FINETUNE_RE = re.compile(r"\b(finetune|fine-tune|lora|adapter|merge|merged|gguf|quantized|quantization|rp|roleplay)\b", re.I)
OFFICIAL_ENTITY_ORGS = {
    "Zhipu/Z.ai": {"zai-org", "zhipuai", "bigmodel"},
    "Qwen/Alibaba": {"qwen", "qwenlm", "alibaba", "alibaba-pai"},
    "Kimi/Moonshot": {"moonshotai", "moonshot-ai", "kimi"},
    "MiniMax": {"minimax-ai", "minimaxir", "minimax"},
    "DeepSeek": {"deepseek-ai", "deepseek"},
    "Doubao/ByteDance": {"bytedance", "doubao-seed", "volcengine"},
    "Hunyuan/Tencent": {"tencent-hunyuan", "tencent", "hunyuan"},
    "StepFun": {"stepfun-ai", "stepfun"},
    "InternLM": {"internlm"},
    "SenseTime": {"sensetime", "senseauto"},
    "Baichuan": {"baichuan-inc", "baichuan"},
    "Flux/Black Forest Labs": {"black-forest-labs"},
    "ComfyUI": {"comfyanonymous", "comfy-org"},
    "LangGraph": {"langchain-ai"},
    "LlamaIndex": {"run-llama"},
    "OpenHands": {"all-hands-ai"},
    "MCP": {"modelcontextprotocol"},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_dt(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return raw
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def trim(text: Any, limit: int = 600) -> str:
    out = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(out) <= limit:
        return out
    return out[:limit].rsplit(" ", 1)[0].strip()


def load_profiles(path: Path = TECH_SOURCE_PROFILES) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    payload = load_json(path)
    return [row for row in payload.get("sources") or [] if isinstance(row, dict)]


def load_watchlist_aliases(path: Path = TECH_FRONTIER_WATCHLIST) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    payload = load_json(path)
    rows: list[dict[str, str]] = []
    for entity in payload.get("entities") or []:
        name = str(entity.get("entity") or "")
        for alias in entity.get("aliases") or []:
            raw = str(alias or "").strip()
            if raw:
                rows.append({"entity": name, "alias": raw})
    return rows


def match_entity_alias(text: str, aliases: list[dict[str, str]]) -> tuple[str, str]:
    hay = str(text or "").lower()
    for row in aliases:
        alias = row["alias"]
        if alias.lower() in hay:
            return row["entity"], alias
    return "", ""


def repo_namespace(repo_id: str) -> str:
    return str(repo_id or "").split("/", 1)[0].strip().lower()


def is_official_entity_namespace(entity: str, repo_id: str) -> bool:
    namespace = repo_namespace(repo_id)
    if not namespace:
        return False
    official = OFFICIAL_ENTITY_ORGS.get(entity, set())
    return namespace in {org.lower() for org in official}


def is_test_repo_name(name: str) -> bool:
    return bool(NOISY_REPO_RE.search(str(name or "").lower()))


def is_personal_finetune_name(name: str, tags: list[Any] | None = None) -> bool:
    blob = " ".join([str(name or ""), *[str(tag) for tag in (tags or [])]])
    return bool(PERSONAL_FINETUNE_RE.search(blob.lower()))


def match_with_strength(
    *,
    strong_text: str,
    weak_text: str,
    repo_id: str,
    aliases: list[dict[str, str]],
) -> tuple[str, str, str, bool, str]:
    entity, alias = match_entity_alias(strong_text, aliases)
    if entity:
        return entity, alias, "strong", is_official_entity_namespace(entity, repo_id), ""
    weak_entity, weak_alias = match_entity_alias(weak_text, aliases)
    if weak_entity and is_official_entity_namespace(weak_entity, repo_id):
        return weak_entity, weak_alias, "medium", True, ""
    if weak_entity:
        return weak_entity, weak_alias, "weak", False, WEAK_MATCH_EVIDENCE
    for row in aliases:
        entity_name = row["entity"]
        if is_official_entity_namespace(entity_name, repo_id):
            return entity_name, row["alias"], "medium", True, ""
    return "", "", "medium", False, ""


def candidate(
    *,
    title: str,
    url: str,
    source: str,
    source_lane: str,
    summary: str,
    published_at: Any,
    raw_source_method: str,
    content_quality: str,
    matched_entity: str = "",
    matched_alias: str = "",
    evidence: str = "",
    authors: list[str] | None = None,
    match_strength: str = "medium",
    official_entity_source: bool = False,
    is_personal_finetune: bool = False,
    is_test_repo: bool = False,
    event_kind: str = "",
    registry_source_id: str = "",
) -> dict[str, Any] | None:
    clean_url = str(url or "").strip()
    clean_title = trim(title, 220)
    if not clean_url.startswith("http") or not clean_title:
        return None
    return {
        "title": clean_title,
        "url": clean_url,
        "source": source or canonical_domain(clean_url),
        "source_lane": source_lane,
        "matched_entity": matched_entity,
        "matched_alias": matched_alias,
        "published_at": parse_dt(published_at),
        "discovered_at": utc_now(),
        "time_verified": bool(parse_dt(published_at)),
        "summary": trim(summary),
        "evidence": evidence or raw_source_method,
        "content_quality": content_quality,
        "raw_source_method": raw_source_method,
        "authors": authors or [],
        "match_strength": match_strength if match_strength in {"strong", "medium", "weak"} else "medium",
        "official_entity_source": bool(official_entity_source),
        "is_personal_finetune": bool(is_personal_finetune),
        "is_test_repo": bool(is_test_repo),
        "event_kind": event_kind or evidence or raw_source_method,
        "registry_source_id": registry_source_id,
    }


def http_json(url: str, headers: dict[str, str] | None = None, timeout: int = 15) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "leonquant-tech-radar/1.0",
            **(headers or {}),
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as res:  # noqa: S310
        return json.loads(res.read().decode("utf-8"))


def http_text(url: str, timeout: int = 20, *, allow_insecure_ssl_retry: bool = False) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "leonquant-tech-radar/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:  # noqa: S310
            return res.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        if not allow_insecure_ssl_retry or "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise
        with urllib.request.urlopen(req, timeout=timeout, context=ssl._create_unverified_context()) as res:  # noqa: S310, SLF001
            return res.read().decode("utf-8", errors="replace")


def source_id_for(profile: dict[str, Any]) -> str:
    raw = str(profile.get("id") or profile.get("name") or profile.get("url") or "").lower()
    raw = re.sub(r"[^a-z0-9]+", "_", raw).strip("_")
    return raw[:80] or "source"


def registry_row(profile: dict[str, Any]) -> dict[str, Any]:
    now = utc_now()
    return {
        "source_id": source_id_for(profile),
        "entity": str(profile.get("entity") or profile.get("name") or "").strip(),
        "name": str(profile.get("name") or "").strip(),
        "url": str(profile.get("url") or "").strip(),
        "lane": str(profile.get("lane") or "").strip(),
        "priority": str(profile.get("priority") or "").lower().strip() or "p2",
        "source_type": str(profile.get("source_type") or "").strip() or "primary",
        "method": str(profile.get("method") or "").strip(),
        "fallback_method": str(profile.get("fallback") or "").strip(),
        "last_checked_at": now,
        "last_success_at": "",
        "latest_item_at": "",
        "status": "pending",
        "error": "",
        "fallback_used": "",
        "candidate_count": 0,
        "verified_timestamp_count": 0,
        "content_quality_mix": {},
        "latest_titles": [],
    }


def update_registry(row: dict[str, Any], candidates: list[dict[str, Any]], *, status: str, error: str = "", fallback_used: str = "") -> None:
    row["status"] = status
    row["error"] = trim(error, 300)
    row["fallback_used"] = fallback_used
    row["candidate_count"] = len(candidates)
    row["verified_timestamp_count"] = sum(1 for item in candidates if item.get("time_verified"))
    row["content_quality_mix"] = {
        quality: sum(1 for item in candidates if item.get("content_quality") == quality)
        for quality in ("full_text", "summary_only", "metadata_only")
    }
    dates = [parse_dt(item.get("published_at")) for item in candidates if item.get("published_at")]
    row["latest_item_at"] = max(dates) if dates else ""
    if status == "success":
        row["last_success_at"] = utc_now()
    row["latest_titles"] = [str(item.get("title") or "") for item in candidates[:5]]


def item_text(node: ET.Element, *names: str) -> str:
    for name in names:
        found = node.find(name)
        if found is not None and found.text:
            return str(found.text)
    return ""


def parse_feed_entries(xml_text: str) -> list[dict[str, str]]:
    root = ET.fromstring(xml_text)
    entries: list[dict[str, str]] = []
    if root.tag.endswith("rss") or root.find("./channel/item") is not None:
        for item in root.findall("./channel/item"):
            link = item_text(item, "link")
            if not link:
                guid = item.find("guid")
                link = str(guid.text or "") if guid is not None else ""
            entries.append(
                {
                    "title": item_text(item, "title"),
                    "url": link,
                    "summary": item_text(item, "description", "{http://purl.org/rss/1.0/modules/content/}encoded"),
                    "published_at": item_text(item, "pubDate", "published", "updated"),
                }
            )
        return entries
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
        link = ""
        for node in entry.findall("a:link", ns):
            href = str(node.attrib.get("href") or "")
            if href.startswith("http") and node.attrib.get("rel", "alternate") == "alternate":
                link = href
                break
        entries.append(
            {
                "title": entry.findtext("a:title", default="", namespaces=ns),
                "url": link,
                "summary": entry.findtext("a:summary", default="", namespaces=ns) or entry.findtext("a:content", default="", namespaces=ns),
                "published_at": entry.findtext("a:published", default="", namespaces=ns) or entry.findtext("a:updated", default="", namespaces=ns),
            }
        )
    return entries


def profile_item_candidate(profile: dict[str, Any], item: dict[str, str], method: str, fallback_used: str = "") -> dict[str, Any] | None:
    entity = str(profile.get("entity") or profile.get("name") or "")
    return candidate(
        title=item.get("title") or f"{entity} source update",
        url=item.get("url") or str(profile.get("url") or ""),
        source=canonical_domain(item.get("url") or profile.get("url") or ""),
        source_lane=str(profile.get("lane") or "official_ai_labs"),
        summary=item.get("summary") or f"Metadata snapshot from {entity}.",
        published_at=item.get("published_at") or utc_now(),
        raw_source_method=method,
        content_quality="summary_only" if item.get("summary") else "metadata_only",
        matched_entity=entity,
        matched_alias=entity,
        evidence=fallback_used or method,
        match_strength="strong",
        official_entity_source=str(profile.get("source_type") or "primary") == "primary",
        event_kind="source_item",
        registry_source_id=source_id_for(profile),
    )


def html_metadata_candidate(profile: dict[str, Any], html: str, method: str, fallback_used: str = "metadata_fallback") -> dict[str, Any] | None:
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.I | re.S)
    h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", html, flags=re.I | re.S)
    title = re.sub(r"<[^>]+>", " ", (h1_match or title_match).group(1) if (h1_match or title_match) else "")
    title = trim(title or f"{profile.get('entity') or profile.get('name')} official source snapshot", 220)
    summary_match = re.search(r'<meta[^>]+(?:name|property)=["\'](?:description|og:description)["\'][^>]+content=["\']([^"\']+)["\']', html, flags=re.I)
    summary = summary_match.group(1) if summary_match else ""
    return profile_item_candidate(
        profile,
        {"title": title, "url": str(profile.get("url") or ""), "summary": summary, "published_at": utc_now()},
        method,
        fallback_used,
    )


def acquire_profile_sources(profiles: list[dict[str, Any]], max_items_per_source: int = 3) -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    notes: list[str] = []
    registry: list[dict[str, Any]] = []
    enabled = [row for row in profiles if row.get("enabled") is True and str(row.get("method") or "") in PROFILE_FETCH_METHODS]
    for profile in enabled:
        row = registry_row(profile)
        registry.append(row)
        method = str(profile.get("method") or "")
        url = str(profile.get("url") or "")
        try:
            text = http_text(url, timeout=20, allow_insecure_ssl_retry=True)
            source_candidates: list[dict[str, Any]] = []
            if method in {"rss", "atom"}:
                entries = parse_feed_entries(text)
                for entry in entries[:max_items_per_source]:
                    item = profile_item_candidate(profile, entry, "rss" if method == "atom" else method)
                    if item:
                        source_candidates.append(item)
            elif method == "sitemap":
                root = ET.fromstring(text)
                urls: list[dict[str, str]] = []
                for node in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
                    loc = node.findtext("{http://www.sitemaps.org/schemas/sitemap/0.9}loc", default="")
                    lastmod = node.findtext("{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod", default="")
                    if loc.startswith("http"):
                        urls.append({"title": f"{profile.get('entity') or profile.get('name')} sitemap item", "url": loc, "summary": "", "published_at": lastmod})
                for entry in urls[:max_items_per_source]:
                    item = profile_item_candidate(profile, entry, "sitemap")
                    if item:
                        source_candidates.append(item)
            else:
                item = html_metadata_candidate(profile, text, method)
                if item:
                    source_candidates.append(item)
            source_candidates = [item for item in source_candidates if item]
            candidates.extend(source_candidates)
            update_registry(row, source_candidates, status="success" if source_candidates else "zero_hit", fallback_used="" if method in {"rss", "atom", "sitemap"} else "metadata_fallback")
        except Exception as exc:  # noqa: BLE001
            fallback = str(profile.get("fallback") or "")
            if fallback == "metadata_only":
                item = profile_item_candidate(
                    profile,
                    {"title": f"{profile.get('entity') or profile.get('name')} official source metadata", "url": url, "summary": str(profile.get("description") or ""), "published_at": utc_now()},
                    "metadata",
                    "metadata_only",
                )
                source_candidates = [item] if item else []
                candidates.extend(source_candidates)
                update_registry(row, source_candidates, status="success" if source_candidates else "failed", error=str(exc), fallback_used="metadata_only")
            else:
                update_registry(row, [], status="failed", error=str(exc))
            notes.append(f"profile {profile.get('name') or url}: {exc}")
    return candidates, notes, registry


def hf_model_candidate(model: Any, alias: str, aliases: list[dict[str, str]]) -> dict[str, Any] | None:
    repo_id = str(getattr(model, "modelId", "") or getattr(model, "id", "") or "")
    if not repo_id and isinstance(model, dict):
        repo_id = str(model.get("modelId") or model.get("id") or "")
    if not repo_id:
        return None
    modified = getattr(model, "lastModified", None)
    if isinstance(model, dict):
        modified = model.get("lastModified") or model.get("last_modified")
    tags = list(getattr(model, "tags", []) or (model.get("tags") if isinstance(model, dict) else []) or [])
    pipeline_tag = str(getattr(model, "pipeline_tag", "") or (model.get("pipeline_tag") if isinstance(model, dict) else "") or "")
    card_data = getattr(model, "cardData", None) or (model.get("cardData") if isinstance(model, dict) else None) or {}
    card_summary = ""
    base_model_text = ""
    if isinstance(card_data, dict):
        card_summary = " ".join(str(x) for x in (card_data.get("language"), card_data.get("license"), card_data.get("library_name")) if x)
        base_model_text = " ".join(str(x) for x in (card_data.get("base_model"), card_data.get("base_model_relation")) if x)
    title = f"Hugging Face model updated: {repo_id}"
    summary = trim(f"alias={alias}; pipeline={pipeline_tag}; tags={', '.join(map(str, tags[:8]))}; base_model={base_model_text}; {card_summary}", 500)
    matched_entity, matched_alias, match_strength, official_entity_source, weak_evidence = match_with_strength(
        strong_text=f"{repo_id}",
        weak_text=f"{alias} {pipeline_tag} {' '.join(map(str, tags))} {base_model_text} {card_summary}",
        repo_id=repo_id,
        aliases=aliases,
    )
    test_repo = is_test_repo_name(repo_id)
    personal_finetune = is_personal_finetune_name(repo_id, tags)
    evidence = weak_evidence or "hf_model_metadata"
    if test_repo:
        match_strength = "weak"
        evidence = WEAK_MATCH_EVIDENCE
    return candidate(
        title=title,
        url=f"https://huggingface.co/{repo_id}",
        source="huggingface.co",
        source_lane="huggingface_model",
        summary=summary,
        published_at=modified,
        raw_source_method="hf_api",
        content_quality="metadata_only",
        matched_entity=matched_entity,
        matched_alias=matched_alias or alias,
        evidence=evidence,
        match_strength=match_strength,
        official_entity_source=official_entity_source,
        is_personal_finetune=personal_finetune,
        is_test_repo=test_repo,
    )


def acquire_hf(limit_per_alias: int, aliases: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[str]]:
    notes: list[str] = []
    rows: list[dict[str, Any]] = []
    try:
        from huggingface_hub import HfApi  # type: ignore
    except Exception as exc:  # noqa: BLE001
        notes.append(f"hf_api unavailable: {exc}")
        for alias in HF_SEARCH_ALIASES:
            try:
                params = urllib.parse.urlencode({"search": alias, "sort": "lastModified", "limit": limit_per_alias, "full": "true"})
                payload = http_json(f"https://huggingface.co/api/models?{params}")
                for model in payload if isinstance(payload, list) else []:
                    item = hf_model_candidate(model, alias, aliases)
                    if item:
                        rows.append(item)
            except Exception as rest_exc:  # noqa: BLE001
                notes.append(f"hf_rest {alias}: {rest_exc}")
        return rows, notes
    api = HfApi()
    for alias in HF_SEARCH_ALIASES:
        try:
            models = api.list_models(search=alias, sort="lastModified", limit=limit_per_alias, full=True, cardData=True)
            for model in models:
                item = hf_model_candidate(model, alias, aliases)
                if item:
                    rows.append(item)
        except Exception as exc:  # noqa: BLE001
            notes.append(f"hf_api {alias}: {exc}")
    return rows, notes


def github_repo_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(str(url or ""))
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return ""


def github_headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def github_release_candidate(repo: str, release: dict[str, Any], aliases: list[dict[str, str]]) -> dict[str, Any] | None:
    name = str(release.get("name") or release.get("tag_name") or "release").strip()
    url = str(release.get("html_url") or f"https://github.com/{repo}/releases").strip()
    published = release.get("published_at") or release.get("created_at")
    body = str(release.get("body") or "")
    matched_entity, matched_alias, match_strength, official_entity_source, weak_evidence = match_with_strength(
        strong_text=f"{repo} {name}",
        weak_text=body,
        repo_id=repo,
        aliases=aliases,
    )
    test_repo = is_test_repo_name(repo)
    personal_finetune = is_personal_finetune_name(f"{repo} {name} {body}")
    evidence = weak_evidence or "github_release"
    if test_repo:
        match_strength = "weak"
        evidence = WEAK_MATCH_EVIDENCE
    return candidate(
        title=f"{repo} release: {name}",
        url=url,
        source="github.com",
        source_lane="github_release",
        summary=body or f"GitHub release metadata for {repo}.",
        published_at=published,
        raw_source_method="github_api",
        content_quality="summary_only" if body else "metadata_only",
        matched_entity=matched_entity,
        matched_alias=matched_alias,
        evidence=evidence,
        match_strength=match_strength,
        official_entity_source=official_entity_source,
        is_personal_finetune=personal_finetune,
        is_test_repo=test_repo,
    )


def github_repo_candidate(repo: str, repo_payload: dict[str, Any], aliases: list[dict[str, str]]) -> dict[str, Any] | None:
    updated = repo_payload.get("updated_at") or repo_payload.get("pushed_at")
    description = str(repo_payload.get("description") or "")
    url = str(repo_payload.get("html_url") or f"https://github.com/{repo}")
    matched_entity, matched_alias, match_strength, official_entity_source, weak_evidence = match_with_strength(
        strong_text=f"{repo}",
        weak_text=description,
        repo_id=repo,
        aliases=aliases,
    )
    test_repo = is_test_repo_name(repo)
    personal_finetune = is_personal_finetune_name(f"{repo} {description}")
    evidence = weak_evidence or "github_repo_metadata"
    if test_repo:
        match_strength = "weak"
        evidence = WEAK_MATCH_EVIDENCE
    return candidate(
        title=f"GitHub repo updated: {repo}",
        url=url,
        source="github.com",
        source_lane="github_release",
        summary=description or f"GitHub repository metadata for {repo}.",
        published_at=updated,
        raw_source_method="github_api",
        content_quality="metadata_only",
        matched_entity=matched_entity,
        matched_alias=matched_alias,
        evidence=evidence,
        match_strength=match_strength,
        official_entity_source=official_entity_source,
        is_personal_finetune=personal_finetune,
        is_test_repo=test_repo,
    )


def acquire_github(profiles: list[dict[str, Any]], aliases: list[dict[str, str]], limit_releases: int) -> tuple[list[dict[str, Any]], list[str]]:
    notes: list[str] = []
    rows: list[dict[str, Any]] = []
    repos = set(GITHUB_REPOS)
    repos.update(github_repo_from_url(row.get("url", "")) for row in profiles if row.get("method") == "github_api")
    repos = {repo for repo in repos if repo and "/" in repo}
    for repo in sorted(repos):
        try:
            releases = http_json(f"https://api.github.com/repos/{repo}/releases?per_page={limit_releases}", github_headers())
            if isinstance(releases, list) and releases:
                for release in releases[:limit_releases]:
                    item = github_release_candidate(repo, release, aliases)
                    if item:
                        rows.append(item)
            else:
                repo_payload = http_json(f"https://api.github.com/repos/{repo}", github_headers())
                if isinstance(repo_payload, dict):
                    item = github_repo_candidate(repo, repo_payload, aliases)
                    if item:
                        rows.append(item)
        except Exception as exc:  # noqa: BLE001
            notes.append(f"github {repo}: {exc}")
    for org in sorted(GITHUB_ORGS):
        try:
            org_repos = http_json(f"https://api.github.com/orgs/{org}/repos?sort=updated&per_page=3", github_headers())
            for repo_payload in org_repos if isinstance(org_repos, list) else []:
                repo_full = str(repo_payload.get("full_name") or "")
                if not repo_full:
                    continue
                item = github_repo_candidate(repo_full, repo_payload, aliases)
                if item:
                    rows.append(item)
        except Exception as exc:  # noqa: BLE001
            notes.append(f"github org {org}: {exc}")
    return rows, notes


def arxiv_entry_candidate(entry: ET.Element, aliases: list[dict[str, str]]) -> dict[str, Any] | None:
    ns = {"a": "http://www.w3.org/2005/Atom"}
    title = trim(entry.findtext("a:title", default="", namespaces=ns), 220)
    summary = trim(entry.findtext("a:summary", default="", namespaces=ns), 900)
    published = entry.findtext("a:published", default="", namespaces=ns)
    link = ""
    for node in entry.findall("a:link", ns):
        href = str(node.attrib.get("href") or "")
        if href.startswith("http") and (node.attrib.get("rel") in {"alternate", None, ""}):
            link = href
            break
    authors = [trim(node.findtext("a:name", default="", namespaces=ns), 120) for node in entry.findall("a:author", ns)]
    matched_entity, matched_alias = match_entity_alias(f"{title} {summary}", aliases)
    return candidate(
        title=title,
        url=link,
        source="arxiv.org",
        source_lane="research_papers",
        summary=summary,
        published_at=published,
        raw_source_method="arxiv_api",
        content_quality="summary_only",
        matched_entity=matched_entity,
        matched_alias=matched_alias,
        evidence="arxiv_abstract",
        authors=[a for a in authors if a],
    )


def acquire_arxiv(aliases: list[dict[str, str]], max_results: int) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    notes: list[str] = []
    per_category = max(1, max_results // len(ARXIV_CATEGORIES))
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    for category in ARXIV_CATEGORIES:
        category_rows, category_notes = acquire_arxiv_category(aliases, category, per_category)
        notes.extend(category_notes)
        for item in category_rows:
            published = item.get("published_at")
            try:
                dt = datetime.fromisoformat(str(published).replace("Z", "+00:00"))
            except ValueError:
                dt = None
            if dt is not None and dt.astimezone(timezone.utc) < cutoff:
                continue
            item["arxiv_category"] = category
            rows.append(item)
    return dedupe(rows)[:max_results], notes


def acquire_arxiv_category(aliases: list[dict[str, str]], category: str, max_results: int) -> tuple[list[dict[str, Any]], list[str]]:
    params = urllib.parse.urlencode(
        {
            "search_query": f"cat:{category} AND {ARXIV_TOPIC_QUERY}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
    )
    url = f"https://export.arxiv.org/api/query?{params}"
    try:
        root = ET.fromstring(http_text(url, timeout=45, allow_insecure_ssl_retry=True))
    except Exception as exc:  # noqa: BLE001
        return [], [f"arxiv_api: {exc}"]
    rows = []
    for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
        item = arxiv_entry_candidate(entry, aliases)
        if not item:
            continue
        rows.append(item)
    return rows, []


def openrouter_candidate(model: dict[str, Any]) -> dict[str, Any] | None:
    model_id = str(model.get("id") or "").strip()
    if not model_id:
        return None
    return candidate(
        title=f"OpenRouter model listed: {model_id}",
        url=f"https://openrouter.ai/{model_id}",
        source="openrouter.ai",
        source_lane="model_hub",
        summary=str(model.get("description") or model.get("name") or model_id),
        published_at=utc_now(),
        raw_source_method="api",
        content_quality="metadata_only",
        evidence="openrouter_model_metadata",
    )


def acquire_openrouter(limit: int) -> tuple[list[dict[str, Any]], list[str]]:
    try:
        payload = http_json("https://openrouter.ai/api/v1/models")
    except Exception as exc:  # noqa: BLE001
        return [], [f"openrouter api: {exc}"]
    rows = []
    for model in (payload.get("data") if isinstance(payload, dict) else []) or []:
        item = openrouter_candidate(model)
        if item:
            rows.append(item)
        if len(rows) >= limit:
            break
    return rows, []


def dedupe(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_url: dict[str, dict[str, Any]] = {}
    for row in candidates:
        url = str(row.get("url") or "")
        if url and url not in by_url:
            by_url[url] = row
    return list(by_url.values())


def api_registry_rows(profiles: list[dict[str, Any]], candidates: list[dict[str, Any]], notes: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    enabled = [row for row in profiles if row.get("enabled") is True and str(row.get("method") or "") in API_METHODS]
    note_blob = "\n".join(notes)
    by_method = defaultdict(list)
    by_repo = defaultdict(list)
    for item in candidates:
        by_method[str(item.get("raw_source_method") or "")].append(item)
        if item.get("registry_source_id"):
            by_repo[str(item.get("registry_source_id"))].append(item)
    for profile in enabled:
        row = registry_row(profile)
        method = str(profile.get("method") or "")
        sid = source_id_for(profile)
        url = str(profile.get("url") or "")
        source_candidates = list(by_repo.get(sid) or [])
        if not source_candidates:
            if method == "github_api":
                repo = github_repo_from_url(url)
                source_candidates = [item for item in by_method.get("github_api", []) if repo and repo.lower() in str(item.get("url") or "").lower()]
                if not source_candidates:
                    entity = str(profile.get("entity") or "").lower()
                    source_candidates = [
                        item for item in by_method.get("github_api", [])
                        if entity
                        and (
                            entity == str(item.get("matched_entity") or "").lower()
                            or entity in str(item.get("title") or "").lower()
                            or entity in str(item.get("summary") or "").lower()
                        )
                    ]
            elif method == "hf_api":
                source_candidates = by_method.get("hf_api", [])
            elif method == "arxiv_api":
                source_candidates = by_method.get("arxiv_api", [])
            elif method == "api" and "openrouter.ai" in url:
                source_candidates = [item for item in by_method.get("api", []) if "openrouter.ai" in str(item.get("url") or "")]
        profile_error = ""
        if method == "hf_api" and "hf_" in note_blob:
            profile_error = "; ".join(note for note in notes if note.startswith("hf_"))[:300]
        elif method == "github_api":
            repo = github_repo_from_url(url)
            profile_error = "; ".join(note for note in notes if repo and repo in note)[:300]
        elif method == "arxiv_api":
            profile_error = "; ".join(note for note in notes if note.startswith("arxiv_api"))[:300]
        elif method == "api":
            profile_error = "; ".join(note for note in notes if "openrouter" in note)[:300]
        status = "success" if source_candidates else ("failed" if profile_error else "zero_hit")
        update_registry(row, source_candidates, status=status, error=profile_error)
        rows.append(row)
    return rows


def write_source_registry(rows: list[dict[str, Any]], profiles: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    now = utc_now()
    rows = sorted(rows, key=lambda row: (row.get("priority") != "p0", row.get("lane") or "", row.get("entity") or ""))
    p0 = [row for row in rows if row.get("priority") == "p0"]
    p0_configured_entities = {str(row.get("entity") or "").strip() for row in p0 if str(row.get("entity") or "").strip()}
    missing = sorted(CRITICAL_ENTITIES - p0_configured_entities)
    checked = [row for row in p0 if row.get("status") != "pending"]
    success = [row for row in p0 if row.get("status") == "success"]
    failed = [row for row in p0 if row.get("status") == "failed"]
    zero_hit = [row for row in p0 if row.get("status") == "zero_hit"]
    verified = sum(1 for item in candidates if item.get("time_verified"))
    quality_mix = {
        quality: sum(1 for item in candidates if item.get("content_quality") == quality)
        for quality in ("full_text", "summary_only", "metadata_only")
    }
    source_type_counts = {
        kind: sum(1 for row in rows if row.get("source_type") == kind)
        for kind in ("primary", "independent", "community")
    }
    lane_counts: dict[str, dict[str, int]] = {}
    for lane in sorted({str(row.get("lane") or "") for row in rows if row.get("lane")}):
        lane_rows = [row for row in rows if row.get("lane") == lane]
        lane_counts[lane] = {
            "configured": len(lane_rows),
            "checked": sum(1 for row in lane_rows if row.get("status") != "pending"),
            "success": sum(1 for row in lane_rows if row.get("status") == "success"),
            "failed": sum(1 for row in lane_rows if row.get("status") == "failed"),
            "zero_hit": sum(1 for row in lane_rows if row.get("status") == "zero_hit"),
        }
    payload = {
        "schema_version": "tech-source-registry-v1",
        "generated_at_utc": now,
        "summary": {
            "source_count": len(rows),
            "p0_configured": len(p0),
            "p0_checked": len(checked),
            "p0_success": len(success),
            "p0_failed": len(failed),
            "p0_zero_hit": len(zero_hit),
            "missing_critical_entities": missing,
            "verified_timestamp_ratio": round(verified / max(1, len(candidates)), 4),
            "content_quality_ratio": {quality: round(count / max(1, len(candidates)), 4) for quality, count in quality_mix.items()},
            "primary_source_count": source_type_counts.get("primary", 0),
            "independent_source_count": source_type_counts.get("independent", 0),
            "community_source_count": source_type_counts.get("community", 0),
            "coverage_by_lane": lane_counts,
        },
        "sources": rows,
    }
    dump_json(TECH_SOURCE_REGISTRY, payload)
    return payload


def load_tier2_discovery_registry_rows() -> list[dict[str, Any]]:
    if not TECH_ACTIVE.is_file():
        return []
    validation_by_url: dict[str, dict[str, Any]] = {}
    if TECH_VALIDATION_JSON.is_file():
        try:
            validation = load_json(TECH_VALIDATION_JSON)
            for item in validation.get("sources") or []:
                url = str(item.get("input_url") or item.get("url") or "").strip()
                if url:
                    validation_by_url[url] = item
        except Exception:
            validation_by_url = {}
    rows: list[dict[str, Any]] = []
    pending_name = ""
    for raw in TECH_ACTIVE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            pending_name = line.lstrip("#").strip()
            continue
        profile = {
            "id": f"tier2_{canonical_domain(line)}",
            "entity": pending_name or canonical_domain(line),
            "name": pending_name or canonical_domain(line),
            "url": line,
            "lane": "independent_ai_news",
            "priority": "p2",
            "source_type": "independent",
            "method": "rss",
            "fallback": "feed_summary_fallback",
        }
        row = registry_row(profile)
        validation_row = validation_by_url.get(line) or {}
        row["status"] = "success"
        row["last_success_at"] = utc_now()
        row["candidate_count"] = int(bool(validation_row.get("production_ready", True)))
        row["fallback_used"] = "feed_summary_fallback"
        row["error"] = str(validation_row.get("validation_status") or "PASS_RSS")
        rows.append(row)
        pending_name = ""
    return rows


def acquire_all(*, hf_limit: int = 2, github_releases: int = 2, arxiv_results: int = 10) -> dict[str, Any]:
    profiles = load_profiles()
    aliases = load_watchlist_aliases()
    candidates: list[dict[str, Any]] = []
    notes: list[str] = []
    registry_rows: list[dict[str, Any]] = []
    method_counts: dict[str, int] = {}

    enabled_profiles = [row for row in profiles if row.get("enabled") is True]
    method_counts = {method: sum(1 for row in enabled_profiles if row.get("method") == method) for method in sorted({str(row.get("method")) for row in enabled_profiles})}

    profile_rows, profile_notes, profile_registry = acquire_profile_sources(profiles)
    candidates.extend(profile_rows)
    notes.extend(profile_notes)
    registry_rows.extend(profile_registry)
    time.sleep(0.2)

    hf_rows, hf_notes = acquire_hf(hf_limit, aliases)
    candidates.extend(hf_rows)
    notes.extend(hf_notes)
    time.sleep(0.2)

    gh_rows, gh_notes = acquire_github(profiles, aliases, github_releases)
    candidates.extend(gh_rows)
    notes.extend(gh_notes)
    time.sleep(0.5)

    arxiv_rows, arxiv_notes = acquire_arxiv(aliases, arxiv_results)
    candidates.extend(arxiv_rows)
    notes.extend(arxiv_notes)

    if any(row.get("url") == "https://openrouter.ai/api/v1/models" and row.get("enabled") for row in profiles):
        openrouter_rows, openrouter_notes = acquire_openrouter(8)
        candidates.extend(openrouter_rows)
        notes.extend(openrouter_notes)

    candidates = dedupe([row for row in candidates if row])
    registry_rows.extend(api_registry_rows(profiles, candidates, notes))
    registry_rows.extend(load_tier2_discovery_registry_rows())
    source_registry = write_source_registry(registry_rows, profiles, candidates)
    return {
        "schema_version": "tech-api-candidates-v1",
        "generated_at_utc": utc_now(),
        "candidate_count": len(candidates),
        "candidates_by_method": {
            method: sum(1 for row in candidates if row.get("raw_source_method") == method)
            for method in ("hf_api", "github_api", "arxiv_api", "api")
        },
        "content_quality_mix": {
            quality: sum(1 for row in candidates if row.get("content_quality") == quality)
            for quality in ("full_text", "summary_only", "metadata_only")
        },
        "active_api_sources": sum(1 for row in enabled_profiles if row.get("method") in API_METHODS),
        "profile_method_counts": method_counts,
        "source_registry": source_registry.get("summary", {}),
        "notes": notes[:50],
        "candidates": candidates,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Acquire API-first candidates for Tech Radar")
    parser.add_argument("--output", type=Path, default=TECH_API_CANDIDATES)
    parser.add_argument("--hf-limit", type=int, default=2)
    parser.add_argument("--github-releases", type=int, default=2)
    parser.add_argument("--arxiv-results", type=int, default=10)
    args = parser.parse_args()
    payload = acquire_all(hf_limit=args.hf_limit, github_releases=args.github_releases, arxiv_results=args.arxiv_results)
    dump_json(args.output, payload)
    print(f"Wrote {payload['candidate_count']} API candidates -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
