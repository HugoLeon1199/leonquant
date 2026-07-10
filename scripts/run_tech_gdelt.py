#!/usr/bin/env python3
"""Standalone GDELT technology & AI pulse."""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google.cloud import bigquery

from scripts.tech_common import (
    TECH_GDELT_OUTPUT,
    TECH_GDELT_SCHEMA,
    TECH_GDELT_WEB_OUTPUT,
    canonical_domain,
    dump_json,
    infer_section,
    is_official_host,
)

ROOT = Path(__file__).resolve().parents[1]
SQL_PATH = ROOT / "sql" / "gdelt_tech_pulse.sql"
STRONG_AI_RE = re.compile(
    r"\b(model|llm|large language model|generative ai|genai|agent|agents|agentic|mcp|"
    r"gpu|semiconductor|robotics|automation|ai startup|openai|anthropic|deepmind|"
    r"gemini|claude|chatgpt|nvidia|mistral|hugging face|qwen|deepseek|llama|"
    r"glm|z\.ai|zhipu|bigmodel|kimi|moonshot|minimax|doubao|hunyuan|flux|"
    r"black forest labs|comfyui|stable diffusion|lora|controlnet|sdxl|runway|"
    r"kling|veo|sora|hunyuanvideo|openrouter|replicate|fal\.ai|vllm|sglang|"
    r"langgraph|llamaindex|cursor|claude code|openhands)\b",
    re.IGNORECASE,
)
POLITICS_WAR_RE = re.compile(
    r"\b(ukraine|russia|war|missile|troops|soldiers|oil terminal|attack|sanction|"
    r"president|minister|election|border|ceasefire)\b",
    re.IGNORECASE,
)


def get_client() -> bigquery.Client:
    return bigquery.Client()


def run_query(
    client: bigquery.Client,
    sql: str,
    *,
    dry_run: bool,
    maximum_bytes_billed: int,
) -> tuple[list[dict[str, Any]] | None, dict[str, Any]]:
    job_config = bigquery.QueryJobConfig(
        maximum_bytes_billed=maximum_bytes_billed,
        dry_run=dry_run,
        use_query_cache=not dry_run,
    )
    job = client.query(sql, job_config=job_config)
    raw_bytes = getattr(job, "total_bytes_processed", None) or getattr(job, "total_bytes_billed", None)
    meta = {
        "dry_run": dry_run,
        "bytes_billed": int(raw_bytes) if raw_bytes not in (None, 0) else None,
    }
    if dry_run:
        return None, meta
    rows = [dict(row.items()) for row in job.result()]
    raw_bytes = getattr(job, "total_bytes_processed", None) or getattr(job, "total_bytes_billed", None)
    meta["bytes_billed"] = int(raw_bytes) if raw_bytes not in (None, 0) else None
    return rows, meta


def event_tags(blob: str) -> list[str]:
    tags: list[str] = []
    checks = {
        "model_agent_moi": ("model", "llm", "agent", "multimodal", "copilot", "chatgpt", "claude", "gemini"),
        "chip_ha_tang": ("gpu", "semiconductor", "chip", "hbm", "datacenter", "cloud", "server"),
        "cybersecurity": ("cyber", "ransomware", "breach", "vulnerability", "zero-day", "prompt injection"),
        "robotics": ("robot", "humanoid", "drone", "robotaxi", "autonomous"),
        "chinh_sach_cuoc_dua_toan_cau": ("regulation", "policy", "governance", "copyright", "export control"),
        "open_source_developer_tools": ("open source", "github", "developer", "sdk", "framework"),
        "radar_khu_vuc": ("china", "japan", "korea", "india", "taiwan", "europe", "arab"),
    }
    low = blob.lower()
    for tag, kws in checks.items():
        if any(kw in low for kw in kws):
            tags.append(tag)
    return tags or [infer_section(blob)]


