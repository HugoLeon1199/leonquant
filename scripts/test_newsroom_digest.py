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
    aggregate_partial_sector_candidates,
    build_digest_merge_prompt,
    finalize_digest_summary,
    find_ungrounded_entities,
    normalize_newsroom_brief,
    supplement_newsroom_from_partials,
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
            "title": "Tóm tắt tổng quan 48h",
            "sections": {
                "main_picture": "Bức tranh chính 48h qua cho thấy rủi ro địa chính trị và AI capex dẫn dắt dòng tin."
                * 3,
                "most_mentioned": "Chủ đề Trung Đông và năng lượng được nhắc nhiều nhất trên các nguồn quốc tế."
                * 3,
            },
            "representative_sources": [
                {
                    "url": "https://vietnamnet.vn/dong-von-dich-chuyen-tu-crypto-sang-co-phieu-ai-123.htm",
                    "title": "Dòng vốn dịch chuyển từ Crypto sang cổ phiếu AI",
                    "source": "vietnamnet.vn",
                }
            ],
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
                        "representative_sources": [
                            {
                                "url": "https://vietnamnet.vn/dong-von-dich-chuyen-tu-crypto-sang-co-phieu-ai-123.htm",
                                "title": "Dòng vốn dịch chuyển từ Crypto sang cổ phiếu AI",
                                "source": "vietnamnet.vn",
                            }
                        ],
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
                        "representative_sources": [
                            {
                                "url": "https://vietnamnet.vn/dong-von-dich-chuyen-tu-crypto-sang-co-phieu-ai-123.htm",
                                "title": "Dòng vốn dịch chuyển từ Crypto sang cổ phiếu AI",
                                "source": "vietnamnet.vn",
                            }
                        ],
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
    assert "để người đọc" not in (out.get("editor_note") or "").lower()
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
    from scripts.newsroom_copy import strip_newsroom_filler

    note = soften_editor_note(
        "Thị trường biến động. Bản tin này gom các nguồn để người đọc thấy rõ diễn biến."
    )
    assert "để người đọc" not in note
    assert "Thị trường biến động" in note
    cleaned = strip_newsroom_filler("X. Bản tin này gom hồ sơ để người đọc thấy rõ.")
    assert "để người đọc" not in cleaned
    assert "gom hồ sơ" not in cleaned


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
    assert str(out.get("editorNote") or "").strip()
    fp = (out.get("frontPage") or [])[0]
    assert not fp.get("links")


def test_supplement_newsroom_from_partials() -> None:
    partials = [
        {
            "summary": {
                "sector_notes": [
                    {
                        "code": "finance",
                        "name": "Kinh tế & Tài chính",
                        "sub_topics": [
                            {
                                "priority_tier": "A",
                                "headline": "Bitcoin giảm áp lực quanh vùng tâm lý",
                                "summary_hint": "Dòng tiền rút khỏi crypto.",
                                "source_urls": ["https://www.coindesk.com/markets/"],
                                "reason_selected": "Tier A trong partial.",
                            },
                            {
                                "priority_tier": "B",
                                "headline": "Fed giữ lãi suất thận trọng",
                                "summary_hint": "Thị trường chờ phát biểu.",
                                "source_urls": ["https://www.cnbc.com/fed/"],
                                "reason_selected": "Tier B liên quan lãi suất.",
                            },
                        ],
                    }
                ],
                "notable_articles": [
                    {
                        "title": "Iran đàm phán với Mỹ",
                        "url": "https://www.aljazeera.com/iran/",
                        "why_notable": "Ảnh hưởng giá dầu.",
                    }
                ],
            }
        }
    ]
    thin = {
        "brief_format": NEWSROOM_BRIEF_FORMAT,
        "front_page": [],
        "sector_deep_briefs": [
            {
                "code": "finance",
                "name": "Kinh tế & Tài chính",
                "sector_thesis": "Thị trường thận trọng.",
                "story_dossiers": [],
            }
        ],
        "watchlist_24_72h": [],
    }
    out = supplement_newsroom_from_partials(thin, partials)
    assert len(out.get("front_page") or []) >= 2
    fin = next(s for s in out["sector_deep_briefs"] if s["code"] == "finance")
    assert len(fin.get("story_dossiers") or []) >= 2
    assert aggregate_partial_sector_candidates(partials)[0]["candidates_in_partials"] == 2


