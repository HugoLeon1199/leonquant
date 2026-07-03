#!/usr/bin/env python3
"""Offline-first tests for the standalone AI Frontier Radar 72h module."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_tech_publication import build_publication
from scripts.validate_tech_publication import validate as validate_publication
from tech.common import NEWS_CLEAN, PUBLICATION_JSON, PUBLICATION_SCHEMA, VALIDATION_JSON, load_json


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_validation_report_exists() -> None:
    report = load_json(VALIDATION_JSON, {})
    assert_true(bool(report), "missing tech validation report")
    sources = report.get("sources") or []
    assert_true(bool(sources), "validation report has no sources")


def test_publication_build_and_validate() -> None:
    crawl = load_json(NEWS_CLEAN, {})
    gdelt = {"events": []}
    publication = build_publication(crawl, gdelt)
    assert_true(publication["schema_version"] == PUBLICATION_SCHEMA, "schema mismatch")
    assert_true(publication["window_hours"] == 72, "window_hours mismatch")
    assert_true(bool(publication.get("must_read")), "must_read should not be empty")
    assert_true(bool(publication["sections"]["full_link_radar"]), "full_link_radar should not be empty")
    assert_true(bool(publication["sections"]["ai_knowledge"]), "missing ai_knowledge")
    assert_true(bool(publication["sections"]["founder_ideas_for_leon"]), "missing founder ideas")


def test_current_publication_file() -> None:
    publication = load_json(PUBLICATION_JSON, {})
    assert_true(bool(publication), "missing publication artifact")
    assert_true(publication.get("schema_version") == PUBLICATION_SCHEMA, "artifact schema mismatch")
    errs = validate_publication(publication)
    assert_true(not errs, f"artifact validation errors: {errs}")


def test_frontend_labels() -> None:
    html = (ROOT / "tech" / "index.html").read_text(encoding="utf-8").lower()
    assert_true('name="viewport"' in html, "missing viewport meta")
    assert_true("ai frontier radar 72h" in html, "missing title label")
    assert_true("full link radar" in html, "missing full link radar label")
    assert_true("apply now for leon" in html, "missing apply now label")
    assert_true("./data/publication.json" in html, "frontend should fetch tech/data/publication.json")
    assert_true("@media (max-width: 760px)" in html, "missing mobile layout rule")


def test_forbidden_terms_fail() -> None:
    bad_publication = {
        "schema_version": PUBLICATION_SCHEMA,
        "generated_at_utc": "2026-07-01T00:00:00+00:00",
        "window_hours": 72,
        "executive_summary": ["Ban tin pipeline tech 24-48h."],
        "must_read": [
            {
                "title": "Pipeline tech 24-48h",
                "url": "https://example.com/bad",
                "source": "example.com",
                "category": "tool",
                "importance": "high",
                "why_read": "Noi dung nhac toi GDELT va Gemini.",
                "apply_now": "BigQuery va crawler van lo ra.",
                "tags": ["bad"],
                "source_count": 1,
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
            "ai_knowledge": [{"title": "Kien thuc", "summary": "Hop le.", "use_case": "Hop le."}],
            "founder_ideas_for_leon": [{"title": "Y tuong", "summary": "Hop le.", "next_step": "Thu nghiem nho."}],
            "full_link_radar": [
                {
                    "title": f"Link {idx}",
                    "url": f"https://example.com/link-{idx}",
                    "source": "example.com",
                    "published_at": "2026-07-01T00:00:00+00:00",
                    "category": "tool",
                    "why_interesting": "Tom tat ngan.",
                    "use_case": "Cach dung ngan.",
                    "source_count": 1,
                    "tags": ["x"],
                }
                for idx in range(30)
            ],
        },
        "stats": {"story_count": 1},
    }
    errs = validate_publication(bad_publication)
    assert_true(any("contains forbidden term" in err for err in errs), "forbidden terms should fail")


def main() -> None:
    test_validation_report_exists()
    test_publication_build_and_validate()
    test_current_publication_file()
    test_frontend_labels()
    test_forbidden_terms_fail()
    print("OK: AI Frontier Radar 72h tests passed")


if __name__ == "__main__":
    main()
