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
    DigestUrlIndex,
    finalize_digest_summary,
    normalize_newsroom_brief,
    validate_newsroom_brief,
)
from scripts.newsroom_copy import soften_editor_note  # noqa: E402
from scripts.newsroom_source_match import (  # noqa: E402
    article_matches_story,
    filter_urls_for_story,
    sanitize_front_page_sources,
)


def _fixture() -> dict:
    return {
        "brief_format": NEWSROOM_BRIEF_FORMAT,
        "title": "Tổng hợp tin tức toàn cầu và Việt Nam 48 giờ",
        "editor_note": "Trong 48 giờ qua, LeonQuant ghi nhận sự dịch chuyển mạnh mẽ của dòng vốn toàn cầu.",
        "executive_briefing": {
            "title": "Tổng quan 48h",
            "content": (
                "Trong 48 giờ qua, rủi ro địa chính trị tiếp tục neo tâm lý thị trường trong khi dòng tin "
                "AI và công nghệ vốn hóa lớn duy trì mật độ phủ cao. Việt Nam nổi bật với luồng điều hành "
                "liên quan pháp lý bất động sản và ổn định vĩ mô."
            )
            * 5,
            "most_mentioned_topics": [
                {"topic": "Trung Đông", "why_mentioned": "Mật độ bài cao", "evidence_hint": "Iran/Hormuz"}
            ],
            "hottest_topics": [
                {
                    "topic": "Năng lượng vùng Vịnh",
                    "why_hot": "Ảnh hưởng giá dầu",
                    "impact": "Tăng biến động tài sản rủi ro",
                    "evidence_hint": "Nhiều nguồn quốc tế",
                }
            ],
            "emerging_signals": [{"signal": "AI capex", "why_watch": "Dẫn dắt nhóm big tech"}],
            "watch_next": ["Brent", "Lợi suất Mỹ"],
        },
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
                "subsector_briefs": [
                    {
                        "name": "Tiền tệ và lạm phát",
                        "overview": "Lạm phát và lãi suất tiếp tục là trục chính của sector.",
                        "key_points": ["CPI neo cao", "Kỳ vọng nới lỏng thận trọng"],
                        "key_story_titles": ["Bitcoin giảm áp lực quanh vùng tâm lý"],
                        "representative_sources": [],
                    }
                ],
                "story_dossiers": [
                    {
                        "rank": 1,
                        "depth_level": "deep",
                        "sub_sector": "Tiền tệ và lạm phát",
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


def _mock_articles() -> list[dict]:
    return [
        {
            "url": "https://vietnamnet.vn/ts-nguyen-si-dung-can-chuyen-tu-logic-den-bu-dat-dai-sang-logic-tai-tao-sinh-ke-2518559.html",
            "title": "TS Nguyễn Sĩ Dũng: Cần chuyển từ logic đền bù đất đai sang logic tái tạo sinh kế",
            "source": "VietnamNet",
        },
        {
            "url": "https://cnbc.com/2026/05/21/bitcoin-falls-below-70000-as-investors-rotate-to-ai-stocks.html",
            "title": "Bitcoin falls below $70,000 as investors rotate to AI stocks",
            "source": "CNBC",
        },
        {
            "url": "https://batdongsan.baoxaydung.vn/can-tho-ra-soat-go-vuong-21-du-an-bat-dong-san-theo-co-che-dac-thu-192260523141631666.htm",
            "title": "Cần Thơ rà soát, gỡ vướng 21 dự án bất động sản theo cơ chế đặc thù",
            "source": "batdongsan.baoxaydung.vn",
        },
        {
            "url": "https://tuoitre.vn/tp-hcm-tinh-chuyen-giu-mo-tien-ti-usd-hang-hai-o-lai-viet-nam-20260521153911458.htm",
            "title": "TP.HCM tính chuyển giữ mở tiền tệ USD, hàng hải ở lại Việt Nam",
            "source": "Tuổi Trẻ",
        },
    ]


def test_normalize_and_validate() -> None:
    out = normalize_newsroom_brief(_fixture())
    assert out.get("brief_format") == NEWSROOM_BRIEF_FORMAT
    assert len(out.get("sector_deep_briefs") or []) == 4
    dossier = out["sector_deep_briefs"][0]["story_dossiers"][0]
    assert out.get("executive_briefing", {}).get("content")
    assert dossier.get("sub_sector") == "Tiền tệ và lạm phát"
    assert dossier.get("why_it_matters")
    assert len(dossier.get("main_developments") or []) >= 2
    assert "LeonQuant ghi nhận" not in (out.get("editor_note") or "")
    warns = validate_newsroom_brief(out)
    assert isinstance(warns, list)
    fin = finalize_digest_summary(out, input_articles=[])
    assert fin and fin.get("sector_deep_briefs")


def test_source_match_rejects_mismatched_urls() -> None:
    articles = _mock_articles()
    index = DigestUrlIndex(articles)
    crypto_headline = "Dòng vốn dịch chuyển từ Crypto sang cổ phiếu AI"
    land_url = articles[0]["url"]
    assert not article_matches_story(
        articles[0], crypto_headline, context="Bitcoin suy yếu"
    )
    kept = filter_urls_for_story(
        [land_url, articles[1]["url"]],
        crypto_headline,
        index,
        context="Bitcoin dưới 70.000 USD",
    )
    assert articles[1]["url"] in kept
    assert land_url not in kept

    tphcm_headline = "TP.HCM đẩy nhanh tiến độ gỡ vướng 28 dự án bất động sản"
    kept2 = sanitize_front_page_sources(
        [articles[2]["url"], articles[3]["url"]],
        headline=tphcm_headline,
        index=index,
        context="Chính quyền thành phố tập trung giải quyết vướng mắc pháp lý",
    )
    assert articles[3]["url"] in kept2
    assert articles[2]["url"] not in kept2


def test_soften_editor_note() -> None:
    note = soften_editor_note("LeonQuant ghi nhận sự dịch chuyển mạnh mẽ của dòng vốn toàn cầu.")
    assert "48 giờ qua cho thấy" in note
    assert "dịch chuyển mạnh mẽ" not in note


def test_sanitize_published_content_json() -> None:
    from scripts.sanitize_newsroom_content_json import sanitize_newsroom_public_content

    payload = {
        "briefMode": "newsroom-brief",
        "editorNote": "LeonQuant ghi nhận sự dịch chuyển mạnh mẽ của dòng vốn.",
        "allArticles": _mock_articles(),
        "frontPage": [
            {
                "rank": 2,
                "title": "Dòng vốn dịch chuyển từ Crypto sang cổ phiếu AI",
                "oneSentence": "Bitcoin dưới 70.000 USD.",
                "links": [
                    {
                        "url": _mock_articles()[0]["url"],
                        "title": "Dòng vốn dịch chuyển từ Crypto sang cổ phiếu AI",
                        "host": "vietnamnet.vn",
                    }
                ],
            }
        ],
        "sectorDeepBriefs": [],
        "sourceDesk": [],
    }
    out = sanitize_newsroom_public_content(payload)
    assert "LeonQuant ghi nhận" not in (out.get("editorNote") or "")
    fp = (out.get("frontPage") or [])[0]
    assert not fp.get("links")


def test_build_newsroom_extras() -> None:
    from build_website_content import build_newsroom_web_extras

    raw = normalize_newsroom_brief(_fixture())
    extras = build_newsroom_web_extras(raw, _mock_articles())
    assert extras.get("editorNote")
    assert extras.get("executiveBriefing", {}).get("content")
    assert len(extras.get("sectorDeepBriefs") or []) == 4
    fin_sec = (extras.get("sectorDeepBriefs") or [])[0]
    if fin_sec:
        assert "subsectorBriefs" in fin_sec
        if fin_sec.get("storyDossiers"):
            assert "subSector" in fin_sec["storyDossiers"][0]
    fp = extras.get("frontPage") or []
    crypto = next((x for x in fp if "Crypto" in (x.get("title") or "")), None)
    if crypto and crypto.get("links"):
        hosts = [str(l.get("host") or "") for l in crypto["links"]]
        assert not any("vietnamnet" in h for h in hosts)


if __name__ == "__main__":
    test_normalize_and_validate()
    test_source_match_rejects_mismatched_urls()
    test_soften_editor_note()
    test_sanitize_published_content_json()
    test_build_newsroom_extras()
    print("OK: newsroom digest tests passed")