def companies_from_blob(blob: str) -> list[str]:
    names = [
        "OpenAI", "Anthropic", "Google", "DeepMind", "Meta", "Microsoft", "NVIDIA",
        "xAI", "Mistral", "Cohere", "Hugging Face", "Databricks", "TSMC", "AMD",
        "Intel", "Broadcom", "ASML", "Alibaba", "Baidu", "Tencent", "Huawei",
        "Z.ai", "Zhipu", "BigModel", "Qwen", "DeepSeek", "Kimi", "Moonshot",
        "MiniMax", "Doubao", "Hunyuan", "Black Forest Labs", "ComfyUI",
        "Runway", "Kling", "Veo", "Sora", "OpenRouter", "Replicate",
        "fal.ai", "LangGraph", "LlamaIndex", "Cursor", "Claude Code", "OpenHands",
    ]
    aliases = {"智谱": "Zhipu", "混元": "Hunyuan", "豆包": "Doubao"}
    extra_names = [
        "Flux", "Stable Diffusion", "LoRA", "ControlNet", "HunyuanVideo",
        "SGLang", "MCP",
    ]
    extra_aliases = {
        "智谱": "Zhipu",
        "智谱AI": "Zhipu",
        "混元": "Hunyuan",
        "豆包": "Doubao",
        "FLUX": "Flux",
        "Black Forest Labs": "Flux",
        "Hunyuan Video": "HunyuanVideo",
        "Model Context Protocol": "MCP",
    }
    aliases.update(extra_aliases)
    low = blob.lower()
    out = [name for name in [*names, *extra_names] if name.lower() in low]
    for alias, canonical in aliases.items():
        if alias in blob and canonical not in out:
            out.append(canonical)
    return out[:32]


def signal_keywords_from_blob(blob: str) -> list[str]:
    keywords = [
        "model", "llm", "large language model", "generative ai", "genai", "agent",
        "mcp", "gpu", "semiconductor", "robotics", "automation", "ai startup",
        "openai", "anthropic", "deepmind", "gemini", "claude", "chatgpt",
        "nvidia", "mistral", "hugging face", "qwen", "deepseek", "llama",
        "glm", "z.ai", "zhipu", "智谱", "bigmodel", "kimi", "moonshot",
        "minimax", "doubao", "hunyuan", "flux", "black forest labs", "comfyui",
        "stable diffusion", "lora", "controlnet", "sdxl", "runway", "kling",
        "veo", "sora", "hunyuanvideo", "openrouter", "replicate", "fal.ai",
        "vllm", "sglang", "langgraph", "llamaindex", "cursor", "claude code", "openhands",
    ]
    low = blob.lower()
    return [kw for kw in keywords if kw in low][:8]


def bytes_status(*values: Any) -> str:
    return "known" if all(value not in (None, 0, "") for value in values) else "unknown"


def has_strong_ai_signal(row: dict[str, Any], source_urls: list[str]) -> bool:
    blob = " ".join(
        str(part or "")
        for part in [
            row.get("Actor1Name"),
            row.get("Actor2Name"),
            row.get("V2Organizations"),
            row.get("V2Themes"),
            row.get("Link_Bai_Bao"),
            " ".join(source_urls),
        ]
    )
    if not STRONG_AI_RE.search(blob):
        return False
    if POLITICS_WAR_RE.search(blob) and not re.search(r"\b(ai|llm|model|gpu|semiconductor|robotics|automation|nvidia|openai|anthropic)\b", blob, re.I):
        return False
    return True


def build_event(row: dict[str, Any]) -> dict[str, Any]:
    source_urls = [u for u in (row.get("SourceURLs") or []) if isinstance(u, str) and u.startswith("http")]
    domains = sorted({canonical_domain(u) for u in source_urls if canonical_domain(u)})
    official_present = any(is_official_host(d) for d in domains)
    actor1 = str(row.get("Actor1Name") or "").strip()
    actor2 = str(row.get("Actor2Name") or "").strip()
    orgs = str(row.get("V2Organizations") or "").strip()
    themes = str(row.get("V2Themes") or "").strip()
    blob = " ".join(
        part for part in [actor1, actor2, orgs, themes, str(row.get("Link_Bai_Bao") or "")] if part
    )
    title_parts = [part for part in [actor1, actor2] if part]
    title = " - ".join(title_parts) or str(row.get("Link_Bai_Bao") or "Technology event")
    summary_parts = []
    if orgs:
        summary_parts.append(f"Tín hiệu tổ chức: {orgs[:180]}")
    if companies_from_blob(blob):
        summary_parts.append("Công ty liên quan: " + ", ".join(companies_from_blob(blob)))
    if event_tags(blob):
        summary_parts.append("Chủ đề: " + ", ".join(event_tags(blob)[:3]))
    summary = ". ".join(summary_parts) or title
    return {
        "event_id": str(row.get("GlobalEventID") or ""),
        "title": title,
        "summary": summary,
        "source_urls": source_urls[:8],
        "source_count": max(int(row.get("source_count") or 0), len(source_urls), 1),
        "independent_domain_count": len(domains),
        "official_source_present": official_present,
        "topic_tags": event_tags(blob),
        "company_tags": companies_from_blob(blob),
        "signal_keywords": signal_keywords_from_blob(blob),
        "reported_at": str(row.get("DATEADDED") or ""),
        "freshness_hours": 72,
        "hot_candidate": len(domains) >= 2 or (official_present and len(domains) >= 2),
        "pool_kind": str(row.get("pool_kind") or ""),
        "avg_tone": float(row.get("AvgTone") or 0.0),
        "num_articles": int(row.get("NumArticles") or 0),
        "primary_url": str(row.get("Link_Bai_Bao") or ""),
    }


