#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tech.common import FORBIDDEN_PUBLIC_TERMS, PUBLICATION_SCHEMA, hot_rule
from tech.publication import build_publication
from tech.validate_publication import validate
from tech.validate_sources import effective_status


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_recent_gate() -> None:
    row = {
        "validation_status": "PASS_RSS",
        "source_type": "independent_news",
        "article_samples": [
            {"extract_ok": True, "published_recent": False},
            {"extract_ok": True, "published_recent": False},
            {"extract_ok": True, "published_recent": False},
        ],
    }
    check(effective_status(row) == "NO_RECENT_CONTENT", "old articles must not pass")


def test_hot_rule() -> None:
    check(hot_rule(["independent_news", "independent_news"])[0], "two independent sources should be hot")
    check(hot_rule(["official", "independent_news"])[0], "official plus independent should be hot")
    check(not hot_rule(["official", "community"])[0], "community cannot confirm official source")
    check(not hot_rule(["community", "community"])[0], "two communities cannot be hot")


def test_publication() -> None:
    os.environ.pop("GEMINI_API_KEY", None)
    crawl = {
        "articles": [
            {
                "title": "OpenAI releases a coding model for developer workflows",
                "url": "https://example.com/ai-coding-model",
                "text": "A new artificial intelligence coding model supports developer workflow automation. " * 20,
                "published_at": "2026-07-01T00:00:00+00:00",
            },
            {
                "title": "OpenAI releases a coding model for developer workflows",
                "url": "https://another.example/ai-coding-model",
                "text": "Independent artificial intelligence coverage adds context about the coding model. " * 20,
                "published_at": "2026-07-01T01:00:00+00:00",
            },
        ]
    }
    events = {"events": []}
    publication = build_publication(crawl, events)
    check(publication["schema_version"] == PUBLICATION_SCHEMA, "schema mismatch")
    errors = validate(publication, crawl, events)
    check(not errors, f"validation errors: {errors}")
    text = str(publication).lower()
    for term in FORBIDDEN_PUBLIC_TERMS:
        check(term not in text, f"public output exposes {term}")


def test_sql_and_web() -> None:
    sql = (ROOT / "tech" / "sql" / "gdelt_tech_72h.sql").read_text(encoding="utf-8")
    check(sql.count("INTERVAL 72 HOUR") >= 3, "all GDELT partitions must use 72h")
    check("TopEvents" in sql and "LimitedDocs" in sql, "cost control CTEs missing")
    html = (ROOT / "tech" / "index.html").read_text(encoding="utf-8").lower()
    check('name="viewport"' in html, "mobile viewport missing")


def main() -> None:
    test_recent_gate()
    test_hot_rule()
    test_publication()
    test_sql_and_web()
    print("OK: tech 72h tests passed")


if __name__ == "__main__":
    main()