def test_merge_prompt_briefing_quality_guidance() -> None:
    prompt = build_digest_merge_prompt(
        [],
        total_articles=1003,
        window_meta={"timezone": "Asia/Ho_Chi_Minh"},
        global_outline=None,
    )
    assert "Hãy học giọng văn" in prompt
    assert "bài briefing thật" in prompt
    assert "sector_thesis" in prompt
    assert "chỉ nên xuất hiện" in prompt
    assert "representative_sources[].excerpt" in prompt
    assert "Không chuỗi headline" in prompt or "không chuỗi headline" in prompt.lower()
    assert "500–10.000" not in prompt
    assert "500-10000" not in prompt
    assert "2–9 câu" not in prompt
    assert "100-500 từ" not in prompt
    assert "Không ép số câu/số chữ" in prompt
    assert "Tổng thống Mỹ Donald Trump" in prompt
    assert "Cục Dự trữ Liên bang Mỹ (Fed)" in prompt
    assert "Kevin Warsh" in prompt or "Fed / chủ tịch Fed" in prompt
    assert "SpaceX" in prompt
    assert "48h thật" in prompt or "cửa sổ 48h" in prompt
    assert "điểm sáng thu hút vốn" in prompt or "quá nông" in prompt
    assert "Main clusters" in prompt or "cụm tin chính" in prompt
    assert "hấp thụ" in prompt.lower() or "Hấp thụ dossier" in prompt


def test_merge_prompt_mentions_key_excerpt_usage_guidance() -> None:
    prompt = build_digest_merge_prompt(
        [], total_articles=1003, window_meta={"timezone": "Asia/Ho_Chi_Minh"}, global_outline=None
    )
    assert "key_excerpt" in prompt


def test_merge_prompt_mentions_front_page_criteria() -> None:
    prompt = build_digest_merge_prompt(
        [], total_articles=1003, window_meta={"timezone": "Asia/Ho_Chi_Minh"}, global_outline=None
    )
    assert "Tiêu chí tin nổi bật" in prompt
    assert "thỏa thuận" in prompt and "xauusd" in prompt.lower()


def test_aggregate_partial_candidates_keeps_key_excerpt_field() -> None:
    partials = [
        {
            "batch_index": 1,
            "summary": {
                "sector_notes": [
                    {
                        "code": "finance",
                        "sub_topics": [
                            {
                                "headline": "Fed tang lai suat",
                                "summary_hint": "Fed quyet dinh tang.",
                                "key_excerpt": "Fed tang 0.25%, theo Powell ngay 15/6.",
                                "source_urls": ["https://example.com/fed"],
                            }
                        ],
                    }
                ]
            },
        }
    ]
    out = aggregate_partial_sector_candidates(partials)
    finance_pool = next(p for p in out if p["code"] == "finance")
    assert finance_pool["candidates"][0]["key_excerpt"] == "Fed tang 0.25%, theo Powell ngay 15/6."


def test_aggregate_partial_candidates_works_when_key_excerpt_absent() -> None:
    partials = [
        {
            "batch_index": 1,
            "summary": {
                "sector_notes": [
                    {
                        "code": "finance",
                        "sub_topics": [
                            {
                                "headline": "Tin khong co key_excerpt",
                                "summary_hint": "Hint cu.",
                                "source_urls": ["https://example.com/old"],
                            }
                        ],
                    }
                ]
            },
        }
    ]
    out = aggregate_partial_sector_candidates(partials)
    finance_pool = next(p for p in out if p["code"] == "finance")
    cand = finance_pool["candidates"][0]
    assert "key_excerpt" not in cand
    assert cand["headline"] == "Tin khong co key_excerpt"
    assert cand["summary_hint"] == "Hint cu."