def load_existing(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Standalone GDELT technology/AI pulse")
    parser.add_argument("--output", type=Path, default=TECH_GDELT_OUTPUT)
    parser.add_argument("--web-output", type=Path, default=TECH_GDELT_WEB_OUTPUT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-bytes-billed", type=int, default=2_000_000_000)
    args = parser.parse_args()

    sql = SQL_PATH.read_text(encoding="utf-8")
    client = get_client()
    rows, meta = run_query(
        client,
        sql,
        dry_run=args.dry_run,
        maximum_bytes_billed=args.max_bytes_billed,
    )
    if args.dry_run:
        print(f"tech dry-run estimated_bytes={meta['bytes_billed'] if meta['bytes_billed'] is not None else 'unknown'}")
        return 0

    raw_rows = rows or []
    accepted_rows: list[dict[str, Any]] = []
    for row in raw_rows:
        urls = [u for u in (row.get("SourceURLs") or []) if isinstance(u, str) and u.startswith("http")]
        if urls and has_strong_ai_signal(row, urls):
            accepted_rows.append(row)
    events = [build_event(row) for row in accepted_rows]
    events = [evt for evt in events if evt["source_urls"] and evt["title"]]
    estimated_bytes_env = os.environ.get("TECH_GDELT_ESTIMATED_BYTES", "").strip()
    estimated_bytes = int(estimated_bytes_env) if estimated_bytes_env.isdigit() else None
    processed_bytes = meta.get("bytes_billed")
    payload = {
        "schema_version": TECH_GDELT_SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "query_window_hours": 72,
        "estimated_bytes": estimated_bytes,
        "processed_bytes": processed_bytes,
        "bytes_status": bytes_status(estimated_bytes, processed_bytes),
        "ran_successfully": True,
        "reused_previous_events": False,
        "fresh_event_count": len(events),
        "previous_events_age_hours": 0,
        "raw_event_count": len(raw_rows),
        "ai_filtered_event_count": len(events),
        "rejected_non_ai_count": max(0, len(raw_rows) - len(events)),
        "events": events,
    }
    if not events:
        existing = load_existing(args.output)
        if existing is not None:
            previous_generated = str(existing.get("generated_at_utc") or "").strip()
            previous_age_hours = 0.0
            if previous_generated:
                try:
                    previous_dt = datetime.fromisoformat(previous_generated.replace("Z", "+00:00"))
                    if previous_dt.tzinfo is None:
                        previous_dt = previous_dt.replace(tzinfo=timezone.utc)
                    previous_age_hours = max(0.0, (datetime.now(timezone.utc) - previous_dt.astimezone(timezone.utc)).total_seconds() / 3600.0)
                except ValueError:
                    previous_age_hours = 0.0
            existing["estimated_bytes"] = payload["estimated_bytes"]
            existing["processed_bytes"] = payload["processed_bytes"]
            existing["bytes_status"] = payload["bytes_status"]
            existing["generated_at_utc"] = payload["generated_at_utc"]
            existing["query_window_hours"] = 72
            existing["ran_successfully"] = True
            existing["reused_previous_events"] = True
            existing["fresh_event_count"] = 0
            existing["previous_events_age_hours"] = round(previous_age_hours, 2)
            existing["raw_event_count"] = payload["raw_event_count"]
            existing["ai_filtered_event_count"] = payload["ai_filtered_event_count"]
            existing["rejected_non_ai_count"] = payload["rejected_non_ai_count"]
            dump_json(args.output, existing)
            dump_json(args.web_output, existing)
            print("No fresh tech events; kept previous valid JSON and refreshed run metadata.")
            return 0
        dump_json(args.output, payload)
        dump_json(args.web_output, payload)
        print("Tech GDELT ran successfully with 0 fresh events.")
        return 0

    dump_json(args.output, payload)
    dump_json(args.web_output, payload)
    print(f"Wrote {len(events)} tech GDELT events -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
