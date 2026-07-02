#!/usr/bin/env python3
"""Offline-first tests for the standalone tech pipeline."""

from __future__ import annotations

import subprocess
import sys
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
    crawl = {
        "articles": [
            {
                "title": "OpenAI launches new coding model",
                "url": "https://example.com/openai-coding-model",
                "text": "OpenAI launches a new coding model for developer workflows and agent tooling." * 20,
                "published_at": "2026-07-01T00:00:00+00:00",
                "source": "example.com",
            },
            {
                "title": "OpenAI launches new coding model",
                "url": "https://another.com/openai-coding-model",
                "text": "Independent coverage of the same OpenAI coding model launch with extra context." * 20,
                "published_at": "2026-07-01T01:00:00+00:00",
                "source": "another.com",
            },
        ]
    }
    gdelt = {
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
                "reported_at": "2026-07-01T02:00:00+00:00",
                "freshness_hours": 72,
            }
        ]
    }
    publication = build_publication(crawl, gdelt)
    assert_true(publication["schema_version"] == TECH_PUBLICATION_SCHEMA, "schema mismatch")
    assert_true(publication["window_hours"] == 72, "window_hours mismatch")
    errs = validate_publication(publication)
    assert_true(not errs, f"publication validation errors: {errs}")


def test_hot_vs_unconfirmed_rule() -> None:
    publication = {
        "schema_version": TECH_PUBLICATION_SCHEMA,
        "window_hours": 72,
        "sections": {
            "tong_quan": [],
            "tin_nong": [
                {
                    "id": "a",
                    "headline": "Single-source story 72 gio",
                    "summary": "Trong 72 gio qua, day la cau chuyen moi tu mot nguon va can cho them xac nhan cheo.",
                    "why_it_matters": "Dien bien nay can theo doi them truoc khi xem la xu huong lon.",
                    "confirmation_label": "chua_duoc_xac_nhan_rong",
                    "source_count": 1,
                    "independent_domain_count": 1,
                    "official_source_present": False,
                    "freshness_hours": 72,
                    "links": [{"url": "https://example.com/a"}],
                }
            ],
            "model_agent_moi": [],
            "cach_dung_ai": [],
            "open_source_developer_tools": [],
            "chip_ha_tang": [],
            "robotics": [],
            "cybersecurity": [],
            "chinh_sach_cuoc_dua_toan_cau": [],
            "radar_khu_vuc": [],
            "watchlist_24_72h": [],
            "source_desk": [],
        },
    }
    errs = validate_publication(publication)
    assert_true(not errs, f"unexpected errors for unconfirmed single-source story: {errs}")


def test_mobile_layout_smoke() -> None:
    html = (ROOT / "tech" / "index.html").read_text(encoding="utf-8").lower()
    assert_true('name="viewport"' in html, "missing viewport meta")
    assert_true("@media (max-width: 700px)" in html, "missing mobile media query")
    assert_true("cong nghe &amp; ai 72h" in html or "cong nghe & ai 72h" in html, "missing 72h title")


def test_forbidden_public_terms_blocked() -> None:
    publication = {
        "schema_version": TECH_PUBLICATION_SCHEMA,
        "window_hours": 72,
        "sections": {
            "tong_quan": [],
            "tin_nong": [
                {
                    "id": "bad",
                    "headline": "Pipeline tech 24-48h",
                    "summary": "Noi dung co nhac toi GDELT va Gemini.",
                    "why_it_matters": "BigQuery va crawler van lo ra.",
                    "confirmation_label": "chua_duoc_xac_nhan_rong",
                    "source_count": 1,
                    "independent_domain_count": 1,
                    "official_source_present": False,
                    "freshness_hours": 72,
                    "links": [{"url": "https://example.com/bad"}],
                }
            ],
            "model_agent_moi": [],
            "cach_dung_ai": [],
            "open_source_developer_tools": [],
            "chip_ha_tang": [],
            "robotics": [],
            "cybersecurity": [],
            "chinh_sach_cuoc_dua_toan_cau": [],
            "radar_khu_vuc": [],
            "watchlist_24_72h": [],
            "source_desk": [],
        },
    }
    errs = validate_publication(publication)
    assert_true(any("forbidden public term found" in err for err in errs), "forbidden terms should fail")


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
    test_hot_vs_unconfirmed_rule()
    test_mobile_layout_smoke()
    test_forbidden_public_terms_blocked()
    test_forbidden_diff_guard()
    print("OK: tech pipeline tests passed")


if __name__ == "__main__":
    main()