def test_validate_flags_ungrounded_entity_in_executive_briefing() -> None:
    corpus_blob = "Fed tang lai suat hom nay. Bitcoin tang gia manh trong phien chieu."
    summary = {
        "editor_note": "note",
        "executive_briefing": {
            "content": ("SpaceX vua hoan tat IPO va Cursor thuc hien M&A lon. " * 30),
            "representative_sources": [],
            "sections": {},
        },
        "front_page": [],
        "sector_deep_briefs": [
            {"code": c, "sector_thesis": "y" * 130, "story_dossiers": []}
            for c in ("finance", "tech", "news", "trends")
        ],
    }
    warnings = validate_newsroom_brief(summary, corpus_blob)
    hits = [w for w in warnings if "có thể hallucinate" in w]
    assert hits, f"expected a hallucination warning, got warnings: {warnings}"
    assert "SpaceX" in hits[0] and "Cursor" in hits[0]


def test_validate_no_false_positive_when_entity_in_corpus() -> None:
    corpus_blob = "SpaceX vua hoan tat IPO lon nhat lich su. Cac nha dau tu theo doi sat."
    summary = {
        "editor_note": "note",
        "executive_briefing": {
            "content": ("SpaceX vua hoan tat IPO gay chu y lon. " * 30),
            "representative_sources": [],
            "sections": {},
        },
        "front_page": [],
        "sector_deep_briefs": [
            {"code": c, "sector_thesis": "y" * 130, "story_dossiers": []}
            for c in ("finance", "tech", "news", "trends")
        ],
    }
    warnings = validate_newsroom_brief(summary, corpus_blob)
    hits = [w for w in warnings if "có thể hallucinate" in w and "SpaceX" in w]
    assert not hits, f"SpaceX is grounded in corpus, should not be flagged: {warnings}"


def test_validate_no_false_positive_when_no_corpus_blob_passed() -> None:
    # Goi validate KHONG truyen corpus_titles_blob (gia tri mac dinh "") - phai
    # khong crash va khong tu nhien bao loi hallucinate vi thieu du lieu doi chieu.
    summary = {
        "editor_note": "note",
        "executive_briefing": {
            "content": ("SpaceX vua hoan tat IPO gay chu y lon. " * 30),
            "representative_sources": [],
            "sections": {},
        },
        "front_page": [],
        "sector_deep_briefs": [
            {"code": c, "sector_thesis": "y" * 130, "story_dossiers": []}
            for c in ("finance", "tech", "news", "trends")
        ],
    }
    warnings = validate_newsroom_brief(summary)
    hits = [w for w in warnings if "có thể hallucinate" in w]
    assert not hits, f"without corpus_titles_blob, should not flag hallucination: {warnings}"


def test_validate_warns_when_front_page_empty_but_dossiers_rich() -> None:
    summary = {
        "editor_note": "note",
        "executive_briefing": {
            "content": "x" * 1600,
            "representative_sources": [{"title": "a", "url": "https://a.com"}],
            "sections": {},
        },
        "front_page": [],
        "sector_deep_briefs": [
            {
                "code": "finance",
                "sector_thesis": "y" * 900,
                "story_dossiers": [
                    {
                        "title": "t",
                        "depth_level": "major",
                        "why_it_matters": "z",
                        "main_developments": ["a", "b"],
                        "representative_sources": [{"title": "s", "url": "https://s.com"}],
                    }
                ],
            },
            *[{"code": c, "sector_thesis": "y" * 900, "story_dossiers": []} for c in ("tech", "news", "trends")],
        ],
    }
    warnings = validate_newsroom_brief(summary)
    hits = [w for w in warnings if "khả năng cao có tin đạt tiêu chí" in w]
    assert hits, f"expected front_page-empty-despite-rich-dossiers warning, got: {warnings}"


