#!/usr/bin/env python3
"""Test fallback: executiveBriefing.links must never be empty when articles exist.

Regression test for the e4a7178 incident: Gemini omitted representative_sources,
front_page was also empty, and content.json shipped with executiveBriefing.links == []
which validate_content.py hard-fails on.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from build_website_content import build_newsroom_web_extras  # noqa: E402


def _make_articles(n: int) -> list[dict]:
    arts = []
    for i in range(n):
        arts.append(
            {
                "url": f"https://example-news.com/article-{i}",
                "title": f"Bai viet kinh te so {i}",
                "source": "Example News",
                "content_for_ai": "noi dung kinh te " * (50 + i * 5),
                "published_at": "2026-06-16T00:00:00Z",
            }
        )
    return arts


def test_fallback_fills_links_when_sources_and_front_page_empty() -> None:
    summary = {
        "front_page": [],
        "sector_deep_briefs": [],
        "executive_briefing": {
            "content": "Tom tat tong quan nhung thieu nguon trich dan.",
            "representative_sources": [],
            "sections": {},
        },
    }
    articles = _make_articles(25)

    extras = build_newsroom_web_extras(summary, articles)
    links = extras["executiveBriefing"]["links"]

    assert links, "executiveBriefing.links must not be empty when articles are available"
    assert 1 <= len(links) <= 2, f"expected 1-2 fallback links, got {len(links)}"
    for link in links:
        assert link.get("url"), "fallback link must have a url"


def test_no_fallback_needed_when_sources_present() -> None:
    summary = {
        "front_page": [],
        "sector_deep_briefs": [],
        "executive_briefing": {
            "content": "Tom tat day du nguon.",
            "representative_sources": [
                {"url": "https://example-news.com/article-0", "title": "Bai 0", "source": "Example News"}
            ],
            "sections": {},
        },
    }
    articles = _make_articles(5)

    extras = build_newsroom_web_extras(summary, articles)
    links = extras["executiveBriefing"]["links"]

    assert links, "links should be populated from representative_sources"
    assert links[0]["url"] == "https://example-news.com/article-0"


def test_empty_corpus_still_returns_no_crash() -> None:
    summary = {
        "front_page": [],
        "sector_deep_briefs": [],
        "executive_briefing": {
            "content": "Khong co bai viet nao.",
            "representative_sources": [],
            "sections": {},
        },
    }
    extras = build_newsroom_web_extras(summary, [])
    links = extras["executiveBriefing"]["links"]
    assert links == [], "with no articles at all, links should stay empty (no crash)"


def main() -> int:
    tests = [
        test_fallback_fills_links_when_sources_and_front_page_empty,
        test_no_fallback_needed_when_sources_present,
        test_empty_corpus_still_returns_no_crash,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL: {t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"ERROR: {t.__name__}: {type(e).__name__}: {e}")
    if failed:
        print(f"\n{failed} test(s) failed")
        return 1
    print("\nAll tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
