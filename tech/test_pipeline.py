#!/usr/bin/env python3
"""Offline-first tests for the standalone AI Frontier Radar 72h module."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("LEON_TECH_BASE_DIR", str(ROOT / "tech"))

from scripts.build_tech_publication import build_publication
from scripts.validate_tech_publication import validate as validate_publication
from tech.common import NEWS_CLEAN, PUBLICATION_JSON, PUBLICATION_SCHEMA, VALIDATION_JSON, load_json


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_validation_report_exists() -> None:
    report = load_json(VALIDATION_JSON, {})
    assert_true(bool(report), "missing tech validation report")
    assert_true(bool(report.get("sources") or []), "validation report has no sources")


def test_publication_build_smoke() -> None:
    crawl = {
        "articles": [
            {
                "title": "OpenAI phát hành model coding mới cho agent",
                "url": "https://example.com/openai-coding-model",
                "text": "OpenAI phát hành model coding mới, nhấn mạnh vào agent, tool use và quy trình lập trình nhiều bước." * 8,
                "published_at": "2026-07-05T01:00:00+00:00",
                "source": "example.com",
            },
            {
                "title": "Qwen cập nhật local multimodal stack cho nhà phát triển",
                "url": "https://example.org/qwen-local-stack",
                "text": "Qwen cập nhật local stack, hỗ trợ multimodal và đường chạy riêng cho đội kỹ thuật cần giữ dữ liệu nội bộ." * 8,
                "published_at": "2026-07-05T02:00:00+00:00",
                "source": "example.org",
            },
            {
                "title": "Repo mới giúp theo dõi LangGraph và MCP tốt hơn",
                "url": "https://github.com/example/mcp-observe",
                "text": "Một repo mới cung cấp lớp quan sát cho LangGraph, MCP và workflow automation với demo rõ ràng." * 8,
                "published_at": "2026-07-05T03:00:00+00:00",
                "source": "github.com",
            },
        ]
    }
    publication = build_publication(crawl, {"events": []})
    assert_true(publication["schema_version"] == PUBLICATION_SCHEMA, "schema mismatch")
    assert_true(publication["window_hours"] == 72, "window_hours mismatch")
    assert_true("ai_knowledge" in publication["sections"], "missing ai_knowledge section")
    assert_true("founder_ideas_for_leon" in publication["sections"], "missing founder ideas section")
    assert_true("full_link_radar" in publication["sections"], "missing full radar section")


def test_current_publication_file() -> None:
    publication = load_json(PUBLICATION_JSON, {})
    assert_true(bool(publication), "missing publication artifact")
    assert_true(publication.get("schema_version") == PUBLICATION_SCHEMA, "artifact schema mismatch")
    errs = validate_publication(publication)
    assert_true(not errs, f"artifact validation errors: {errs}")


def test_frontend_contract() -> None:
    html = (ROOT / "tech" / "index.html").read_text(encoding="utf-8").lower()
    assert_true('name="viewport"' in html, "missing viewport meta")
    assert_true("kiến thức ai nên nắm" in html, "missing vietnamese knowledge label")
    assert_true("ý tưởng có thể làm ngay cho leon" in html, "missing founder ideas label")
    assert_true("item.concept" in html, "frontend must read concept")
    assert_true("item.explain_simple" in html, "frontend must read explain_simple")
    assert_true("item.why_now" in html, "frontend must read why_now")
    assert_true("item.how_to_apply" in html, "frontend must read how_to_apply")
    assert_true("item.best_links" in html, "frontend must read best_links")
    assert_true("item.idea" in html, "frontend must read founder idea")
    assert_true("item.based_on" in html, "frontend must read based_on")
    assert_true("number(importance" in html, "frontend must compare numeric importance")
    assert_true("./data/publication.json" in html, "frontend should fetch tech/data/publication.json")
    assert_true("@media (max-width: 760px)" in html, "missing mobile layout rule")


def test_validator_rejects_bad_publication() -> None:
    bad_publication = {
        "schema_version": PUBLICATION_SCHEMA,
        "generated_at_utc": "2026-07-05T00:00:00+00:00",
        "window_hours": 72,
        "executive_summary": ["Ban tin pipeline tech 24-48h."],
        "must_read": [
            {
                "title": "Coredump generated using tool",
                "url": "https://forums.example.com/coredump",
                "source": "forums.example.com",
                "category": "tool",
                "importance": 5,
                "why_read": "Nội dung này nhắc tới GDELT và pipeline.",
                "apply_now": "Gemini và BigQuery vẫn lộ ra.",
                "tags": ["tool"],
                "source_count": 1,
                "source_type": "official",
                "published_at": "2026-07-01T00:00:00+00:00",
            }
        ] * 10,
        "sections": {
            "ai_models": [],
            "local_ai_china_ai": [],
            "ai_tools": [],
            "automation_mcp_agents": [],
            "open_source_hot": [],
            "ai_business_money": [],
            "industry_impact": [],
            "ai_knowledge": [
                {
                    "concept": "Kien thuc khong dau",
                    "explain_simple": "Thieu dau",
                    "why_now": "Thieu dau",
                    "how_to_apply": "Thieu dau",
                    "best_links": ["https://example.com/a"],
                    "source_count": 1,
                }
            ],
            "founder_ideas_for_leon": [
                {
                    "idea": "Y tuong khong dau",
                    "based_on": "Support thread",
                    "why_now": "Thieu dau",
                    "apply_now": "Thieu dau",
                    "source_count": 1,
                }
            ],
            "full_link_radar": [
                {
                    "title": f"Link {idx}",
                    "url": f"https://forums.example.com/link-{idx}",
                    "source": "forums.example.com",
                    "published_at": "",
                    "category": "tool",
                    "why_interesting": "Noi dung khong dau",
                    "use_case": "Noi dung khong dau",
                    "source_type": "official",
                    "source_count": 1,
                    "time_verified": False,
                    "tags": ["x"],
                }
                for idx in range(30)
            ],
        },
        "stats": {
            "render_checks": {
                "knowledge_fields_ready": False,
                "founder_fields_ready": False,
            }
        },
    }
    errs = validate_publication(bad_publication)
    joined = "\n".join(errs)
    assert_true("community share" in joined or "forum/community source cannot be official" in joined, "must catch community/official bug")
    assert_true("must contain Vietnamese diacritics" in joined, "must catch non-accented public text")
    assert_true("support noise cannot have importance >= 4" in joined, "must catch support noise importance")


def main() -> None:
    test_validation_report_exists()
    test_publication_build_smoke()
    test_current_publication_file()
    test_frontend_contract()
    test_validator_rejects_bad_publication()
    print("OK: AI Frontier Radar 72h tests passed")


if __name__ == "__main__":
    main()