def test_validate_no_warning_when_front_page_empty_and_corpus_genuinely_thin() -> None:
    summary = {
        "editor_note": "note",
        "executive_briefing": {
            "content": "x" * 1600,
            "representative_sources": [{"title": "a", "url": "https://a.com"}],
            "sections": {},
        },
        "front_page": [],
        "sector_deep_briefs": [
            {"code": c, "sector_thesis": "y" * 900, "story_dossiers": []}
            for c in ("finance", "tech", "news", "trends")
        ],
    }
    warnings = validate_newsroom_brief(summary)
    hits = [w for w in warnings if "khả năng cao có tin đạt tiêu chí" in w]
    assert not hits, f"corpus genuinely has no dossiers, should not warn about missed front_page: {warnings}"


def test_validate_warns_when_sectors_full_but_zero_dossiers() -> None:
    summary = {
        "editor_note": "note",
        "executive_briefing": {
            "content": "x" * 1600,
            "representative_sources": [{"title": "a", "url": "https://a.com"}],
            "sections": {},
        },
        "front_page": [{"title": "t", "why_it_matters": "w", "watch_next": "n"}],
        "sector_deep_briefs": [
            {"code": c, "sector_thesis": "y" * 900, "story_dossiers": []}
            for c in ("finance", "tech", "news", "trends")
        ],
    }
    warnings = validate_newsroom_brief(summary)
    hits = [w for w in warnings if "KHÔNG sector nào có story_dossiers" in w]
    assert hits, f"expected all-sectors-empty warning, got: {warnings}"


def test_find_ungrounded_entities_direct() -> None:
    missing = find_ungrounded_entities(
        "SpaceX vua IPO va Cursor M&A gay chu y.",
        [],
        "Fed tang lai suat. Bitcoin tang gia.",
    )
    assert "SpaceX" in missing and "Cursor" in missing


def test_find_ungrounded_entities_no_false_positive_on_vietnamese_sentence_starts() -> None:
    missing = find_ungrounded_entities(
        "Trong khi đó, Điều này cho thấy Định hướng mới.", [], ""
    )
    assert missing == [], f"capitalized Vietnamese sentence-starters should not be flagged: {missing}"


def test_main_editorial_story_cluster_dedupe() -> None:
    from scripts.newsroom_main_quality import enforce_newsroom_main_editorial_quality

    raw = {
        "brief_format": NEWSROOM_BRIEF_FORMAT,
        "front_page": [
            {"rank": 1, "title": "Kevin Warsh được xem là ứng viên Fed", "source_urls": []},
            {"rank": 2, "title": "Fed chọn Kevin Warsh làm chủ tịch", "source_urls": []},
            {"rank": 3, "title": "SpaceX IPO có thể huy động vốn lớn", "source_urls": []},
            {"rank": 4, "title": "Starship và kế hoạch IPO SpaceX", "source_urls": []},
        ],
        "sector_deep_briefs": [
            {
                "code": "finance",
                "name": "Kinh tế & Tài chính",
                "sector_thesis": "Thị trường thận trọng.",
                "story_dossiers": [],
            }
        ],
    }
    out = enforce_newsroom_main_editorial_quality(raw)
    titles = [str(x.get("title") or "") for x in out.get("front_page") or []]
    assert len(titles) == 2
    assert sum("warsh" in t.lower() or "fed" in t.lower() for t in titles) == 1
    assert sum("spacex" in t.lower() or "starship" in t.lower() for t in titles) == 1


