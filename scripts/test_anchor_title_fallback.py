#!/usr/bin/env python3
"""Test anchor text fallback: title khong dich duoc phai giu nguyen ban (truncate),
khong duoc roi ve cau mau chung lap lai giua nhieu bai khac nhau.

Regression test: content.json 15/06 co 2 link KHAC NHAU cung mang title
"Dien bien kinh te quoc te dang theo doi trong 48 gio qua" - day la cau mau
chung tu _english_headline_vietnamese_stub() khi khong khop pattern hardcode.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from build_website_content import _public_display_title  # noqa: E402
from summarize_news_gemini import (  # noqa: E402
    _english_headline_vietnamese_stub,
    _vietnamese_public_headline,
)

_GENERIC_SENTENCES = (
    "Diễn biến tài chính quốc tế đáng theo dõi trong 48 giờ qua",
    "Diễn biến công nghệ quốc tế đáng theo dõi trong 48 giờ qua",
    "Diễn biến thời sự quốc tế đáng theo dõi trong 48 giờ qua",
    "Diễn biến xu hướng quốc tế đáng theo dõi trong 48 giờ qua",
)


def test_stub_returns_empty_when_unmatched() -> None:
    out = _english_headline_vietnamese_stub(
        "Some totally unmatched English headline about widgets", sector_code="finance"
    )
    assert out == "", f"expected empty string fallback, got: {out!r}"


def test_known_pattern_still_translates() -> None:
    out = _english_headline_vietnamese_stub(
        "Trump Signs Executive Order On AI Governance", sector_code="tech"
    )
    assert out, "known hardcode pattern must still translate"
    assert "Trump" in out and "AI" in out


def test_vietnamese_public_headline_keeps_original_when_unmatched() -> None:
    original = "Some totally unmatched English headline about widgets"
    out = _vietnamese_public_headline(original, sector_code="finance")
    assert out == original, f"expected original headline returned, got: {out!r}"


def test_unmatched_english_headline_keeps_original_truncated() -> None:
    title = "Some totally unmatched English headline about widgets and gadgets that is very long indeed"
    out = _public_display_title(title, sector_code="finance")
    assert out not in _GENERIC_SENTENCES, f"must not fall back to generic sentence, got: {out!r}"
    assert title.startswith(out.rstrip(".")[:20]) or out.startswith(
        title[:20]
    ), f"output should start like the original title, got: {out!r}"
    assert len(out) <= 60, f"output must be truncated to <=60 chars, got {len(out)}: {out!r}"


def test_two_different_unmatched_titles_produce_different_anchor_text() -> None:
    title_a = "Some totally unmatched English headline about widgets and gadgets indeed"
    title_b = "Another completely different unmatched English headline about gizmos"
    out_a = _public_display_title(title_a, sector_code="finance")
    out_b = _public_display_title(title_b, sector_code="tech")
    assert out_a != out_b, "two different unmatched titles must not collapse to the same anchor text"
    assert out_a not in _GENERIC_SENTENCES
    assert out_b not in _GENERIC_SENTENCES


def test_vietnamese_title_unaffected() -> None:
    title = "VN-Index giảm mạnh trong phiên chiều"
    out = _public_display_title(title, sector_code="finance")
    assert out == title, f"Vietnamese title with diacritics should pass through, got: {out!r}"


def main() -> int:
    tests = [
        test_stub_returns_empty_when_unmatched,
        test_known_pattern_still_translates,
        test_vietnamese_public_headline_keeps_original_when_unmatched,
        test_unmatched_english_headline_keeps_original_truncated,
        test_two_different_unmatched_titles_produce_different_anchor_text,
        test_vietnamese_title_unaffected,
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
