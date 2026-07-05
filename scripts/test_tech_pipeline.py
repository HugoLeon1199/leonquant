#!/usr/bin/env python3
"""Offline-first tests for the standalone tech pipeline."""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_tech_publication import build_publication  # noqa: E402
from scripts.tech_common import PASS_STATUSES, TECH_PUBLICATION_SCHEMA  # noqa: E402
from scripts.validate_tech_publication import validate as validate_publication  # noqa: E402

FORBIDDEN_DIFF_PATHS = {
    "config/sources_seed.txt",
    "leon.py",
    "summarize_news_gemini.py",
    "build_website_content.py",
    "sql/gdelt_invest_pulse.sql",
    ".github/workflows/daily.yml",
    ".github/workflows/pulse-hourly.yml",
}


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_validation_fixture_generation() -> None:
    sources = [
        {
            "name": "Pass RSS",
            "input_url": "https://example.com/rss",
            "domain": "example.com",
            "validation_status": "PASS_RSS",
        },
        {
            "name": "Soft Pass",
            "input_url": "https://soft.example.com",
            "domain": "soft.example.com",
            "validation_status": "SOFT_PASS",
        },
    ]
    active = sum(1 for src in sources if src["validation_status"] in PASS_STATUSES)
    disabled = len(sources) - active
    assert_true(active == 1, "fixture active count mismatch")
    assert_true(disabled == 1, "fixture disabled count mismatch")


def test_publication_build_and_validate() -> None:
    now = datetime.now(timezone.utc).isoformat()
    crawl = {
        "articles": [
            {
                "title": "OpenAI launches new coding model",
                "url": "https://example.com/openai-coding-model",
                "text": "OpenAI launches a new coding model for developer workflows and agent tooling." * 20,
                "published_at": now,
                "source": "example.com",
            },
            {
                "title": "Anthropic releases agent workflow SDK",
                "url": "https://another.com/openai-coding-model",
                "text": "Anthropic releases an agent workflow SDK with model context protocol support and automation examples." * 20,
                "published_at": now,
                "source": "another.com",
            },
            {
                "title": "Qwen adds local multimodal model tools",
                "url": "https://qbitai.com/qwen-local-model",
                "text": "Qwen adds local multimodal model tools for private AI workflows and developer experiments." * 20,
                "published_at": now,
                "source": "qbitai.com",
            },
            {
                "title": "GitHub trending repo adds MCP automation demo",
                "url": "https://github.com/example/mcp-demo",
                "text": "A GitHub repository adds an MCP automation demo with agent tool use and practical developer workflow examples." * 20,
                "published_at": now,
                "source": "github.com",
            },
            {
                "title": "NVIDIA GPU inference toolkit update",
                "url": "https://developer.nvidia.com/blog/gpu-inference-toolkit",
                "text": "NVIDIA updates a GPU inference toolkit for AI model serving, automation and developer deployment." * 20,
                "published_at": now,
                "source": "developer.nvidia.com",
            },
        ]
    }
    gdelt = {
        "raw_event_count": 1,
        "ai_filtered_event_count": 1,
        "rejected_non_ai_count": 0,
        "bytes_status": "known",
        "events": [
            {
                "event_id": "123",
                "title": "NVIDIA expands GPU data center roadmap",
                "summary": "GPU, HBM and cloud server capacity stay at the center of AI infrastructure demand.",
                "source_urls": ["https://infra.example.com/nvidia", "https://market.example.com/nvidia"],
                "source_count": 2,
                "independent_domain_count": 2,
                "official_source_present": False,
                "topic_tags": ["chip_ha_tang"],
                "reported_at": now,
                "freshness_hours": 72,
            }
        ]
    }
    publication = build_publication(crawl, gdelt)
    assert_true(publication["schema_version"] == TECH_PUBLICATION_SCHEMA, "schema mismatch")
    assert_true(publication["window_hours"] == 72, "window_hours mismatch")
    assert_true(len(publication["must_read"]) >= 5, "must_read floor not enforced")
    errs = validate_publication(publication, check_external=False)
    assert_true(not errs, f"publication validation errors: {errs}")


def test_empty_must_read_guard() -> None:
    publication = {
        "schema_version": TECH_PUBLICATION_SCHEMA,
        "window_hours": 72,
        "executive_summary": ["Trong 72 giờ qua, radar giữ lại 0 bài đáng đọc nhất."],
        "must_read": [],
        "sections": {
            "ai_models": [],
            "local_ai_china_ai": [],
            "ai_tools": [],
            "automation_mcp_agents": [],
            "open_source_hot": [],
            "ai_business_money": [],
            "industry_impact": [],
            "ai_knowledge": [],
            "founder_ideas_for_leon": [],
            "full_link_radar": [{"title": "Link AI có dấu", "url": "https://example.com/a", "category": "tool", "why_interesting": "Có tín hiệu công cụ AI mới.", "use_case": "Mở link để kiểm tra nhanh.", "source_type": "independent"}],
        },
        "stats": {"curator_candidate_count": 5, "main_candidate_count": 10, "render_checks": {"knowledge_fields_ready": True, "founder_fields_ready": True}},
    }
    errs = validate_publication(publication, check_external=False)
    assert_true(any("must_read must not be empty" in err for err in errs), "empty must_read should fail")
    assert_true(any("0 bài đáng đọc" in err for err in errs), "0 bài summary should fail")


def test_mobile_layout_smoke() -> None:
    html = (ROOT / "tech" / "index.html").read_text(encoding="utf-8").lower()
    assert_true('name="viewport"' in html, "missing viewport meta")
    assert_true("@media" in html and "max-width" in html, "missing mobile media query")
    assert_true("ai frontier radar 72h" in html or "công nghệ" in html, "missing 72h title")


def test_forbidden_public_terms_blocked() -> None:
    publication = {
        "schema_version": TECH_PUBLICATION_SCHEMA,
        "window_hours": 72,
        "executive_summary": ["Pipeline tech 24-48h có GDELT và Gemini."],
        "must_read": [],
        "sections": {
            "ai_models": [],
            "local_ai_china_ai": [],
            "ai_tools": [],
            "automation_mcp_agents": [],
            "open_source_hot": [],
            "ai_business_money": [],
            "industry_impact": [],
            "ai_knowledge": [],
            "founder_ideas_for_leon": [],
            "full_link_radar": [],
        },
        "stats": {"render_checks": {"knowledge_fields_ready": False, "founder_fields_ready": False}},
    }
    errs = validate_publication(publication, check_external=False)
    assert_true(any("contains forbidden term" in err for err in errs), "forbidden terms should fail")


def test_forbidden_diff_guard() -> None:
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only"],
            cwd=ROOT,
            text=True,
        )
    except Exception:
        return
    changed = {line.strip().replace("\\", "/") for line in out.splitlines() if line.strip()}
    bad = sorted(path for path in changed if path in FORBIDDEN_DIFF_PATHS)
    assert_true(not bad, f"forbidden paths modified: {bad}")


def main() -> None:
    test_validation_fixture_generation()
    test_publication_build_and_validate()
    test_empty_must_read_guard()
    test_mobile_layout_smoke()
    test_forbidden_public_terms_blocked()
    test_forbidden_diff_guard()
    print("OK: tech pipeline tests passed")


if __name__ == "__main__":
    main()