def test_main_editorial_rejects_bad_urls_and_titles() -> None:
    from scripts.newsroom_main_quality import (
        enforce_newsroom_main_editorial_quality,
        is_bad_main_editorial_title,
        is_bad_main_editorial_url,
    )

    assert is_bad_main_editorial_title("PAGE NOT FOUND")
    assert is_bad_main_editorial_title("nan")
    assert is_bad_main_editorial_url("https://example.com/category/world")
    assert is_bad_main_editorial_url("https://example.com/news/coupon-deals")

    raw = {
        "brief_format": NEWSROOM_BRIEF_FORMAT,
        "notable_articles": [
            {"title": "PAGE NOT FOUND", "url": "https://example.com/a.htm"},
            {"title": "Tin hợp lệ", "url": "https://example.com/2026/05/story-123456.htm"},
        ],
        "sector_deep_briefs": [],
    }
    out = enforce_newsroom_main_editorial_quality(raw)
    notable = out.get("notable_articles") or []
    assert len(notable) == 1
    assert notable[0]["title"] == "Tin hợp lệ"


def test_archive_link_index_unchanged() -> None:
    from build_website_content import build_newsroom_web_extras

    articles = _mock_articles() + [
        {
            "url": "https://example.com/category/world",
            "title": "PAGE NOT FOUND",
            "source": "example.com",
        }
    ]
    raw = normalize_newsroom_brief(_fixture())
    extras = build_newsroom_web_extras(raw, articles)
    archive = extras.get("articleLinkIndex") or []
    assert len(archive) == len(articles)
    render_src = (ROOT / "scripts" / "newsroom_brief_render.mjs").read_text(encoding="utf-8")
    assert "Bản tin được tổng hợp từ" in render_src
    assert "bấm vào xem chi tiết" in render_src


def test_sanitize_preserves_source_excerpt() -> None:
    from scripts.newsroom_source_match import sanitize_representative_sources

    out = sanitize_representative_sources(
        [
            {
                "url": "https://example.com/a",
                "title": "Tin A",
                "source": "example.com",
                "excerpt": "Hai câu giải thích vì sao bài này củng cố luận điểm về dòng vốn AI.",
            }
        ],
        headline="Dòng vốn AI",
        index=None,
    )
    assert len(out) == 1
    assert "củng cố luận điểm" in str(out[0].get("excerpt") or "")


def test_build_newsroom_extras() -> None:
    from build_website_content import build_newsroom_web_extras

    articles = _mock_articles()
    raw = normalize_newsroom_brief(_fixture())
    fin_src = articles[1]["url"]
    fin_sec_raw = raw["sector_deep_briefs"][0]
    for sb in fin_sec_raw.get("subsector_briefs") or []:
        if isinstance(sb, dict) and sb.get("representative_sources"):
            sb["representative_sources"][0]["url"] = fin_src
    for d in fin_sec_raw.get("story_dossiers") or []:
        if isinstance(d, dict) and d.get("representative_sources"):
            d["representative_sources"][0]["url"] = fin_src
    extras = build_newsroom_web_extras(raw, articles)
    eb_content = str((extras.get("executiveBriefing") or {}).get("content") or "")
    assert eb_content
    assert "48 giờ qua" in eb_content or "LeonQuant" not in eb_content
    assert len(extras.get("sectorDeepBriefs") or []) == 4
    fin_sec = (extras.get("sectorDeepBriefs") or [])[0]
    if fin_sec:
        assert "links" in fin_sec
        assert len(fin_sec.get("storyDossiers") or []) >= 1
        assert len(fin_sec.get("subsectorBriefs") or []) >= 1
        thesis = str(fin_sec.get("sectorThesis") or "")
        assert len(thesis) > 80
        assert "Bitcoin" in thesis or "crypto" in thesis.lower()
    fp = extras.get("frontPage") or []
    crypto = next((x for x in fp if "Crypto" in (x.get("title") or "")), None)
    if crypto and crypto.get("links"):
        hosts = [str(l.get("host") or "") for l in crypto["links"]]
        assert not any("vietnamnet" in h for h in hosts)
    assert all(item.get("links") for item in fp)


