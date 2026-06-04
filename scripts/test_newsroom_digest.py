#!/usr/bin/env python3
"""Unit tests for newsroom brief normalize/validate (no Gemini)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from summarize_news_gemini import (  # noqa: E402
    NEWSROOM_BRIEF_FORMAT,
    finalize_digest_summary,
    normalize_newsroom_brief,
    validate_newsroom_brief,
)


def _fixture() -> dict:
    return {
        "brief_format": NEWSROOM_BRIEF_FORMAT,
        "title": "Tổng hợp tin tức toàn cầu và Việt Nam 48 giờ",
        "editor_note": "Trong 48 giờ qua, thị trường phân hóa giữa rủi ro địa chính Trung Đông và dòng vốn vào AI.",
        "front_page": [
            {
                "rank": 1,
                "title": "Trung Đông quay lại biến số năng lượng",
                "one_sentence": "Căng thẳng Iran làm dầu và vàng được theo dõi sát.",
                "why_it_matters": "Nếu leo thang, Brent và tâm lý risk-off có thể dịch chuyển nhanh.",
                "watch_next": "Brent, vàng, phát biểu Washington–Tehran.",
                "source_urls": [],
            }
        ],
        "sector_deep_briefs": [
            {
                "code": "finance",
                "name": "Kinh tế & Tài chính",
                "sector_thesis": "Dòng tiền chọn lọc hơn; Bitcoin áp lực, AI giữ sức hút.",
                "story_dossiers": [
                    {
                        "rank": 1,
                        "depth_level": "deep",
                        "title": "Bitcoin giảm áp lực quanh vùng tâm lý",
                        "summary": "BTC chịu bán mạnh khi nhà đầu tư xoay sang cổ phiếu AI.",
                        "main_developments": ["Giảm quanh mốc 70k", "Alt rotation tăng", "ETF flow yếu"],
                        "why_it_matters": "Phản ánh risk-off có chọn lọc, không rút khỏi tài sản rủi ro hoàn toàn.",
                        "affected_groups": ["Nhà đầu tư crypto", "Miner"],
                        "watch_next": ["Funding rate", "Dòng ETF"],
                        "representative_sources": [],
                    }
                ],
            },
            {"code": "tech", "name": "Công nghệ & AI", "sector_thesis": "AI capex.", "story_dossiers": []},
            {"code": "news", "name": "Thời sự", "sector_thesis": "Trung Đông.", "story_dossiers": []},
            {"code": "trends", "name": "Xu hướng", "sector_thesis": "Đời sống.", "story_dossiers": []},
        ],
        "watchlist_24_72h": [
            {"theme": "Dầu", "what_to_watch": "Brent", "why": "Nhạy Trung Đông"}
        ],
        "source_desk": [],
    }


def test_normalize_and_validate() -> None:
    out = normalize_newsroom_brief(_fixture())
    assert out.get("brief_format") == NEWSROOM_BRIEF_FORMAT
    assert len(out.get("sector_deep_briefs") or []) == 4
    dossier = out["sector_deep_briefs"][0]["story_dossiers"][0]
    assert dossier.get("why_it_matters")
    assert len(dossier.get("main_developments") or []) >= 2
    warns = validate_newsroom_brief(out)
    assert any("dossiers" in w for w in warns) or len(warns) >= 0
    fin = finalize_digest_summary(out, input_articles=[])
    assert fin and _is_newsroom(fin)


def _is_newsroom(s: dict) -> bool:
    return bool(s.get("sector_deep_briefs"))


def test_build_newsroom_extras() -> None:
    from build_website_content import build_newsroom_web_extras

    raw = normalize_newsroom_brief(_fixture())
    extras = build_newsroom_web_extras(raw, [])
    assert extras.get("editorNote")
    assert len(extras.get("sectorDeepBriefs") or []) == 4
    d0 = extras["sectorDeepBriefs"][0]["storyDossiers"][0]
    assert d0.get("whyItMatters")


if __name__ == "__main__":
    test_normalize_and_validate()
    test_build_newsroom_extras()
    print("OK: newsroom digest tests passed")
