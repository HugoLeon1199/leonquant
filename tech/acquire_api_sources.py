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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("LEON_TECH_BASE_DIR", str(ROOT / "tech"))

from scripts.tech_common import (  # noqa: E402
    TECH_API_CANDIDATES,
    TECH_FRONTIER_WATCHLIST,
    TECH_SOURCE_PROFILES,
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
ARXIV_QUERY = (
    '(cat:cs.AI OR cat:cs.CL OR cat:cs.LG OR cat:cs.CV OR cat:cs.RO) '
    'AND (LLM OR agent OR multimodal OR diffusion OR "video generation" '
    'OR "text-to-image" OR ComfyUI OR MCP OR "reasoning model")'
)
API_METHODS = {"api", "github_api", "hf_api", "arxiv_api", "gdelt"}


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
    if isinstance(card_data, dict):
        card_summary = " ".join(str(x) for x in (card_data.get("language"), card_data.get("license"), card_data.get("library_name")) if x)
    title = f"Hugging Face model updated: {repo_id}"
    summary = trim(f"alias={alias}; pipeline={pipeline_tag}; tags={', '.join(map(str, tags[:8]))}; {card_summary}", 500)
    matched_entity, matched_alias = match_entity_alias(f"{repo_id} {alias} {summary}", aliases)
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
        evidence="hf_model_metadata",
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
    matched_entity, matched_alias = match_entity_alias(f"{repo} {name}", aliases)
    if not matched_entity:
        matched_entity, matched_alias = match_entity_alias(body, aliases)
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
        evidence="github_release",
    )


def github_repo_candidate(repo: str, repo_payload: dict[str, Any], aliases: list[dict[str, str]]) -> dict[str, Any] | None:
    updated = repo_payload.get("updated_at") or repo_payload.get("pushed_at")
    description = str(repo_payload.get("description") or "")
    url = str(repo_payload.get("html_url") or f"https://github.com/{repo}")
    matched_entity, matched_alias = match_entity_alias(f"{repo} {description}", aliases)
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
        evidence="github_repo_metadata",
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
    params = urllib.parse.urlencode(
        {
            "search_query": ARXIV_QUERY,
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
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
        item = arxiv_entry_candidate(entry, aliases)
        if not item:
            continue
        published = item.get("published_at")
        try:
            dt = datetime.fromisoformat(str(published).replace("Z", "+00:00"))
        except ValueError:
            dt = None
        if dt is not None and dt.astimezone(timezone.utc) < cutoff:
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


def acquire_all(*, hf_limit: int = 2, github_releases: int = 2, arxiv_results: int = 10) -> dict[str, Any]:
    profiles = load_profiles()
    aliases = load_watchlist_aliases()
    candidates: list[dict[str, Any]] = []
    notes: list[str] = []
    method_counts: dict[str, int] = {}

    enabled_profiles = [row for row in profiles if row.get("enabled") is True]
    method_counts = {method: sum(1 for row in enabled_profiles if row.get("method") == method) for method in sorted({str(row.get("method")) for row in enabled_profiles})}

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