def test_sector_thesis_depth_validation() -> None:
    shallow = {
        "brief_format": NEWSROOM_BRIEF_FORMAT,
        "executive_briefing": {"content": "x" * 600, "sections": {}, "representative_sources": []},
        "front_page": [
            {
                "rank": 1,
                "title": "A",
                "one_sentence": "B",
                "why_it_matters": "C",
                "watch_next": "D",
                "source_urls": [],
            }
        ]
        * 3,
        "sector_deep_briefs": [
            {
                "code": "tech",
                "name": "Công nghệ & AI",
                "sector_thesis": "Công nghệ và AI tiếp tục là điểm sáng thu hút vốn.",
                "story_dossiers": [
                    {
                        "title": "Nvidia huy động vốn cho hạ tầng AI",
                        "why_it_matters": "Ảnh hưởng capex chip.",
                        "main_developments": ["A", "B"],
                        "representative_sources": [{"url": "https://example.com/a"}],
                    },
                    {
                        "title": "OpenAI mở rộng trung tâm dữ liệu",
                        "why_it_matters": "Kéo nhu cầu điện.",
                        "main_developments": ["C", "D"],
                        "representative_sources": [{"url": "https://example.com/b"}],
                    },
                ],
            },
            {"code": "finance", "name": "Kinh tế", "sector_thesis": "x" * 900, "story_dossiers": []},
            {"code": "news", "name": "Thời sự", "sector_thesis": "y" * 900, "story_dossiers": []},
            {"code": "trends", "name": "Xu hướng", "sector_thesis": "z" * 900, "story_dossiers": []},
        ],
    }
    warns = validate_newsroom_brief(shallow)
    joined = " ".join(warns)
    assert "quá nông/generic" in joined
    assert "chưa phản ánh cụm dossier" in joined or "Nvidia" in joined


def test_main_editorial_front_page_requires_sources_and_continuous_rank() -> None:
    from scripts.newsroom_main_quality import enforce_newsroom_main_editorial_quality

    raw = {
        "brief_format": NEWSROOM_BRIEF_FORMAT,
        "front_page": [
            {
                "rank": 2,
                "title": "Tin cÃ³ nguá»“n",
                "one_sentence": "Thá»‹ trÆ°á»ng pháº£n á»©ng vá»›i cÃ¢u chuyá»‡n cÃ³ nguá»“n rÃµ rÃ ng.",
                "why_it_matters": "CÃ¢u chuyá»‡n nÃ y áº£nh hÆ°á»Ÿng Ä‘áº¿n Ä‘á»‹nh vá»‹ tÃ i sáº£n rá»§i ro.",
                "watch_next": "Theo dÃµi lá»£i suáº¥t vÃ  dÃ²ng vá»‘n liÃªn thá»‹ trÆ°á»ng.",
                "source_urls": ["https://example.com/2026/06/story-a-123456.htm"],
            },
            {
                "rank": 8,
                "title": "Tin thiáº¿u nguá»“n",
                "one_sentence": "KhÃ´ng nÃªn cÃ²n xuáº¥t hiá»‡n trÃªn front page.",
                "why_it_matters": "Náº¿u khÃ´ng cÃ³ nguá»“n thÃ¬ khÃ´ng Ä‘á»§ chuáº©n newsroom.",
                "watch_next": "Theo dÃµi thÃªm.",
                "source_urls": [],
            },
        ],
        "sector_deep_briefs": [],
    }
    out = enforce_newsroom_main_editorial_quality(raw)
    front = out.get("front_page") or []
    assert len(front) == 1
    assert front[0]["rank"] == 1
    assert front[0]["source_urls"] == ["https://example.com/2026/06/story-a-123456.htm"]


def test_main_editorial_falls_back_executive_sources_and_drops_thin_dossiers() -> None:
    from scripts.newsroom_main_quality import enforce_newsroom_main_editorial_quality

    raw = {
        "brief_format": NEWSROOM_BRIEF_FORMAT,
        "executive_briefing": {"content": "x" * 1600, "sections": {}, "representative_sources": []},
        "front_page": [
            {
                "rank": 1,
                "title": "CÃ¢u chuyá»‡n chÃ­nh",
                "one_sentence": "DÃ²ng vá»‘n rá»i crypto Ä‘á»ƒ sang nhÃ³m AI vá»‘n hÃ³a lá»›n.",
                "why_it_matters": "Cho tháº¥y Æ°u tiÃªn tÃ i sáº£n Ä‘Ã£ Ä‘á»•i sang háº¡ táº§ng AI.",
                "watch_next": "Theo dÃµi ETF crypto vÃ  capex trung tÃ¢m dá»¯ liá»‡u.",
                "source_urls": ["https://example.com/2026/06/story-main-123456.htm"],
            }
        ],
        "sector_deep_briefs": [
            {
                "code": "tech",
                "name": "CÃ´ng nghá»‡ & AI",
                "sector_thesis": "AI capex dáº«n dÃ²ng vá»‘n.",
                "story_dossiers": [
                    {
                        "rank": 1,
                        "title": "Dossier má»ng",
                        "summary": "Chá»‰ cÃ³ má»™t Ã½ nÃªn khÃ´ng nÃªn lÃªn deep brief.",
                        "main_developments": ["Má»™t Ã½"],
                        "why_it_matters": "Ná»™i dung cÃ²n quÃ¡ má»ng.",
                        "watch_next": ["Theo dÃµi Ä‘Æ¡n hÃ ng má»›i"],
                        "representative_sources": [{"url": "https://example.com/2026/06/story-thin-123456.htm"}],
                    }
                ],
            }
        ],
    }
    out = enforce_newsroom_main_editorial_quality(raw)
    assert out.get("executive_briefing", {}).get("representative_sources")
    tech = (out.get("sector_deep_briefs") or [])[0]
    assert not tech.get("story_dossiers")
    assert out.get("watchlist_24_72h")


def test_validate_content_newsroom_quality_rules() -> None:
    from validate_content import _validate_digest_content

    payload = {
        "briefMode": "newsroom-brief",
        "mainThesis": {"thesis": "DÃ²ng vá»‘n vÃ  Ä‘á»‹a chÃ­nh trá»‹ cÃ¹ng Ä‘á»‹nh hÃ¬nh bá»©c tranh 48h."},
        "executiveBriefing": {"content": "x" * 200, "sections": {}, "links": []},
        "frontPage": [
            {
                "rank": 2,
                "title": "A",
                "oneSentence": "A",
                "whyItMatters": "A",
                "watchNext": "A",
                "links": [],
            }
        ],
        "sectorDeepBriefs": [
            {"name": "1", "sectorThesis": "x", "links": [], "storyDossiers": []},
            {"name": "2", "sectorThesis": "x", "links": [], "storyDossiers": []},
            {"name": "3", "sectorThesis": "x", "links": [], "storyDossiers": []},
            {
                "name": "4",
                "sectorThesis": "x",
                "links": [{"url": "https://example.com/a"}],
                "storyDossiers": [
                    {
                        "title": "Thin",
                        "mainDevelopments": ["Má»™t Ã½"],
                        "whyItMatters": "TrÃ¹ng",
                        "watchNext": ["TrÃ¹ng"],
                        "links": [],
                    }
                ],
            },
        ],
    }
    errs = _validate_digest_content(payload)
    joined = " ".join(errs)
    assert "executiveBriefing.links" in joined
    assert "frontPage[0]: rank must be continuous" in joined
    assert "frontPage[0]: links must contain" in joined
    assert "duplicate phrasing" in joined
    assert "need at least 2 mainDevelopments" in joined


def test_main_editorial_story_cluster_dedupe() -> None:
    from scripts.newsroom_main_quality import enforce_newsroom_main_editorial_quality

    raw = {
        "brief_format": NEWSROOM_BRIEF_FORMAT,
        "front_page": [
            {
                "rank": 1,
                "title": "Kevin Warsh được xem là ứng viên Fed",
                "one_sentence": "Bối cảnh Fed thay đổi.",
                "why_it_matters": "Bầu Fed ảnh hưởng lợi suất toàn cầu.",
                "watch_next": "Theo dõi phản ứng trái phiếu.",
                "source_urls": ["https://example.com/2026/06/warsh-a-123456.htm"],
            },
            {
                "rank": 2,
                "title": "Fed chọn Kevin Warsh làm chủ tịch",
                "one_sentence": "Kỳ vọng thị trường đổi nhịp.",
                "why_it_matters": "Kỳ vọng chính sách tiền tệ thay đổi.",
                "watch_next": "Theo dõi USD và lợi suất.",
                "source_urls": ["https://example.com/2026/06/warsh-b-123457.htm"],
            },
            {
                "rank": 3,
                "title": "SpaceX IPO có thể huy động vốn lớn",
                "one_sentence": "Nhóm vũ trụ tư nhân lại nóng lên.",
                "why_it_matters": "Thị trường sơ cấp có thể nóng lên.",
                "watch_next": "Theo dõi hồ sơ IPO và định giá.",
                "source_urls": ["https://example.com/2026/06/spacex-a-123458.htm"],
            },
            {
                "rank": 4,
                "title": "Starship và kế hoạch IPO SpaceX",
                "one_sentence": "Tiến độ thử nghiệm gắn với câu chuyện vốn hóa.",
                "why_it_matters": "Nhóm vũ trụ tư nhân thu hút vốn lớn.",
                "watch_next": "Theo dõi tiến độ thử nghiệm.",
                "source_urls": ["https://example.com/2026/06/spacex-b-123459.htm"],
            },
        ],
        "sector_deep_briefs": [
            {
                "code": "finance",
                "name": "Kinh tế & Tài chính",
                "sector_thesis": "Thị trường thận trọng.",
                "story_dossiers": [],
            }
        ],
    }
    out = enforce_newsroom_main_editorial_quality(raw)
    titles = [str(x.get("title") or "") for x in out.get("front_page") or []]
    assert len(titles) == 2
    assert sum("warsh" in t.lower() or "fed" in t.lower() for t in titles) == 1
    assert sum("spacex" in t.lower() or "starship" in t.lower() for t in titles) == 1


if __name__ == "__main__":
    test_normalize_and_validate()
    test_source_match_rejects_mismatched_urls()
    test_soften_editor_note()
    test_sanitize_published_content_json()
    test_supplement_newsroom_from_partials()
    test_merge_prompt_briefing_quality_guidance()
    test_main_editorial_story_cluster_dedupe()
    test_main_editorial_rejects_bad_urls_and_titles()
    test_main_editorial_front_page_requires_sources_and_continuous_rank()
    test_main_editorial_falls_back_executive_sources_and_drops_thin_dossiers()
    test_archive_link_index_unchanged()
    test_sanitize_preserves_source_excerpt()
    test_sector_thesis_depth_validation()
    test_build_newsroom_extras()
    test_validate_content_newsroom_quality_rules()
    test_merge_prompt_mentions_key_excerpt_usage_guidance()
    test_merge_prompt_mentions_front_page_criteria()
    test_aggregate_partial_candidates_keeps_key_excerpt_field()
    test_aggregate_partial_candidates_works_when_key_excerpt_absent()
    test_validate_flags_ungrounded_entity_in_executive_briefing()
    test_validate_no_false_positive_when_entity_in_corpus()
    test_validate_no_false_positive_when_no_corpus_blob_passed()
    test_validate_warns_when_front_page_empty_but_dossiers_rich()
    test_validate_no_warning_when_front_page_empty_and_corpus_genuinely_thin()
    test_validate_warns_when_sectors_full_but_zero_dossiers()
    test_find_ungrounded_entities_direct()
    test_find_ungrounded_entities_no_false_positive_on_vietnamese_sentence_starts()
    print("OK: newsroom digest tests passed")
