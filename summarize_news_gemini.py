import argparse
import json
import os
import re
import sys
import time
from difflib import SequenceMatcher
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from build_website_content import rebuild_content_from_digest

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT_FILE = PROJECT_DIR / "news_for_ai_clean.json"
DEFAULT_ENRICHED_FILE = PROJECT_DIR / "enriched_news.json"
DEFAULT_OUTPUT_FILE = PROJECT_DIR / "gemini_summary.json"
DEFAULT_DIGEST_OUTPUT_FILE = PROJECT_DIR / "gemini_digest_summary.json"
DEFAULT_CONTENT_FILE = PROJECT_DIR / "content.json"
DEFAULT_ENV_FILE = PROJECT_DIR / ".env"
GEMINI_GENERATE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
USER_AGENT = "LEONQuantLabsArticleFetcher/0.1 (personal research; contact: local-dev)"
DIGEST_DEFAULT_MODEL = "gemini-3.1-flash-lite"
# flash-lite family: inputTokenLimit=1_048_576, outputTokenLimit=65_536 (API v1beta).
MODEL_INPUT_TOKEN_LIMIT: dict[str, int] = {
    "gemini-3.1-flash-lite": 1_048_576,
    "gemini-2.5-flash-lite": 1_048_576,
    "gemini-2.5-flash": 1_048_576,
    "gemini-2.0-flash-lite": 1_048_576,
    "gemini-2.0-flash": 1_048_576,
}
MODEL_OUTPUT_TOKEN_LIMIT_DEFAULT = 65_536
OUTPUT_TOKEN_RESERVE = 70_000
PROMPT_TEMPLATE_TOKEN_SLACK = 12_000
# Free tier flash-lite: ~125k TPM — keep each request at ~100k input tokens.
# See https://ai.google.dev/gemini-api/docs/rate-limits
DEFAULT_MAX_INPUT_TOKENS_PER_REQUEST = 100_000
FREE_TIER_TPM_FLASH_LITE = 125_000
# 0 = use DEFAULT_MAX_INPUT_TOKENS_PER_REQUEST only (no extra TPM shrink).
DEFAULT_FREE_TPM_LIMIT = 0
MIN_REQUEST_INTERVAL_SECONDS = 60.0
MODEL_FREE_TPM_HINT: dict[str, int] = {
    "gemini-3.1-flash-lite": FREE_TIER_TPM_FLASH_LITE,
    "gemini-2.5-flash-lite": FREE_TIER_TPM_FLASH_LITE,
    "gemini-2.5-flash": 250_000,
}
# Legacy char cap (ignored when --max-input-tokens-per-request > 0 or auto).
BATCH_DIGEST_CHUNK_CHARS_DEFAULT = 0

# Gợi ý tên lĩnh vực (không bắt buộc đủ 6/10 mục — số mục = theo tin crawl).
DIGEST_FOUR_SECTORS: tuple[tuple[str, str], ...] = (
    ("finance", "Kinh tế & Tài chính"),
    ("tech", "Công nghệ & AI"),
    ("news", "Thời sự & Chính trị"),
    ("trends", "Xu hướng & Đời sống"),
)
DIGEST_SECTOR_CODES = frozenset(code for code, _ in DIGEST_FOUR_SECTORS)
DIGEST_MIN_SECTORS_FINAL = 4
# Soft hints for docs/logging only — prompts must NOT treat these as quotas.
DIGEST_SOFT_TARGET_SUB_TOPICS_PER_SECTOR = 8
DIGEST_SOFT_MAX_DISPLAY_HINT = 15
DIGEST_SOFT_NOTABLE_HINT = 8
DIGEST_SOFT_EXEC_OVERVIEW_HINT = 6
# Parser safety ceiling (không dùng trong prompt để cắt tin quan trọng).
DIGEST_PARSER_MAX_SUB_TOPICS_PER_SECTOR = 25
DIGEST_PARSER_MAX_NOTABLE = 12
DIGEST_PARSER_MAX_EXEC_BULLETS = 12
DIGEST_MAX_OUTLINE_THEMES = 18
DIGEST_MERGE_MAX_OUTPUT_TOKENS = 65_536
NEWSROOM_BRIEF_FORMAT = "newsroom-brief-v1"
DIGEST_PARSER_MAX_STORY_DOSSIERS_PER_SECTOR = 25
DIGEST_MAX_REPRESENTATIVE_SOURCES = 5
DIGEST_PARSER_MAX_FRONT_PAGE = 12
DIGEST_PARSER_MAX_WATCHLIST = 10
DIGEST_PARSER_MAX_SOURCE_DESK = 12
DIGEST_SECTOR_SUMMARY_MAX_CHARS = 2800
NEWSROOM_DEPTH_LEVELS = frozenset({"brief", "deep", "major"})


def _digest_adaptive_count_block() -> str:
    return "\n".join(
        [
            "## Số lượng adaptive (KHÔNG quota cứng)",
            "- Mỗi sector **tự quyết** số `sub_topics` theo dữ liệu. Chỉ giữ tin đạt tiêu chuẩn chất lượng.",
            "- Số lượng **thường** có thể 3–15; **có thể nhiều hơn** nếu nhiều sự kiện thật sự quan trọng, khác nhau, có ích cho người đọc.",
            f"- Gợi ý trình bày (không phải quota): ~{DIGEST_SOFT_TARGET_SUB_TOPICS_PER_SECTOR} tin/sector, "
            f"~{DIGEST_SOFT_MAX_DISPLAY_HINT} khi sector rất nóng, notable ~{DIGEST_SOFT_NOTABLE_HINT}.",
            "- **Không fill** tin yếu để đủ số. **Không cắt máy móc** tin quan trọng chỉ vì vượt gợi ý.",
            "- Nếu >15 tin chất lượng trong một sector: **gom** theo sub-cluster (chính sách, BĐS, crypto, năng lượng…) thay vì một bài một dòng vụn.",
        ]
    )


def _digest_coverage_sanity_block() -> str:
    return "\n".join(
        [
            "## Coverage sanity (không phải quota cứng)",
            "- Số lượng **không cố định**, nhưng output phải **phản ánh đúng độ giàu** của dữ liệu.",
            "- Input lớn và nhiều candidate chất lượng → mỗi sector thường nên giữ **nhiều luồng A/B khác nhau**.",
            "- Nếu một sector có nhiều candidate tier A/B **khác chủ đề** trong partials, **phải giữ đủ các luồng chính**.",
            "- **Không** co sector xuống 1–3 tin chỉ vì muốn gọn, trừ khi dữ liệu thật sự ít hoặc các tin **trùng** đã gom.",
            "- Sau merge, nếu sector <4 `sub_topics`: chỉ chấp nhận khi **không còn** candidate A/B đạt chuẩn; nếu còn trong partials → **bổ sung**.",
            "- **Gọn** = gom thông minh, không lặp, không rác — **không** hiểu gọn là ít tin.",
        ]
    )


def _digest_subcluster_block() -> str:
    return "\n".join(
        [
            "## Sub-cluster (khi sector nhiều tin chất lượng)",
            "- Gom theo cụm chủ đề (vd finance: crypto/BTC, tiền tệ VN, BĐS–hạ tầng, lạm phát–XK, vàng–năng lượng, thuế–ngân hàng).",
            "- Mỗi cụm = một `sub_topic` nếu cùng luồng; headline tổng hợp cụm, không một bài một dòng khi quá chi tiết.",
            '- Ví dụ: priority_tier A, headline "Tài sản rủi ro phân hóa: Bitcoin giảm mạnh trong khi cổ phiếu AI giữ sức hút", '
            'source_urls 2 URL (coindesk + báo AI), reason_selected giải thích phân hóa dòng vốn.',
            "- Dùng `source`, `published_at`, `region` trong payload để chọn nguồn và phân VN/quốc tế.",
        ]
    )


def _digest_source_urls_block() -> str:
    return "\n".join(
        [
            "## source_urls (1–3 URL đại diện)",
            "- Mỗi `sub_topics[]`: `source_urls` có **1–3** URL từ dữ liệu crawl; **cấm** `[]`.",
            "- Chỉ copy **nguyên văn** trường `url` của bài trong JSON đầu vào — **cấm** rút gọn, đoán slug, hoặc tạo URL mới.",
            "- URL[0] phải **khớp trực tiếp** headline chính; URL[1–2] (nếu có) đại diện thêm **cùng chủ đề/sub-cluster**.",
            "- **Cấm** URL ngẫu nhiên không liên quan headline.",
        ]
    )


def _digest_quality_criteria_block() -> str:
    return "\n".join(
        [
            "## Tiêu chuẩn giữ tin (≥3/5 mới đưa vào `sub_topics`)",
            "1. Sự kiện cụ thể: ai / làm gì / chuyện gì.",
            "2. Ảnh hưởng rõ: kinh tế, chính trị, công nghệ, xã hội, đời sống hoặc thị trường.",
            "3. Không trùng tin đã chọn (gom chủ đề trùng).",
            "4. Có URL nguồn đại diện trong dữ liệu crawl.",
            "5. Có giá trị cho người đọc — giúp hiểu bức tranh 48h.",
            "**Không giữ:** tin nhỏ chỉ để đủ số; headline giật thiếu nội dung; profile/golf/hội thao nhỏ; PR không đổi bức tranh.",
        ]
    )


def _digest_priority_tier_block() -> str:
    return "\n".join(
        [
            "## priority_tier (A/B/C)",
            '- Mỗi `sub_topics[]`: `priority_tier` = `"A"` | `"B"` | `"C"` + `summary_hint` (1 câu) + `reason_selected`.',
            '- **A**: lõi, ảnh hưởng lớn — đầu sector / có thể vào `executive_overview`.',
            '- **B**: quan trọng — nên có trong sector.',
            '- **C**: đáng biết — giữ nếu sector không quá dài; nhiều C cùng chủ đề → gom một dòng.',
            "- **Không giới hạn** số A/B nếu dữ liệu có nhiều sự kiện lớn thật.",
            "- `importance_rank`: 1 = quan trọng nhất (sau khi xếp tier).",
        ]
    )


def _digest_accuracy_and_freshness_block(*, for_merge: bool = False) -> str:
    exec_rule = (
        "- `executive_overview`: **mảng bullet adaptive** — đủ luồng quan trọng, không quota cố định. "
        "Mỗi bullet **một luồng khác** (Trung Đông/năng lượng, Ukraine, AI/chip, crypto/IPO, VN tiền tệ/thuế/BĐS, xã hội/y tế…). **Cấm** lặp ý."
        if for_merge
        else "- Outline/chunk: ghi nhận candidate; merge chọn theo chất lượng."
    )
    return "\n".join(
        [
            "## Độ chính xác (BẮT BUỘC)",
            "- **Chỉ** dùng nội dung bài crawl. **Cấm** bịa, **cấm** thêm tin ngoài JSON.",
            "- Mỗi `headline` / bullet / `summary` khớp ít nhất một bài; `source_urls[0]` là bài khớp headline chính.",
            "- Dùng `source`, `published_at`, `category`, `region` trong JSON bài viết khi chọn và mô tả.",
            "- Mâu thuẫn hoặc thiếu ngữ cảnh → `gaps_and_limits` ngắn, không đoán.",
            "- Claim lớn chưa rõ trong text: wording thận trọng (\"được đưa tin\", \"cần theo dõi\"), không khẳng định như fact chắc.",
            exec_rule,
            "- `vietnam_highlights` / `international_highlights`: đủ ý cụ thể theo mức độ quan trọng — không quota câu.",
            '- Không viết "hạ tầng ," — dùng "hạ tầng AI" / "hạ tầng dữ liệu" theo nguồn.',
            "- Tên sản phẩm/model: chỉ dùng nếu chắc trong text nguồn.",
        ]
    )


def _digest_adaptive_length_block() -> str:
    return "\n".join(
        [
            "## Độ dài biên tập (adaptive — KHÔNG quota cứng)",
            "- **Không ép số câu/số chữ.**",
            "- Độ dài do **mức độ quan trọng**, **độ phức tạp** và **số nguồn chất lượng** quyết định.",
            "- Tin nóng/quan trọng → viết đủ sâu; tin nhỏ → tóm tắt gọn.",
            "- **Không** viết dài để đủ quota; **không** viết ngắn đến mức mất ý chính.",
            "- **Viết dài hơn là tốt nếu mỗi câu thêm thông tin mới** (fact mới, góc nhìn mới, hệ quả mới). "
            "**Cấm** lặp lại ý đã nói bằng từ ngữ khác để kéo dài; cấm câu đệm không mang dữ kiện; cấm liệt kê lan man không có mạch nối.",
            "- `executive_briefing`, `sector_thesis`, dossier, excerpt: chia **đoạn văn** có mạch; độ dài tự nhiên theo pool.",
        ]
    )


def _digest_entity_clarity_block() -> str:
    return "\n".join(
        [
            "## Rõ chủ thể (Entity clarity — BẮT BUỘC cho văn bản public)",
            "Người đọc bình thường phải hiểu **ai/cái gì** ngay lần nhắc đầu — không dùng tên-viết-tắt mơ hồ nếu độc giả có thể không biết.",
            "",
            "**Quy tắc lần nhắc đầu:**",
            "- **Người:** vai trò + họ tên đầy đủ nếu có trong dữ liệu.",
            '  Ví dụ: "Tổng thống Mỹ Donald Trump" — không chỉ "Trump".',
            "- **Tổ chức/doanh nghiệp:** loại hình + tên.",
            '  Ví dụ: "công ty công nghệ FPT" hoặc "cổ phiếu công ty FPT" — không chỉ "FPT".',
            "- **Chỉ số/thị trường:** giải thích ngắn lần đầu.",
            '  Ví dụ: "VN-Index, chỉ số đại diện thị trường chứng khoán Việt Nam".',
            "- **Viết tắt:** mở rộng một lần, sau đó dùng viết tắt.",
            '  Ví dụ: "Cục Dự trữ Liên bang Mỹ (Fed)"; sau đó "Fed".',
            "- **Sự kiện nổi tiếng:** nêu tên sự kiện thật.",
            '  Ví dụ: "Ngày hội bóng đá lớn nhất hành tinh World Cup 2026" — không chỉ "ngày hội bóng đá lớn nhất hành tinh".',
            "- **Big tech/startup nổi tiếng:** thêm ngữ cảnh ngắn khi hữu ích.",
            '  Ví dụ: "SpaceX, công ty hàng không vũ trụ của Elon Musk".',
            "- **Mã cổ phiếu/ticker:** nói rõ là cổ phiếu/công ty/ngành.",
            '  Ví dụ: "cổ phiếu FPT", "nhóm cổ phiếu ngân hàng", "cổ phiếu Nvidia".',
            "",
            "**Lần nhắc sau:** có thể rút gọn (Trump, Fed, FPT…) nếu đã rõ ngữ cảnh.",
            "**Tránh:** lặp giải thích mỗi câu; ngoặc dài robot; biến bài thành từ điển.",
            "",
            "**Ví dụ SAI → ĐÚNG:**",
            '- SAI: "Trump gây sức ép lên Iran."',
            '  ĐÚNG: "Tổng thống Mỹ Donald Trump gia tăng sức ép lên Iran trong bối cảnh đàm phán hạt nhân bế tắc."',
            '- SAI: "FPT tăng mạnh."',
            '  ĐÚNG: "Cổ phiếu công ty công nghệ FPT tăng mạnh, phản ánh dòng tiền vẫn quan tâm nhóm công nghệ Việt Nam."',
            '- SAI: "Ngày hội bóng đá lớn nhất hành tinh đang nóng lên."',
            '  ĐÚNG: "Ngày hội bóng đá lớn nhất hành tinh World Cup 2026 đang trở thành câu chuyện kinh tế – truyền thông lớn, khi tài trợ, bản quyền và du lịch cùng được kích hoạt."',
            '- SAI: "Fed phát tín hiệu mới."',
            '  ĐÚNG: "Cục Dự trữ Liên bang Mỹ (Fed) phát tín hiệu mới về lãi suất, ảnh hưởng trực tiếp đến kỳ vọng thị trường tài chính toàn cầu."',
        ]
    )


def _digest_who_what_why_block() -> str:
    return "\n".join(
        [
            "## Ai – Việc gì – Vì sao (Who–What–Why)",
            "Mỗi đoạn/ý quan trọng phải làm rõ:",
            "- **Ai/cái gì** là chủ thể chính? (theo quy tắc Entity clarity ở lần nhắc đầu)",
            "- **Chuyện gì** đã xảy ra? (fact từ dữ liệu, không bịa)",
            "- **Vì sao** quan trọng — tác động tới thị trường, chính sách, công nghệ, xã hội, hoặc bối cảnh Việt Nam/toàn cầu?",
            "Không để người đọc đoán mò đối tượng hoặc mức độ quan trọng.",
        ]
    )


def _digest_main_freshness_block() -> str:
    return "\n".join(
        [
            "## Độ mới — nội dung chính Tin48h (BẮT BUỘC)",
            "- `executive_briefing`, `sector_thesis`, `story_dossiers`, `front_page`, notable: **ưu tiên bài trong cửa sổ 48h thật** (`published_at` gần nhất).",
            "- **Không** để tin cũ chiếm vị trí chính nếu cùng chủ đề đã có bài mới hơn trong input.",
            "- Bài cũ vẫn có thể nằm trong archive đầy đủ — nhưng **không** lên Tổng quan / Đi sâu ngành / Tin đáng chú ý nếu không còn relevance 48h.",
            "- Khi gom cụm (Fed, SpaceX, Iran…): chọn nguồn **mới + đại diện** nhất, không lặp cùng diễn biến nhiều lần.",
        ]
    )


def _digest_main_quality_block() -> str:
    return "\n".join(
        [
            "## Chất lượng nguồn — phần chính (BẮT BUỘC)",
            "- **Không** dùng link/tiêu đề kiểu PAGE NOT FOUND, `nan`, trang category/section rỗng, trang listing/review/coupon/promo làm story chính.",
            "- **Không** chọn thể thao/giải trí làm story chính trừ khi có tác động kinh tế, văn hóa, địa chính trị hoặc xã hội rõ.",
            "- Tin yếu/nhiễu: để archive minh bạch — **không** đưa vào notable, front page, dossier chính.",
            "- Mỗi `representative_sources` / `source_urls` phải khớp story và là bài thật từ crawl.",
        ]
    )


def _digest_story_cluster_block() -> str:
    return "\n".join(
        [
            "## Gom story — tránh lặp ở phần chính (BẮT BUỘC)",
            "Cùng một câu chuyện chỉ xuất hiện **một lần** ở output chính (có thể nhiều URL trong cùng dossier).",
            "Ví dụ phải gom, không lặp 3–5 lần:",
            "- Kevin Warsh / Fed / chủ tịch Fed → **một** cụm chính sách tiền tệ.",
            "- SpaceX / Starship / IPO SpaceX → **một** cụm.",
            "- Iran / Hormuz / đàm phán Trump–Iran → **một** hoặc tối đa **hai** cụm (quân sự vs đàm phán) — không rải rác.",
            "**Không** gom/dedupe archive đầy đủ — chỉ output biên tập chính.",
        ]
    )


def _digest_gemini_writing_rules_block() -> str:
    return "\n\n".join(
        [
            _digest_adaptive_length_block(),
            _digest_entity_clarity_block(),
            _digest_who_what_why_block(),
            _digest_main_freshness_block(),
            _digest_main_quality_block(),
            _digest_story_cluster_block(),
        ]
    )


def _digest_editorial_style_block() -> str:
    return "\n".join(
        [
            "## Văn phong xuất bản LeonQuant (BẮT BUỘC)",
            "- Viết như biên tập viên kinh tế - công nghệ cấp cao, không viết như máy tóm tắt.",
            "- Mỗi đoạn phải có thesis rõ: điều gì đang thay đổi, vì sao quan trọng, người đọc nên theo dõi biến số nào.",
            "- Tránh câu sáo rỗng: 'chứng kiến sự phân hóa mạnh mẽ', 'đặt ra thách thức', 'tiếp tục là động lực', "
            "'đang là tâm điểm', nếu không có chi tiết cụ thể đi kèm.",
            "- Ưu tiên câu cụ thể: tài sản/ngành/chính sách/công nghệ nào đang bị ảnh hưởng.",
            "- Không bê nguyên headline crawl nếu headline giật hoặc thô. Viết lại headline biên tập: ngắn, rõ actor + event + ý nghĩa.",
            "- **Headline public phải tiếng Việt** — không để headline tiếng Anh nguyên bản từ crawl.",
            "- Summary sector không được chỉ liệt kê headline. Phải nối các tin thành một câu chuyện 48h.",
            "- Mỗi `summary_hint` trả lời: vì sao tin này đáng chú ý với người đọc?",
            "- Mỗi `reason_selected` phải cụ thể — không 'tin quan trọng' / 'ảnh hưởng toàn cầu' chung chung.",
            "- **Cấm** `summary_hint`/`reason_selected` generic: "
            "'Tin này được giữ vì phản ánh một luồng đáng chú ý trong 48 giờ.' / "
            "'Được chọn vì bổ sung một góc riêng cho bức tranh 48h.'",
            "- Giọng trung lập, sắc, không hô hào, không khuyến nghị mua bán.",
        ]
    )


def _digest_headline_rewrite_block() -> str:
    return "\n".join(
        [
            "## Viết lại headline (BẮT BUỘC cho merge)",
            "Không bê headline crawl nếu: quá giật, quá dài, từ cảm xúc ('sập', 'tháo chạy', 'địa chấn', 'máy in tiền', 'hoàn hảo đến vô thực'), không rõ ý nghĩa 48h.",
            "Format: **[Actor/thị trường] + [sự kiện] + [vì sao đáng chú ý]**",
            '- Raw: "Giá vàng thế giới bất ngờ sập mạnh, nhà đầu tư tháo chạy" → '
            'Editorial: "Giá vàng giảm mạnh khi kỳ vọng rủi ro Trung Đông được định giá lại"',
            '- Raw: "Robot hình người giá chưa tới 3.000 USD gây địa chấn" → '
            'Editorial: "Robot hình người giá thấp làm nóng cuộc đua phần cứng AI"',
            '- Raw: "Loạt thương hiệu Việt lâu đời trở thành máy in tiền cho cổ đông" → '
            'Editorial: "Một số thương hiệu Việt lâu đời tiếp tục tạo dòng tiền ổn định cho cổ đông"',
            "- Raw EN: \"Google owner Alphabet to sell $80bn in stock...\" → "
            'VI: "Alphabet huy động vốn lớn để tài trợ làn sóng đầu tư AI"',
            "- Raw EN: \"Trump Says It's Time... Iran... Deal\" → "
            'VI: "Tổng thống Mỹ Donald Trump gia tăng sức ép đàm phán với Iran giữa căng thẳng vùng Vịnh"',
            "- Raw EN: \"US strikes Iran's Qeshm Island...\" → "
            'VI: "Mỹ tấn công đảo Qeshm, rủi ro Trung Đông leo thang"',
        ]
    )


def _digest_content_polish_block() -> str:
    return "\n".join(
        [
            "## Polish nội dung public (BẮT BUỘC)",
            "- Gom tin **cùng luồng** trong sector thành sub-cluster (vd. Mỹ-Iran/Qeshm/Tehran/ceasefire → tối đa **2** item: "
            '"Leo thang quân sự Mỹ–Iran quanh đảo Qeshm" + "Đàm phán Tehran bế tắc, rủi ro năng lượng còn kéo dài").',
            "- `summary_hint` / `reason_selected`: câu cụ thể theo actor/sự kiện/luồng — **không** dùng câu fallback máy.",
            "- **Không** cắt `headline[:80]` làm summary_hint; tech/AI: hint riêng (Alphabet vốn, Microsoft/OpenAI, Trump EO, robot, DPPA).",
            "- Headline **tiếng Việt** cho người đọc Việt Nam; paraphrase nếu nguồn tiếng Anh.",
            "- Bỏ tin metadata/lịch họp (vd. IMF Executive Board Calendar Archive) nếu không có phân tích.",
        ]
    )


def _digest_sector_routing_block() -> str:
    return "\n".join(
        [
            "## Routing override (BẮT BUỘC)",
            "- AI regulation / AI executive order / AI oversight / model policy → **`tech`**, không `news` (trừ khi trọng tâm chính trị thuần túy).",
            "- Phân loại theo NỘI DUNG bài viết, không theo domain nguồn: ví dụ CoinDesk đăng bài về ETF Bitcoin được SEC phê duyệt → `finance` (chủ đề tài chính/quy định); CoinDesk đăng bài về AI agent giao dịch tự động → `tech` (chủ đề công nghệ) — cùng nguồn nhưng sector khác nhau tùy nội dung.",
            "- Tuyển sinh, giáo dục, đời sống học đường → **`trends`**, không `news`.",
            "- Xăng E10: chính sách năng lượng/giá/nguồn cung → `finance` hoặc `news`; phản ứng người tiêu dùng/hướng dẫn → `trends`.",
            "- **Cả bản tin:** cùng chủ đề xăng E10 tối đa **2** lần, mỗi lần góc khác nhau.",
            "- Tin giải trí/celebrity/listicle ('ngọc nữ đẹp nhất', 'sao', 'miss') → **không** đưa vào digest trừ tác động xã hội lớn.",
            "- Blue Origin / NASA / phóng tên lửa / nhiệm vụ không gian → **`tech`** (hoặc `trends` nếu góc đời sống), không `news` trừ chính sách/chính trị thuần.",
        ]
    )


_FRONT_PAGE_HIGHLIGHT_KEYWORDS = (
    "thỏa thuận",
    "lãi suất",
    "ipo",
    "tăng trưởng gdp",
    "chiến tranh",
    "vàng",
    "xauusd",
)


def _digest_front_page_criteria_block() -> str:
    keywords_joined = ", ".join(f'"{k}"' for k in _FRONT_PAGE_HIGHLIGHT_KEYWORDS)
    return "\n".join(
        [
            "## Tiêu chí tin nổi bật (front_page) — BẮT BUỘC áp dụng",
            "Một tin được coi là nổi bật và PHẢI có mặt trong `front_page` nếu thỏa MỘT trong hai điều kiện:",
            "1. Cùng một sự kiện/chủ đề được ít nhất **3 nguồn khác nhau** (khác domain/tên cơ quan báo chí trong field `source`) đưa tin trong cửa sổ 48h — tự đối chiếu qua toàn bộ candidates/partials, không cần đếm chính xác tuyệt đối, ước lượng hợp lý là đủ.",
            f"2. Tiêu đề hoặc nội dung chính chứa một trong các từ khóa: {keywords_joined} (hoặc biến thể rõ nghĩa tương đương).",
            "Nếu sau khi rà soát có ít nhất 1 tin đạt tiêu chí trên mà KHÔNG đưa vào `front_page` — coi là lỗi, phải sửa trước khi trả JSON.",
            "Nếu rà soát toàn bộ corpus mà THẬT SỰ không có tin nào đạt tiêu chí (corpus toàn tin nhỏ/nhiễu) — có thể để `front_page` trống, nhưng đây là trường hợp hiếm; nếu corpus có ≥80 candidates mà `front_page` trống, hãy tự kiểm tra lại vì khả năng cao đã bỏ sót.",
        ]
    )


def _digest_executive_overview_editing_block() -> str:
    return _digest_executive_briefing_writing_block()


def _digest_anti_rule_leak_block() -> str:
    return "\n".join(
        [
            "## Cấm lộ rule/prompt trong văn bản public (TUYỆT ĐỐI)",
            "Mọi trường người đọc thấy (`executive_briefing`, `sector_thesis`, dossier, excerpt) phải là **tin tức/bài briefing**, không phải hướng dẫn nội bộ.",
            "**Không** viết câu kiểu quy tắc biên tập — ví dụ SAI:",
            '- "Thể thao và giải trí chỉ nên xuất hiện trong bản tin chính khi có tác động kinh tế – văn hóa rõ ràng."',
            "Viết ĐÚNG — kể câu chuyện cụ thể:",
            '- "World Cup 2026 nổi bật như một câu chuyện kinh tế – văn hóa, khi giải đấu trở thành điểm giao giữa truyền thông, tài trợ, tiêu dùng và cạnh tranh thương hiệu."',
            "**Cấm** các cụm (và biến thể gần nghĩa) trong output public:",
            "- chỉ nên xuất hiện / không nên đưa vào / nếu có tác động thì",
            "- theo rule / theo prompt / theo quy tắc / dữ liệu cho thấy lặp quá nhiều",
            "- đáng chú ý (nếu không giải thích cụ thể ngay sau đó)",
            "- diễn biến phức tạp / tác động lớn / theo dõi diễn biến tiếp trong 24–72 giờ",
            "- để người đọc thấy / bản tin này gom / người đọc cần theo dõi",
            "Khi lọc nhiễu: **im lặng bỏ tin**, không giải thích rule vì sao bỏ.",
        ]
    )


def _digest_executive_briefing_writing_block() -> str:
    return "\n".join(
        [
            "## Tổng quan 48h (`executive_briefing`) — viết như bài briefing thật",
            "Đây là **bài mở số** của trang Tin48h: editorial liền mạch, không phải outline, không phải bullet rời, không phải nhãn + một câu. UI không hiển thị danh sách nguồn riêng cho phần này — mọi nguồn quan trọng phải được dẫn chiếu tự nhiên trong văn bản hoặc qua sector/dossier phía dưới.",
            "`front_page` là danh sách tin nổi bật BẮT BUỘC phải có khi corpus đạt tiêu chí highlight (xem '## Tiêu chí tin nổi bật' phía dưới) — không được để trống chỉ vì executive_briefing đã viết đủ; hai phần này phục vụ mục đích khác nhau (executive_briefing = bài mở số liền mạch, front_page = danh sách rank để UI hiển thị khối tin nổi bật riêng).",
            "Ưu tiên `executive_briefing.content` như **thân bài chính**. Viết 3–5 đoạn có mạch: mở bức tranh, các story quyết định, tác động, rồi watchlist 24–72h.",
            "Viết **đủ ý** theo mức độ quan trọng và độ phức tạp của pools — tin lớn phân tích sâu, tin nhỏ gọn. Không ép số chữ/số câu; không viết dài để đủ quota; không viết ngắn đến mức mất ý chính.",
            "**Dài hơn là chấp nhận được và được khuyến khích** khi 48h qua có nhiều dữ kiện thật để khai triển — điều kiện bắt buộc: mỗi câu/đoạn phải mở ra một góc mới (story mới, tác động mới, biến số mới), **không** diễn đạt lại ý đã nói bằng từ khác, không thêm câu đệm cho dài.",
            "**BẮT BUỘC phủ đủ — không phải xin phép dài, mà là buộc phải đủ:** `content` phải điểm qua **từng cụm tin lớn (tier A/B)** đã được chọn vào `sector_notes`/`story_dossiers` từ mọi partial — không bỏ sót cụm nào đủ tầm vóc chỉ vì muốn viết ngắn/gọn. "
            "Nếu pools có N cụm tier A/B thật sự khác nhau, bài phải có đủ chỗ cho N góc đó (không nén N cụm thành 1-2 câu chung). "
            "**Cấm tuyệt đối** rút gọn cả bài xuống vài dòng/một đoạn ngắn khi pools giàu dữ liệu — input đã tổng hợp từ hàng trăm bài viết, output phải phản ánh đúng khối lượng đó, không phải tóm tắt-của-tóm tắt.",
            "Mỗi đoạn phải trả lời đủ **actor + event + implication**. Người đọc phải hiểu ngay: ai/cái gì, chuyện gì xảy ra, vì sao đáng quan tâm.",
            "**Cấm** mở đoạn bằng các nhãn template hoặc câu meta-biên tập như:",
            '- "Bức tranh chính là…" / "Chủ đề được nhắc nhiều nhất là…" / "Câu chuyện quan trọng nhất là…" / "Tác động theo khu vực/ngành là…"',
            '- "Phản ánh sự quan tâm của giới đầu tư" / "Đặt ra những câu hỏi" / "Tiếp tục là tâm điểm" nếu không có biến số cụ thể đi ngay sau.',
            "UI đã có heading riêng — **không** lặp nhãn mục trong thân bài; chỉ viết prose như mở bài trang nhất.",
            "Bài phải nối được:",
            "- Trục nào đang chi phối 48h qua.",
            "- Story nào thật sự quyết định tâm lý thị trường/chính sách.",
            "- Các dòng tin liên kết với nhau ra sao (cùng một bức tranh, không danh sách headline).",
            "- Tác động tới ngành/khu vực/tài sản nào.",
            "- **24–72h** tới nên theo dõi biến số gì (tên tài sản, doanh nghiệp, chính sách, sự kiện; không filler).",
            "Giữ `executive_briefing.sections` để back-compat, nhưng **không ép** phải đủ 5 mục. Chỉ điền section khi thật sự có góc riêng, không trùng ý với `content`.",
            "- `main_picture`: 1–2 đoạn mở bức tranh chung 48h, nếu cần.",
            "- `most_mentioned`: chỉ dùng khi lượng nhắc đến là dữ kiện đáng kể, không phải đổi nhãn cho cùng một story.",
            "- `top_stories`: chỉ dùng khi có 1–2 câu chuyện cần tách riêng, không lặp nội dung mở bài.",
            "- `sector_impacts`: chỉ dùng khi có tác động liên ngành rõ ràng.",
            "- `watch_24_72h`: ưu tiên bullet/đoạn **cụ thể**, nêu biến số, mốc, actor.",
            "Nếu `content` đã đủ sạch và đầy, `sections` có thể để rất mỏng hoặc bỏ trống phần không cần thiết.",
            "Gom chủ đề trùng: Trung Đông/Iran/Hormuz → **một** luồng; AI/chip/capex → **một**; VN BĐS/hạ tầng/thuế → **một**.",
            "Ví dụ hướng viết đúng cho `content`: mở ngay bằng 1-2 trục chính của 48h, đoạn sau đi vào story lớn, đoạn tiếp nêu tác động tới Việt Nam/tài sản, rồi chốt bằng 3-5 watchpoints cụ thể.",
        ]
    )


def _digest_sector_narrative_block() -> str:
    return "\n".join(
        [
            "## Đi sâu theo từng ngành (`sector_thesis`) — bài tóm tắt ngành đủ sâu theo dữ liệu",
            "Mỗi `sector_thesis` là **một mini analyst note** (nhiều đoạn), không nối summary dossier rời rạc.",
            "**Không ép số câu/số chữ.** Ngành nhiều tin nóng → viết dài và sâu; ngành ít tin → gọn nhưng **không** mất ý chính.",
            "**Viết dài là tốt nếu mỗi đoạn mở ra một góc mới** (cụm tin mới, tác động mới, biến số mới) — **cấm** lặp lại ý đã nói ở đoạn trước bằng cách diễn đạt khác, cấm câu đệm/transition không mang dữ kiện.",
            "Không padding; không rút gọn đến mức chỉ còn một câu sáo; không biến thành chuỗi headline cùng tag.",
            "- Khi viết `sector_thesis`, đối chiếu `key_excerpt` của các candidate tier A/B trong sector (không chỉ headline) để lấy dữ kiện cụ thể (số liệu, tên, trích dẫn) làm dày mỗi đoạn — đây là nguồn dữ kiện CHI TIẾT NHẤT bạn có được, vì bạn không đọc lại text gốc của bài báo.",
            "",
            "Form ưu tiên:",
            "- Đoạn 1: thesis của ngành trong 48h qua — ngành này đang đổi hướng ở đâu.",
            "- Đoạn 2–3: 1–3 cụm story chính, mỗi cụm phải có actor + event + implication.",
            "- Đoạn cuối: tác động thực tế + 2–4 biến số cần theo dõi 24–72h tới.",
            "",
            "**Các lớp cần phủ khi dữ liệu có (trong prose liền mạch, không heading robot):**",
            "- **Sector thesis:** ngành này 48h qua nổi bật vì điều gì.",
            "- **Main clusters:** các cụm tin chính — gom theo chủ đề, không liệt kê headline rời.",
            "- **Who–What–Why:** ai/cái gì, chuyện gì xảy ra, vì sao quan trọng.",
            "- **Impact:** tác động tới thị trường, chính sách, doanh nghiệp, người tiêu dùng, Việt Nam/toàn cầu.",
            "- **Watch next:** biến số cần theo dõi **24–72h** tới (cụ thể, không filler).",
            "",
            "**Tổng hợp, không liệt kê:**",
            '- **Không:** "Tin A xảy ra. Tin B xảy ra. Tin C xảy ra."',
            '- **Viết:** "Các tin A, B, C cùng cho thấy…" / "Điểm chung là…" / "Rủi ro nằm ở…" / "Biến số tiếp theo là…"',
            '- **Không:** "Ngành này tiếp tục là điểm sáng/đang thu hút sự chú ý/mang lại nhiều cơ hội và thách thức."',
            "",
            "**Ví dụ SAI (quá nông):**",
            '"Công nghệ và AI tiếp tục là điểm sáng thu hút vốn."',
            "",
            "**Ví dụ ĐÚNG (đủ chiều sâu):**",
            '"Công nghệ và AI trong 48 giờ qua không chỉ nổi bật ở câu chuyện cổ phiếu công nghệ, '
            "mà còn ở hạ tầng dữ liệu, bán dẫn, trung tâm dữ liệu và ứng dụng AI trong tài chính – sản xuất. "
            "Các bài liên quan đến Nvidia, OpenAI, SpaceX hoặc doanh nghiệp công nghệ Việt Nam cần được nối "
            'thành một bức tranh về dòng vốn, năng lực tính toán và cạnh tranh hạ tầng."',
            "",
            "**Ví dụ SAI (dài nhưng lặp ý dưới dạng diễn đạt khác — không chấp nhận):**",
            '"Ngành công nghệ đang thu hút nhiều sự quan tâm. Có thể thấy công nghệ là lĩnh vực được chú ý nhiều trong 48h qua. '
            'Điều này cho thấy công nghệ tiếp tục là tâm điểm của thị trường."',
            "",
            "**Ví dụ ĐÚNG (dài vì mỗi câu mở góc mới, không lặp):**",
            '"Công nghệ và AI 48h qua nổi bật ở hạ tầng dữ liệu và bán dẫn, không chỉ ở cổ phiếu. '
            "Nvidia và các nhà cung cấp chip tiếp tục mở rộng công suất để đáp ứng nhu cầu trung tâm dữ liệu, "
            "trong khi OpenAI công bố hợp tác mới với doanh nghiệp tài chính — cho thấy AI đang chuyển từ giai đoạn "
            'thử nghiệm sang triển khai thực tế trong vận hành."',
            "",
            "**Hấp thụ dossier/subsector:**",
            "- Nếu sector có nhiều `story_dossiers` hoặc `subsector_briefs` chất lượng, `sector_thesis` **phải** tổng hợp đủ ý chính từng cụm.",
            "- **Không** bỏ qua dossier A/B chỉ vì muốn gọn; **không** lặp nguyên văn dossier.",
            "Link nguồn (`representative_sources` / pools) đặt **sau** khi đã viết xong thân bài — thân bài không được đọc như chuỗi excerpt hay danh sách nguồn.",
            "Không lặp nguyên văn `executive_briefing`; đi sâu hơn vào ngành đó.",
            "Ví dụ hướng viết đúng: mở bằng thesis ngành, sau đó nối 2-3 story chính thành một narrative, cuối cùng chốt tác động tới Việt Nam/tài sản/doanh nghiệp và watchlist cụ thể.",
        ]
    )


def _digest_source_excerpt_rules_block() -> str:
    return "\n".join(
        [
            "## Trích yếu nguồn (`representative_sources[].excerpt`)",
            "Mỗi nguồn tiêu biểu kèm `excerpt` (trích yếu biên tập, **không** copy máy summary RSS):",
            "- Độ dài **adaptive**: đủ ý theo mức quan trọng của nguồn — không quota câu/chữ.",
            "- Nói rõ bài đó **củng cố luận điểm nào** trong đoạn ngành/dossier gần nhất.",
            "- Dùng fact từ input; không bịa; không lặp nguyên headline.",
            "- Không viết \"bài này đáng chú ý\" chung chung — phải chỉ ra ý cụ thể.",
            "- Nếu candidate tương ứng đã có `key_excerpt` trong pools, dùng nó làm nền viết `excerpt` (diễn giải lại cho mượt, không copy nguyên văn) thay vì tự bịa.",
        ]
    )


def _digest_newsroom_prose_example_block() -> str:
    return "\n".join(
        [
            "## Mẫu văn (học giọng và cách nối ý — KHÔNG copy dữ liệu nếu input khác)",
            "Hãy học giọng văn và cách nối ý của mẫu dưới đây, nhưng không copy dữ liệu nếu input khác.",
            "Viết như biên tập viên đang tổng hợp 48h tin tức, không viết như nối các summary rời rạc.",
            "",
            "### Tổng quan 48h (mẫu)",
            "",
            "Trong 48 giờ qua, dòng tin nổi bật không nằm ở một sự kiện đơn lẻ, mà ở sự dịch chuyển đồng thời của ba trục lớn: thị trường tài sản rủi ro thận trọng hơn, công nghệ AI tiếp tục hút vốn, và chính sách tại Việt Nam bước vào giai đoạn cụ thể hóa mạnh hơn. Crypto, vàng, AI, bán dẫn, tài sản số, hạ tầng và năng lượng cùng xuất hiện dày đặc, cho thấy thị trường đang vừa phòng thủ trước biến động ngắn hạn, vừa tìm kiếm các câu chuyện tăng trưởng có nền tảng dài hạn.",
            "",
            "Ở lớp thị trường, Bitcoin và nhóm tài sản số được nhắc nhiều vì đang chịu áp lực điều chỉnh sau giai đoạn tăng mạnh. Điều đáng chú ý không chỉ là giá giảm, mà là cách dòng tiền đang được tái định vị: rời khỏi các tài sản mang tính đầu cơ cao và hướng sang những lĩnh vực có câu chuyện thực hơn như AI, bán dẫn, trung tâm dữ liệu và hạ tầng năng lượng. Đây là tín hiệu cho thấy khẩu vị rủi ro đang thay đổi.",
            "",
            "Tại Việt Nam, nhóm tin quan trọng xoay quanh việc hoàn thiện hành lang pháp lý cho tài sản số, siết tiêu chí doanh nghiệp tham gia thị trường tài sản mã hóa, thúc đẩy trung tâm tài chính quốc tế, tháo gỡ điểm nghẽn bất động sản và đẩy nhanh hạ tầng. Các tin này cùng cho thấy chính sách đang chuyển từ giai đoạn định hướng sang giai đoạn thiết kế luật chơi.",
            "",
            "Trong công nghệ, AI không còn chỉ là câu chuyện ứng dụng phần mềm. Các bài viết nổi bật cho thấy AI đang kéo theo nhu cầu về bán dẫn, dữ liệu, trung tâm dữ liệu, năng lực lưu trữ và khả năng triển khai trong ngân hàng, tài chính, sản xuất và dịch vụ.",
            "",
            "Trong 24–72 giờ tới, các biến số cần theo dõi gồm: phản ứng của thị trường với Bitcoin và tài sản số; diễn biến giá vàng trong nước so với thế giới; các văn bản cụ thể về tài sản mã hóa tại Việt Nam; tiến độ các dự án hạ tầng; và dòng tin mới về AI, bán dẫn, dữ liệu và trung tâm tài chính.",
            "",
            "### Đi sâu theo từng ngành (mẫu — Kinh tế & Tài chính, rút gọn)",
            "",
            "Kinh tế & Tài chính trong 48 giờ qua nổi bật bởi bốn nhóm tín hiệu: tài sản số chịu áp lực, giá vàng điều chỉnh, nhập siêu tăng mạnh và chính sách tài chính trong nước bước vào giai đoạn rõ nét hơn. Điểm đáng chú ý là các tín hiệu này không tách rời nhau. Chúng cùng phản ánh một thị trường đang đánh giá lại rủi ro, dòng vốn và kỳ vọng chính sách.",
            "",
            "Với tài sản số, câu chuyện không chỉ là Bitcoin giảm giá. Điều quan trọng hơn là tâm lý thị trường đang thay đổi: dòng tiền có dấu hiệu rời khỏi các tài sản mang tính đầu cơ cao và tìm đến các lĩnh vực có nền tảng tăng trưởng thực tế hơn. Trong bối cảnh Việt Nam cũng đang đẩy nhanh khung pháp lý cho tài sản số, chủ đề này trở thành giao điểm giữa thị trường toàn cầu và chính sách tài chính trong nước.",
        ]
    )


def _digest_editorial_selection_block(*, for_merge: bool) -> str:
    if for_merge:
        return "\n".join(
            [
                "## Biên tập merge (adaptive)",
                "Bạn là **tổng biên tập** bản tin 48h LeonQuant — khách quan theo dữ liệu crawl.",
                "**Không có số lượng cố định** cho mỗi sector. Số tin do **chất lượng và ý nghĩa** quyết định.",
                "Nhiều tin lớn thật → giữ nhiều (tổ chức theo cụm). Ít tin lớn → giữ ít.",
                "**Tuyệt đối không fill** tin yếu. **Không cắt** tin A/B quan trọng chỉ vì muốn gọn.",
                "Ưu tiên: chất lượng, độ chính xác, ý nghĩa, tính đại diện bức tranh 48h.",
                f"`reading_time_minutes`: `\"auto\"` hoặc ước lượng theo độ dài thực tế.",
            ]
        )
    return "\n".join(
        [
            "## Ghi nhận nội bộ (chunk/outline)",
            "- Chunk: ghi **candidate** đạt tiêu chuẩn — **không** ép số lượng; có thể nhiều hoặc ít tùy phần.",
            f"- Outline: tối đa {DIGEST_MAX_OUTLINE_THEMES} theme — bản đồ chủ đề, không khẳng định từ title đơn.",
        ]
    )


def _digest_four_sector_rules_block(*, for_merge: bool = False) -> str:
    sector_lines = "\n".join(
        f'   - `"{code}"` — {label}' for code, label in DIGEST_FOUR_SECTORS
    )
    lines = [
        "## Phân loại 4 chuyên mục (BẮT BUỘC)",
        "- Mỗi bài / mỗi ý tin phải thuộc **ĐÚNG MỘT** trong 4 mã (mã chỉ dùng nội bộ JSON; public hiển thị tên tiếng Việt).",
        sector_lines,
        '- `finance`: kinh tế, tài chính, chứng khoán, bất động sản, tiền ảo.',
        '- `tech`: công nghệ, AI, khoa học, bán dẫn, viễn thông.',
        '- `news`: thời sự, chính trị, ngoại giao, sự kiện quốc tế, địa chính trị.',
        '- `trends`: xu hướng, đời sống, quan điểm, góc nhìn, văn hóa, thể thao, y tế, môi trường, pháp luật/xã hội không thuần chính trị.',
        "- **Không** tạo sector ngoài 4 mã; **không** gộp hết vào finance/tech.",
        "- **Tổng hợp** (không liệt kê từng bài); mỗi `sub_topics[]`: headline + `source_urls` (1–3 URL).",
        "- Gom tin trùng chủ đề; không chọn chỉ vì headline giật.",
        _digest_source_urls_block(),
        _digest_adaptive_count_block(),
        _digest_quality_criteria_block(),
        _digest_priority_tier_block(),
        _digest_subcluster_block(),
        _digest_editorial_selection_block(for_merge=for_merge),
        _digest_accuracy_and_freshness_block(for_merge=for_merge),
    ]
    if for_merge:
        lines.extend(
            [
                "- **`sectors`:** đúng **4** phần tử (finance, tech, news, trends).",
                "- `notable_articles`: tier A/B đa ngành — số lượng adaptive theo chất lượng pools (không quota cố định).",
                _digest_editorial_style_block(),
                _digest_headline_rewrite_block(),
                _digest_sector_routing_block(),
                _digest_content_polish_block(),
                _digest_executive_briefing_writing_block(),
                _digest_gemini_writing_rules_block(),
                _digest_anti_rule_leak_block(),
                _digest_coverage_sanity_block(),
                _digest_sector_summary_rules_block(for_merge=True),
            ]
        )
    else:
        lines.extend(
            [
                f"- Outline: gắn theme với 1 trong 4 mã; tối đa {DIGEST_MAX_OUTLINE_THEMES} theme.",
                "- Chunk: `sector_notes` đủ 4 mã; candidate theo chất lượng (không quota).",
            ]
        )
    return "\n".join(lines)


def _digest_sector_summary_rules_block(*, for_merge: bool = False) -> str:
    lines = [
        "## Đoạn ngành (`sector_thesis`)",
        "- Chỉ dùng candidates/pools đã crawl; **không bịa** actor, số liệu, hay sự kiện.",
        "- Viết **bài tóm tắt ngành** nhiều đoạn — **không cap** độ dài; pool dày / nhiều dossier → viết dài và đủ lớp (thesis, clusters, Who–What–Why, impact, watch next).",
        "- Gom luồng A/B thành **câu chuyện liền mạch**; không chuỗi headline, không nối dossier summary rời.",
        "- `sector_thesis` phải **hấp thụ** các cụm trong `story_dossiers`/`subsector_briefs` cùng sector — không bỏ cụm quan trọng vì muốn ngắn.",
    ]
    if for_merge:
        lines.append(_digest_sector_narrative_block())
    else:
        lines.append(
            "- Partial: `sector_notes[].summary` ghi **luồng + mối liên hệ** trong chunk (nháp cho merge), không cắt vì sợ dài."
        )
    return "\n".join(lines)


def _is_newsroom_brief(summary: dict[str, Any]) -> bool:
    if not isinstance(summary, dict):
        return False
    if str(summary.get("brief_format") or "").strip() == NEWSROOM_BRIEF_FORMAT:
        return True
    sdb = summary.get("sector_deep_briefs")
    return isinstance(sdb, list) and len(sdb) >= 1


def _digest_newsroom_voice_block() -> str:
    return "\n".join(
        [
            "## Vai trò — Tổng biên tập Daily Intelligence Briefing",
            "Bạn là Tổng biên tập cấp cao kiêm News Intelligence Analyst cho Tin48h của LeonQuant.",
            "Bạn không tóm tắt từng bài báo riêng lẻ; bạn đọc toàn bộ dữ liệu 48h để phát hiện chủ đề được nhắc nhiều, chủ đề nóng thật sự, tín hiệu mới, bên bị ảnh hưởng, và nhiễu.",
            "Gemini là não biên tập: tự quyết phân tích, chọn tin nóng, phân ngành con, mức độ ưu tiên; không viết kiểu template chung chung.",
            "Python phía sau chỉ làm hygiene/whitelist/normalize/validate/render; vì vậy output phải thể hiện tư duy biên tập thực chất.",
            "Viết tiếng Việt chuyên nghiệp, rõ ràng, có chiều sâu; phục vụ người đọc bận cần nắm bức tranh 48h trong 10–20 phút.",
            _digest_editorial_style_block(),
            "## Nguyên tắc dữ liệu bắt buộc",
            "- Chỉ dùng JSON đầu vào; không mở web, không thêm sự kiện ngoài dữ liệu.",
            "- Không bịa số liệu/nguyên nhân/kết quả/tổ chức/con người.",
            "- Mọi link nguồn phải lấy nguyên văn từ input; không tạo URL mới.",
            "- Nếu dữ liệu chưa chắc, dùng wording thận trọng.",
            "## Nguyên tắc biên tập",
            "- Phân biệt rõ `most_mentioned_topics` (được nhắc nhiều) và `hottest_topics` (nóng theo impact/recency/source diversity).",
            "- Không nhầm nhiều bài với nóng thật; nhiều bài nhưng một domain không đủ gọi là nóng toàn cục.",
            "- Lọc nhiễu: coupon/promo/listing/review vụn/giải trí nhẹ/thể thao trận đơn lẻ không lên vị trí chính.",
            "- Mỗi nhận định lớn phải có `representative_sources` URL thật từ input; không URL → không claim lớn.",
            "- Trước khi viết tên riêng/công ty/sự kiện trong `executive_briefing.content` hay `sector_thesis`, tự kiểm tra: tên đó có xuất hiện (nguyên văn hoặc biến thể gần) trong title/text của ít nhất 1 bài trong input không? Nếu không chắc — BỎ tên đó, diễn đạt chung hơn, KHÔNG đoán.",
            "- **Không** tạo section UI “Điểm nóng”: tích hợp điểm nóng vào `executive_briefing.sections` và `sector_deep_briefs`.",
            "- `front_page` BẮT BUỘC có khi có tin đạt tiêu chí highlight (xem '## Tiêu chí tin nổi bật' dưới đây) — không bỏ trống chỉ vì đã có executive_briefing/sector_thesis.",
            _digest_front_page_criteria_block(),
            "- `front_page` / `notable_articles` / `story_dossiers` public phải Việt hoá tiêu đề tự nhiên; không để raw English headline lên output nếu đã có cách viết Việt tốt hơn.",
            "- Mọi prose public (`editor_note`, `executive_briefing`, `sector_thesis`, `summary`, `why_it_matters`, `watch_next`) phải viết bằng tiếng Việt tự nhiên; chỉ giữ nguyên tên riêng, ticker, tên công ty, tên chương trình hay thuật ngữ bắt buộc.",
            "- Viết **prose có mạch** — không outline, không nhãn + một câu, không danh sách tin rời.",
            _digest_anti_rule_leak_block(),
        ]
    )


def _digest_story_dossier_rules_block() -> str:
    return "\n".join(
        [
            "## Story dossier (cụm tin — nội bộ, không thay `sector_thesis`)",
            "Dossier bổ sung chi tiết từng cụm; **thân bài ngành** vẫn là `sector_thesis` viết mạch.",
            "- `title`: tiêu đề biên tập (tiếng Việt, không giật).",
            "- `summary`: **2–5 câu hoàn chỉnh, nối ý thành đoạn văn** (không phải một headline, không phải excerpt copy từ bài crawl) — "
            "đây là đoạn hiển thị công khai phía trên danh sách nguồn, phải tự đứng được mà không cần đọc thêm: nêu chuyện gì xảy ra, "
            "ai/cái gì liên quan, vì sao đáng chú ý. Mỗi câu phải có ý mới, không lặp.",
            "- `main_developments`: các ý chính từ nhiều bài cùng cụm (thứ tự logic) — đủ ý theo độ phức tạp, không quota số ý.",
            "- Khi candidate có sẵn `key_excerpt` (từ pools): DÙNG nó — không chỉ `headline`/`summary_hint` — làm nguyên liệu chính viết `summary`/`main_developments`/`why_it_matters`; đây là dữ kiện cụ thể nhất bạn có, KHÔNG đọc lại text gốc nên PHẢI khai thác triệt để field này.",
            "- `why_it_matters`: tác động cụ thể — đủ sâu theo `depth_level` và dữ liệu.",
            "- `affected_groups`: mảng ngắn (nhóm/tài sản/ngành/quốc gia).",
            "- `watch_next`: biến số **24–72h** cụ thể (tên, không filler).",
            "- `representative_sources`: **1–5** object `{title, source, url, excerpt}` — URL từ crawl; `excerpt` theo quy tắc trích yếu.",
            "- `depth_level`: `brief` | `deep` | `major`.",
            _digest_source_excerpt_rules_block(),
        ]
    )


def _digest_newsroom_json_schema_fragment() -> str:
    subsector = """        {
          "name": "Tên ngành con do Gemini tự chọn",
          "overview": "Tổng quan ngành con 48h — đủ ý từ dữ liệu, không cap độ dài.",
          "key_points": ["ý chính 1", "ý chính 2"],
          "key_story_titles": ["Tên story dossier liên quan"],
          "representative_sources": [
            {"title": "...", "source": "...", "url": "https://url-that-tu-crawl", "excerpt": "Trích yếu adaptive: bài này củng cố luận điểm gì trong ngành/dossier."}
          ]
        }"""
    sector_blocks = []
    dossier = """        {
          "rank": 1,
          "depth_level": "deep",
          "sub_sector": "Tên ngành con do Gemini tự chọn",
          "title": "Tiêu đề biên tập",
          "summary": "Tóm tắt cụm — rõ ai/việc gì/vì sao.",
          "main_developments": ["ý 1", "ý 2", "ý 3"],
          "why_it_matters": "Tác động — đủ sâu theo depth_level và dữ liệu.",
          "affected_groups": ["...", "..."],
          "watch_next": ["...", "..."],
          "representative_sources": [
            {"title": "...", "source": "...", "url": "https://url-that-tu-crawl", "excerpt": "Trích yếu adaptive — biên tập, không copy RSS."}
          ]
        }"""
    for code, label in DIGEST_FOUR_SECTORS:
        sector_blocks.append(
            f"""    {{
      "code": "{code}",
      "name": "{label}",
      "sector_thesis": "Bài tóm tắt ngành nhiều đoạn: mở thesis → tin chính liên kết → tác động/theo dõi. Không chuỗi headline.",
      "subsector_briefs": [
{subsector}
      ],
      "story_dossiers": [
{dossier}
      ]
    }}"""
        )
    sectors_joined = ",\n".join(sector_blocks)
    return f"""{{
  "brief_format": "{NEWSROOM_BRIEF_FORMAT}",
  "title": "Tổng hợp tin tức toàn cầu và Việt Nam 48 giờ",
  "reading_time_minutes": "auto",
  "editor_note": "Mở đầu bản tin: tóm tắt bức tranh 48h, không nhắc người đọc phải làm gì.",
  "executive_briefing": {{
    "title": "Tóm tắt tổng quan 48h",
    "sections": {{
      "main_picture": "Đoạn văn mở — bức tranh chung 48h (nhiều câu, có mạch).",
      "most_mentioned": "Đoạn văn — chủ đề được nhắc nhiều + vì sao.",
      "top_stories": "Đoạn văn — câu chuyện quan trọng nhất + liên kết giữa chúng.",
      "sector_impacts": "Đoạn văn — tác động theo ngành/khu vực (nối ý).",
      "watch_24_72h": "Đoạn hoặc bullet — biến số 24-72h cụ thể."
    }},
    "content": "Legacy: cùng chất briefing prose — độ dài adaptive theo pools.",
    "representative_sources": [
      {{"title": "...", "source": "...", "url": "https://url-that-tu-crawl", "excerpt": "Trích yếu adaptive."}}
    ],
    "most_mentioned_topics": [
      {{"topic": "...", "why_mentioned": "...", "evidence_hint": "..."}}
    ],
    "hottest_topics": [
      {{"topic": "...", "why_hot": "...", "impact": "...", "evidence_hint": "..."}}
    ],
    "emerging_signals": [
      {{"signal": "...", "why_watch": "..."}}
    ],
    "watch_next": ["...", "..."]
  }},
  "front_page": [
    {{
      "rank": 1,
      "title": "...",
      "one_sentence": "...",
      "why_it_matters": "...",
      "watch_next": "...",
      "source_urls": ["https://url-that-tu-crawl"]
    }}
  ],
  "sector_deep_briefs": [
{sectors_joined}
  ],
  "watchlist_24_72h": [
    {{
      "theme": "...",
      "what_to_watch": "...",
      "why": "..."
    }}
  ],
  "source_desk": [
    {{
      "topic": "...",
      "representative_sources": [
        {{"title": "...", "source": "...", "url": "https://..."}}
      ]
    }}
  ],
  "gaps_and_limits": "Ngắn — chỉ thiếu dữ liệu thật"
}}"""


def _digest_sector_json_schema_fragment() -> str:
    sub = """        {
          "importance_rank": 1,
          "priority_tier": "A",
          "headline": "Một dòng tổng hợp (có thể gom sub-cluster)",
          "summary_hint": "1 câu vì sao đáng chú ý",
          "source_urls": ["https://url-khop-headline", "https://url-cung-chu-de-neu-co"],
          "reason_selected": "Giá trị cho người đọc / bức tranh 48h"
        }"""
    blocks = []
    for code, label in DIGEST_FOUR_SECTORS:
        blocks.append(
            f"""    {{
      "code": "{code}",
      "name": "{label}",
      "summary": "Tóm tắt sector — đủ ý từ pool, không cap độ dài",
      "sub_topics": [
{sub}
      ]
    }}"""
        )
    return ",\n".join(blocks)


_DIGEST_TIER_ORDER = {"A": 0, "B": 1, "C": 2}


def _sub_topic_sort_key(row: dict[str, Any], fallback_index: int) -> tuple[int, int, int]:
    tier = str(row.get("priority_tier") or "B").strip().upper()[:1]
    tier_ord = _DIGEST_TIER_ORDER.get(tier, 2)
    for field in ("importance_rank", "importance", "rank"):
        raw = row.get(field)
        if raw is None or raw == "":
            continue
        try:
            return (tier_ord, 0, int(raw))
        except (TypeError, ValueError):
            continue
    return (tier_ord, 1, fallback_index)


_OVERVIEW_TOPIC_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("middle_east", re.compile(r"iran|israel|hormuz|trung\s*đông|dầu|venez|ukraine|nga\s*s", re.I)),
    ("ai_tech", re.compile(r"\bai\b|chip|nvidia|microsoft|openai|robot|công nghệ|bán dẫn", re.I)),
    ("vn_policy", re.compile(r"việt\s*nam|vn-index|ngân hàng|thuế|lãi suất|bđs|hạ tầng|đầu tư công", re.I)),
    ("markets", re.compile(r"bitcoin|crypto|chứng khoán|vàng|etf|vnindex", re.I)),
    ("inflation", re.compile(r"lạm phát|cpi|nhập siêu", re.I)),
)

_ENTERTAINMENT_HEADLINE_RE = re.compile(
    r"ngọc nữ|đẹp nhất.*việt\s*nam|miss\s|sao\s|celebrity|listicle|golf\b|khảo cổ nhỏ|"
    r"hoàn hảo đến vô thực|bikini|sao việt",
    re.I,
)

_E10_TOPIC_RE = re.compile(r"xăng\s*e10|\be10\b|ethanol\s*e10", re.I)

_AI_POLICY_RE = re.compile(
    r"\bai\b|artificial intelligence|executive order|openai|oversight|llm|model policy|"
    r"chip act|semiconductor",
    re.I,
)

_EDUCATION_TRENDS_RE = re.compile(
    r"tuyển sinh|kỳ thi|lớp\s*10|thi tốt nghiệp|giáo dục|học sinh|đại học|điểm chuẩn",
    re.I,
)

_NOTABLE_MIN_FALLBACK = 4
_NOTABLE_TARGET_FALLBACK = 8

_SENSATIONAL_HEADLINE_RE = re.compile(
    r'sập|tháo chạy|địa chấn|máy in tiền|hoàn hảo đến vô thực|bất ngờ\s*\"?sập',
    re.I,
)

_GENERIC_SUMMARY_HINT = (
    "Tin này được giữ vì phản ánh một luồng đáng chú ý trong 48 giờ."
)
_GENERIC_REASON_SELECTED = "Được chọn vì bổ sung một góc riêng cho bức tranh 48h."

_GENERIC_COPY_FRAGMENTS: tuple[str, ...] = (
    _GENERIC_SUMMARY_HINT,
    _GENERIC_REASON_SELECTED,
    "một luồng đáng chú ý trong 48 giờ",
    "góc riêng cho bức tranh 48h",
    "Tin nêu bật diễn biến:",
    "đáng chú ý trong khung 48h của sector",
    "Sự kiện này được giữ vì đại diện cho nhóm tin:",
    "Tin liên quan ",
    "Luồng AI/công nghệ định hình lại dòng vốn",
)

_SECTOR_SUMMARY_HINT_FALLBACK: dict[str, str] = {
    "finance": (
        "Tin này bổ sung một góc về dòng vốn, thị trường hoặc điều hành kinh tế trong 48 giờ."
    ),
    "tech": (
        "Tin này bổ sung một góc về cạnh tranh công nghệ, AI hoặc hạ tầng số."
    ),
    "news": (
        "Tin này bổ sung một góc về địa chính trị, chính sách hoặc an ninh khu vực."
    ),
    "trends": (
        "Tin này phản ánh một thay đổi đáng chú ý trong đời sống, tiêu dùng hoặc hành vi xã hội."
    ),
    "notable": (
        "Tin này bổ sung một góc đáng chú ý trong bức tranh 48 giờ."
    ),
}

_LOW_VALUE_DIGEST_RE = re.compile(
    r"executive\s+board\s+calendar\s+archive|calendar\s+archive|"
    r"board\s+calendar(?!.*(policy|rate|growth|warning))|"
    r"imf.*calendar(?!.*(cảnh báo|growth|forecast|warning))|"
    r"metadata\s+only|archive\s+page|sitemap|rss\s+feed\s+only",
    re.I,
)

_E10_POLICY_RE = re.compile(
    r"chỉ\s*đạo|phó\s*thủ\s*tướng|bộ\s+|nghị\s*định|chính\s*sách|thường\s*trực",
    re.I,
)
_E10_CONSUMER_RE = re.compile(
    r"người\s*tiêu\s*dùng|lộ\s*trình|triển\s*khai|hướng\s*dẫn|chất\s*lượng\s*xăng",
    re.I,
)

_IRAN_TOPIC_RE = re.compile(r"iran|qeshm|tehran|hormuz|vùng\s*vịnh", re.I)

_SPACE_TECH_RE = re.compile(
    r"blue\s*origin|nasa\b|rocket|long\s*march|space\s*launch|không\s*gian|vệ\s*tinh|"
    r"phóng\s*tên\s*lửa|mission\s+to\s+space",
    re.I,
)

_VIET_DIACRITIC_RE = re.compile(
    r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]",
    re.I,
)

_SUBTOPIC_CLUSTER_DEFS: tuple[tuple[str, re.Pattern[str], str, frozenset[str]], ...] = (
    (
        "us_iran_escalation",
        re.compile(
            r"qeshm|strikes?\s+iran|us\s+strikes|iran.?s\s+qeshm|attack.*iran|iran.*attack|"
            r"war\s+live|tấn\s*công.*iran|leo\s*thang.*iran|iran\s*war|intensify\s+attacks|"
            r"kuwait|bahrain",
            re.I,
        ),
        "Leo thang quân sự Mỹ–Iran quanh đảo Qeshm",
        frozenset({"news"}),
    ),
    (
        "us_iran_talks",
        re.compile(
            r"trump.*iran|tehran|ceasefire|peace\s+deal|talks.*iran|rubio.*iran|"
            r"đàm\s*phán.*iran|thỏa\s*thuận.*iran|one\s+way\s+or\s+another|"
            r"negotiat.*iran|ongoing.*talks",
            re.I,
        ),
        "Đàm phán Tehran bế tắc, rủi ro năng lượng còn kéo dài",
        frozenset({"news"}),
    ),
    (
        "e10_policy",
        _E10_TOPIC_RE,
        "Chính sách và chỉ đạo triển khai xăng E10 tại Việt Nam",
        frozenset({"news", "finance"}),
    ),
    (
        "e10_consumer",
        _E10_TOPIC_RE,
        "Người tiêu dùng và thị trường phản ứng với lộ trình xăng E10",
        frozenset({"trends", "finance"}),
    ),
)

_HEADLINE_EN_TO_VI: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"google\s+owner\s+alphabet.*sell.*(?:stock|bn).*ai", re.I),
        "Alphabet huy động vốn lớn để tài trợ làn sóng đầu tư AI",
    ),
    (
        re.compile(r"alphabet.*sell.*stock.*ai", re.I),
        "Alphabet huy động vốn lớn để tài trợ làn sóng đầu tư AI",
    ),
    (
        re.compile(r"trump\s+says.*time.*iran.*deal", re.I),
        "Trump gia tăng sức ép đàm phán với Iran giữa căng thẳng vùng Vịnh",
    ),
    (
        re.compile(r"trump.*one\s+way\s+or\s+another.*iran", re.I),
        "Trump gia tăng sức ép đàm phán với Iran giữa căng thẳng vùng Vịnh",
    ),
    (
        re.compile(r"us\s+strikes\s+iran.*qeshm", re.I),
        "Mỹ tấn công đảo Qeshm, rủi ro Trung Đông leo thang",
    ),
    (
        re.compile(r"trump.*rubio.*talks.*tehran", re.I),
        "Washington cho rằng đàm phán với Iran vẫn tiếp diễn",
    ),
    (
        re.compile(r"u\.?s\.?,?\s*iran\s+intensify\s+attacks", re.I),
        "Mỹ-Iran leo thang tấn công khi lệnh ngừng bắn mong manh",
    ),
    (
        re.compile(r"trump\s+signs.*(?:ai.*executive\s+order|executive\s+order.*ai)", re.I),
        "Trump ký sắc lệnh quản trị AI, yêu cầu doanh nghiệp chia sẻ mô hình sớm",
    ),
    (
        re.compile(r"goldman\s+sachs.*greed", re.I),
        "Goldman Sachs: thị trường ở trạng thái 'tham lam' khi các công ty AI huy động vốn lớn",
    ),
    (
        re.compile(r"trump\s+signs\s+narrower\s+executive\s+order.*ai", re.I),
        "Trump ký sắc lệnh AI thu hẹp sau phản ứng của ngành công nghệ",
    ),
    (
        re.compile(r"microsoft\s+unveils\s+new\s+ai\s+models", re.I),
        "Microsoft ra mắt mô hình AI mới để giảm phụ thuộc OpenAI",
    ),
    (
        re.compile(r"microsoft\s+unveils\s+project\s+solara", re.I),
        "Microsoft giới thiệu Project Solara cho thiết bị ưu tiên AI agent",
    ),
    (
        re.compile(r"china\s+launches\s+new\s+long\s+march", re.I),
        "Trung Quốc phóng tên lửa Long March 12B mới",
    ),
    (
        re.compile(r"blue\s+origin.*nasa|nasa.*blue\s+origin", re.I),
        "Blue Origin gặp sự cố trong nhiệm vụ hợp tác với NASA",
    ),
)


def _is_generic_digest_copy(text: str) -> bool:
    t = str(text or "").strip()
    if not t:
        return True
    if t in (_GENERIC_SUMMARY_HINT, _GENERIC_REASON_SELECTED):
        return True
    low = t.lower()
    for frag in _GENERIC_COPY_FRAGMENTS:
        if frag.lower() in low:
            return True
    return False


def _is_weak_summary_hint(text: str) -> bool:
    """Câu cụt từ headline[:80] hoặc copy máy không đủ nghĩa."""
    t = str(text or "").strip()
    if not t or _is_generic_digest_copy(t):
        return True
    if t.startswith("Tin liên quan "):
        return True
    if re.search(r":\s*[^.]{0,12}\.\s*$", t) and len(t) < 90:
        return True
    if t.endswith((" lọt '.", " toà.", " lọt '.")):
        return True
    return False


def _sector_summary_hint_fallback(sector_code: str) -> str:
    code = str(sector_code or "").strip().lower()
    return _SECTOR_SUMMARY_HINT_FALLBACK.get(
        code, _SECTOR_SUMMARY_HINT_FALLBACK["news"]
    )


def _is_low_value_digest_item(headline: str) -> bool:
    return bool(_LOW_VALUE_DIGEST_RE.search(str(headline or "")))


def _canonical_digest_url(url: str) -> str:
    u = str(url or "").strip()
    if not u:
        return ""
    try:
        p = urlparse(u)
    except ValueError:
        return u.rstrip("/")
    host = (p.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = (p.path or "").rstrip("/") or ""
    scheme = (p.scheme or "https").lower()
    query = f"?{p.query}" if p.query else ""
    return f"{scheme}://{host}{path}{query}".rstrip("/")


def _digest_url_aliases(url: str) -> list[str]:
    c = _canonical_digest_url(url)
    if not c or not c.startswith("http"):
        return []
    aliases = [c]
    p = urlparse(c)
    host = p.hostname or ""
    if host and not host.startswith("www."):
        aliases.append(_canonical_digest_url(f"{p.scheme}://www.{host}{p.path}"))
    return aliases


class DigestUrlIndex:
    """Whitelist URL thật từ crawl — mọi source_urls public phải thuộc tập này."""

    __slots__ = ("allowed", "by_url")

    def __init__(self, articles: list[dict[str, Any]]) -> None:
        self.allowed: set[str] = set()
        self.by_url: dict[str, dict[str, Any]] = {}
        for art in articles:
            if not isinstance(art, dict):
                continue
            raw_u = str(art.get("url") or "")
            if not raw_u.startswith("http"):
                continue
            for alias in _digest_url_aliases(raw_u):
                self.allowed.add(alias)
                if alias not in self.by_url:
                    self.by_url[alias] = art

    @property
    def active(self) -> bool:
        return bool(self.allowed)


def _digest_headline_keywords(headline: str) -> list[str]:
    low = str(headline or "").lower()
    keys: list[str] = []
    for pat, token in (
        (r"bitcoin|btc", "bitcoin"),
        (r"alphabet|google", "alphabet"),
        (r"vn-index|vnindex|hqc", "vn-index"),
        (r"vn-index|vnindex|hqc", "vnindex"),
        (r"trump.*ai|ai.*trump|sắc lệnh.*ai", "trump ai"),
        (r"microsoft.*ai|ai.*microsoft", "microsoft"),
        (r"iran|qeshm|tehran", "iran"),
        (r"e10|xăng e10", "e10"),
        (r"bất động sản|bđs|dự án", "bất động sản"),
        (r"giá vàng|vàng", "vàng"),
        (r"goldman", "goldman"),
        (r"blue origin|nasa", "blue origin"),
        (r"openai|robot", "openai"),
    ):
        if re.search(pat, low):
            keys.append(token)
    keys.extend(re.findall(r"[\wàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]{5,}", low, re.I)[:6])
    seen: set[str] = set()
    out: list[str] = []
    for k in keys:
        k = k.strip().lower()
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


_KEYWORD_TITLE_REQUIRED = frozenset(
    {
        "bitcoin",
        "alphabet",
        "vn-index",
        "vnindex",
        "iran",
        "trump ai",
        "microsoft",
        "goldman",
        "blue origin",
        "openai",
        "e10",
    }
)


def _article_matches_keywords(art: dict[str, Any], keywords: list[str]) -> bool:
    if not keywords:
        return True
    title_low = str(art.get("title") or "").lower()
    blob = f"{title_low} {art.get('content_for_ai') or ''} {art.get('text') or ''}".lower()
    title_req = [k for k in keywords if k in _KEYWORD_TITLE_REQUIRED]
    if title_req and any(k in title_low for k in title_req):
        return True
    soft = [k for k in keywords if k not in _KEYWORD_TITLE_REQUIRED]
    if soft:
        return any(k in blob for k in soft)
    return False


def _score_digest_headline_article(headline: str, art: dict[str, Any]) -> float:
    title = str(art.get("title") or "")
    hl = str(headline or "").strip().lower()
    if not hl:
        return 0.0
    title_low = title.lower()
    title_sc = SequenceMatcher(None, hl, title_low).ratio()
    keywords = _digest_headline_keywords(headline)
    if keywords and not _article_matches_keywords(art, keywords):
        return 0.0
    text = str(art.get("content_for_ai") or art.get("text") or art.get("summary") or "")[:500]
    blob_sc = SequenceMatcher(None, hl, f"{title} {text}".lower()).ratio() if text else 0.0
    hl_tokens = set(re.findall(r"[\wàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]{4,}", hl, re.I))
    title_tokens = set(re.findall(r"\w{4,}", title_low))
    overlap = len(hl_tokens & title_tokens) / max(1, len(hl_tokens))
    return max(title_sc, blob_sc * 0.55, overlap * 0.7)


def _is_likely_fabricated_digest_url(url: str) -> bool:
    """URL Gemini rút gọn / slug giả — không dùng path-fuzzy, chỉ headline match."""
    u = _canonical_digest_url(url)
    if not u.startswith("http"):
        return True
    try:
        p = urlparse(u)
    except ValueError:
        return True
    path = (p.path or "").strip("/")
    if not path:
        return True
    if re.search(r"\d{6,}|liveblog|\.htm|/20\d{2}/", path):
        return False
    host = (p.hostname or "").lower()
    if host.endswith("baochinhphu.vn") or host.endswith("dantri.com.vn"):
        return len(path) < 12
    if host in {"cnbc.com", "coindesk.com", "wired.com", "tuoitre.vn", "theguardian.com"}:
        return len(path) < 28 or path.count("/") < 2
    return len(path) < 16


def _resolve_digest_url_by_path(
    raw: str, headline: str, index: DigestUrlIndex
) -> str:
    raw_c = _canonical_digest_url(raw)
    if not raw_c or _is_likely_fabricated_digest_url(raw_c):
        return ""
    if raw_c in index.allowed:
        return raw_c
    host = (urlparse(raw_c).hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    raw_path = urlparse(raw_c).path or ""
    if not host or len(raw_path) < 10:
        return ""
    hl = str(headline or "").strip()
    best_u = ""
    best_sc = 0.0
    for cand in index.allowed:
        ch = (urlparse(cand).hostname or "").lower()
        if ch.startswith("www."):
            ch = ch[4:]
        if ch != host:
            continue
        cand_path = urlparse(cand).path or ""
        sc = SequenceMatcher(None, raw_path, cand_path).ratio()
        if raw_path in cand_path or cand_path in raw_path:
            sc = max(sc, 0.82)
        art = index.by_url.get(cand)
        if art and hl:
            sc = min(1.0, sc * (0.55 + 0.45 * _score_digest_headline_article(hl, art)))
        if sc > best_sc:
            best_sc, best_u = sc, cand
    return best_u if best_sc >= 0.72 else ""


def _best_allowed_url_for_headline(
    headline: str,
    index: DigestUrlIndex,
    *,
    prefer_host: str = "",
    sector_code: str = "",
    min_score: float | None = None,
) -> str:
    best_u = ""
    best_sc = 0.0
    host = (prefer_host or "").lower()
    if host.startswith("www."):
        host = host[4:]

    def _host_key(u: str) -> str:
        h = (urlparse(u).hostname or "").lower()
        return h[4:] if h.startswith("www.") else h

    pool = [u for u in index.allowed if not host or _host_key(u) == host]
    if not pool:
        pool = list(index.allowed)
    keywords = _digest_headline_keywords(headline)
    title_req = [k for k in keywords if k in _KEYWORD_TITLE_REQUIRED]
    if title_req:
        filtered = [
            u
            for u in pool
            if (art := index.by_url.get(u))
            and any(k in str(art.get("title") or "").lower() for k in title_req)
        ]
        if filtered:
            pool = filtered
    elif keywords:
        filtered = [
            u
            for u in pool
            if (art := index.by_url.get(u)) and _article_matches_keywords(art, keywords)
        ]
        if filtered:
            pool = filtered
    for cand in pool:
        art = index.by_url.get(cand)
        if not art:
            continue
        sc = _score_digest_headline_article(headline, art)
        src = str(art.get("source") or "").lower()
        if sector_code == "finance" and re.search(r"cnbc|bloomberg|reuters|ft\.com", src):
            sc = min(1.0, sc * 1.04)
        if sc > best_sc:
            best_sc, best_u = sc, cand
    min_sc = min_score if min_score is not None else (0.32 if host else 0.36)
    return best_u if best_u and best_sc >= min_sc else ""


def _resolve_digest_url(
    url: str,
    headline: str,
    index: DigestUrlIndex | None,
    *,
    sector_code: str = "",
) -> str:
    if index is None or not index.active:
        return _canonical_digest_url(url)
    raw = _canonical_digest_url(url)
    hl = str(headline or "").strip()
    if raw in index.allowed:
        return raw
    path_match = _resolve_digest_url_by_path(raw, hl, index) if raw else ""
    if path_match:
        if raw not in index.allowed:
            print(
                f"WARN digest URL: path-matched {raw[:80]} -> {path_match[:80]}",
                file=sys.stderr,
            )
        return path_match
    host = (urlparse(raw).hostname or "").lower() if raw else ""
    if host.startswith("www."):
        host = host[4:]
    need_strong = bool(raw and raw not in index.allowed)
    strong_min = 0.48 if need_strong else None
    matched = _best_allowed_url_for_headline(
        hl, index, prefer_host=host, sector_code=sector_code, min_score=strong_min
    )
    if not matched and hl:
        matched = _best_allowed_url_for_headline(
            hl, index, sector_code=sector_code, min_score=strong_min
        )
    if matched:
        if raw and raw not in index.allowed:
            print(
                f"WARN digest URL: replaced fabricated {raw[:90]} -> {matched[:90]}",
                file=sys.stderr,
            )
        return matched
    if raw:
        print(f"WARN digest URL: dropped not in whitelist: {raw}", file=sys.stderr)
    return ""


def _sanitize_sub_topic_urls(
    row: dict[str, Any],
    index: DigestUrlIndex | None,
    sector_code: str,
) -> dict[str, Any]:
    out = dict(row)
    hl = str(out.get("headline") or "").strip()
    urls: list[str] = []
    for raw in out.get("source_urls") or []:
        resolved = _resolve_digest_url(str(raw), hl, index, sector_code=sector_code)
        if resolved and resolved not in urls:
            urls.append(resolved)
    if not urls and hl and index and index.active:
        resolved = _resolve_digest_url("", hl, index, sector_code=sector_code)
        if resolved:
            urls.append(resolved)
    out["source_urls"] = urls[:3]
    return out


def _sanitize_notable_url(
    notable: dict[str, Any],
    index: DigestUrlIndex | None,
) -> dict[str, Any]:
    out = dict(notable)
    title = str(out.get("title") or "").strip()
    u = _resolve_digest_url(str(out.get("url") or ""), title, index, sector_code="notable")
    if u:
        out["url"] = u
    else:
        out.pop("url", None)
    return out


def validate_digest_url_whitelist(
    summary: dict[str, Any],
    index: DigestUrlIndex | None,
) -> list[str]:
    if index is None or not index.active:
        return []
    warnings: list[str] = []

    def _check(path: str, url: str) -> None:
        cu = _canonical_digest_url(str(url))
        if cu and cu not in index.allowed:
            warnings.append(f"{path} URL ngoài whitelist: {cu[:80]}")

    for i, sec in enumerate(summary.get("sectors") or []):
        if not isinstance(sec, dict):
            continue
        code = str(sec.get("code") or "?")
        for j, row in enumerate(sec.get("sub_topics") or []):
            if not isinstance(row, dict):
                continue
            for u in row.get("source_urls") or []:
                _check(f"sectors[{i}] ({code}) sub_topics[{j}]", str(u))
    for k, n in enumerate(summary.get("notable_articles") or []):
        if not isinstance(n, dict):
            continue
        _check(f"notable_articles[{k}]", str(n.get("url") or ""))
    for i, fp in enumerate(summary.get("front_page") or []):
        if not isinstance(fp, dict):
            continue
        for u in fp.get("source_urls") or []:
            _check(f"front_page[{i}]", str(u))
    for i, sec in enumerate(summary.get("sector_deep_briefs") or []):
        if not isinstance(sec, dict):
            continue
        code = str(sec.get("code") or "?")
        for j, dossier in enumerate(sec.get("story_dossiers") or []):
            if not isinstance(dossier, dict):
                continue
            for k, src in enumerate(dossier.get("representative_sources") or []):
                if isinstance(src, dict):
                    _check(
                        f"sector_deep_briefs[{i}] ({code}) story_dossiers[{j}] sources[{k}]",
                        str(src.get("url") or ""),
                    )
    for i, desk in enumerate(summary.get("source_desk") or []):
        if not isinstance(desk, dict):
            continue
        for j, src in enumerate(desk.get("representative_sources") or []):
            if isinstance(src, dict):
                _check(f"source_desk[{i}] sources[{j}]", str(src.get("url") or ""))
    return warnings


def _infer_alphabet_digest_copy(headline: str) -> tuple[str, str] | None:
    low = str(headline or "").lower()
    if re.search(r"alphabet|google", low) and re.search(
        r"huy động|vốn|capital|đầu tư|spending|ai|tài trợ|làn sóng",
        low,
    ):
        return (
            "Cho thấy chi phí đầu tư AI và hạ tầng dữ liệu đang tăng mạnh.",
            "Đại diện cho luồng đầu tư hạ tầng AI và nhu cầu vốn của các tập đoàn công nghệ lớn.",
        )
    return None


def _recompute_digest_subtopic_copy(
    row: dict[str, Any], sector_code: str
) -> dict[str, Any]:
    out = dict(row)
    hl = str(out.get("headline") or "").strip()
    alpha = _infer_alphabet_digest_copy(hl)
    if alpha:
        out["summary_hint"], out["reason_selected"] = alpha
        return out
    out["summary_hint"] = _infer_summary_hint(hl, sector_code)
    out["reason_selected"] = _infer_reason_selected(hl, sector_code)
    return out


def _bitcoin_finance_bucket(headline: str) -> str:
    low = str(headline or "").lower()
    if not re.search(r"bitcoin|btc", low):
        return ""
    if re.search(
        r"ai|cổ phiếu|giữ sức hút|phân hóa|risk|tài sản rủi ro|giảm mạnh trong khi",
        low,
    ):
        return "btc_ai_mixed"
    if re.search(r"70\.?000|thủng|mốc|usd", low):
        return "btc_level"
    return "btc_other"


def _merge_bitcoin_finance_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mixed: list[dict[str, Any]] = []
    level: list[dict[str, Any]] = []
    other: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        bucket = _bitcoin_finance_bucket(str(row.get("headline") or ""))
        if bucket == "btc_ai_mixed":
            mixed.append(row)
        elif bucket == "btc_level":
            level.append(row)
        else:
            other.append(row)
    out = list(other)
    if mixed and level:
        title = str(mixed[0].get("headline") or "").strip()
        if not title:
            title = "Bitcoin giảm mạnh trong khi cổ phiếu AI giữ sức hút"
        out.insert(0, _merge_cluster_rows(mixed + level, title, "finance"))
    else:
        out = mixed + level + out
    return out


def _iran_cluster_key(headline: str) -> str | None:
    low = str(headline or "").lower()
    if not _IRAN_TOPIC_RE.search(low):
        return None
    if re.search(
        r"qeshm|strikes?\s+iran|us\s+strikes|iran.?s\s+qeshm|war\s+live|"
        r"tấn\s*công|intensify\s+attacks|kuwait|bahrain|leo\s*thang|mỹ\s*tấn\s*công",
        low,
        re.I,
    ):
        return "us_iran_escalation"
    if re.search(
        r"trump|tehran|ceasefire|peace\s+deal|talks|rubio|negotiat|"
        r"đàm\s*phán|one\s+way\s+or\s+another|thỏa\s*thuận",
        low,
        re.I,
    ):
        return "us_iran_talks"
    return "us_iran_escalation"


def _e10_cluster_key(headline: str) -> str | None:
    if not _E10_TOPIC_RE.search(str(headline or "")):
        return None
    if _E10_CONSUMER_RE.search(headline) and not _E10_POLICY_RE.search(headline):
        return "e10_consumer"
    return "e10_policy"


def _headline_is_mostly_english(headline: str) -> bool:
    h = str(headline or "").strip()
    if not h or len(_VIET_DIACRITIC_RE.findall(h)) >= 3:
        return False
    latin_words = re.findall(r"[A-Za-z]{4,}", h)
    return len(latin_words) >= 3


def _vietnamese_public_headline(headline: str, sector_code: str = "") -> str:
    h = re.sub(r"\s+", " ", str(headline or "").strip())
    if not h:
        return h
    for pat, vi in _HEADLINE_EN_TO_VI:
        if pat.search(h):
            return vi
    low = h.lower()
    if re.search(r"alphabet|google\s+owner", low) and re.search(r"sell|stock|ai|spending", low):
        return "Alphabet huy động vốn lớn để tài trợ làn sóng đầu tư AI"
    if "trump" in low and "iran" in low and re.search(r"deal|talks|one way", low):
        return "Trump gia tăng sức ép đàm phán với Iran giữa căng thẳng vùng Vịnh"
    if re.search(r"qeshm|strikes.*iran|us\s+strikes", low):
        return "Mỹ tấn công đảo Qeshm, rủi ro Trung Đông leo thang"
    if re.search(r"vn-index|vnindex", low, re.I):
        return h if _VIET_DIACRITIC_RE.search(h) else "VN-Index giảm mạnh, thị trường cổ phiếu phân hóa"
    if re.search(r"trump\s+signs.*ai", low):
        return "Trump ký sắc lệnh quản trị AI, yêu cầu doanh nghiệp chia sẻ mô hình sớm"
    if re.search(r"goldman\s+sachs", low) and "greed" in low:
        return (
            "Goldman Sachs: thị trường ở trạng thái 'tham lam' "
            "khi các công ty AI huy động vốn lớn"
        )
    if _headline_is_mostly_english(h):
        stub = _english_headline_vietnamese_stub(h, sector_code)
        return stub if stub else h
    return h


def _english_headline_vietnamese_stub(headline: str, sector_code: str = "") -> str:
    """Paraphrase tối thiểu sang VI khi không khớp template — tránh để nguyên câu EN."""
    low = str(headline or "").lower()
    if re.search(r"alphabet|google", low) and "ai" in low:
        return "Alphabet huy động vốn lớn để tài trợ làn sóng đầu tư AI"
    if "trump" in low and "iran" in low:
        return "Trump gia tăng sức ép đàm phán với Iran giữa căng thẳng vùng Vịnh"
    if re.search(r"qeshm|strikes.*iran", low):
        return "Mỹ tấn công đảo Qeshm, rủi ro Trung Đông leo thang"
    if re.search(r"trump\s+signs.*ai", low):
        return "Trump ký sắc lệnh quản trị AI, yêu cầu doanh nghiệp chia sẻ mô hình sớm"
    if "microsoft" in low and "ai" in low:
        return "Microsoft đẩy mạnh mô hình AI và hạ phụ thuộc OpenAI"
    if "bitcoin" in low or "crypto" in low:
        return "Bitcoin và tài sản rủi ro biến động mạnh trong 48 giờ"
    if _SPACE_TECH_RE.search(low):
        return "Sự kiện không gian và công nghệ hàng không vũ trụ đáng chú ý"
    # Không khớp pattern hardcode nào -> KHÔNG dùng câu mẫu chung (gây trùng lặp
    # anchor text giữa nhiều bài khác nhau). Trả về chuỗi rỗng để caller tự quyết
    # định fallback về title gốc tiếng Anh (truncate ở nơi gọi).
    return ""


def _digest_topic_stream(headline: str) -> str:
    low = str(headline or "").lower()
    if re.search(r"qeshm|strikes.*iran|tấn công.*iran|war\s+live", low):
        return "us_iran_escalation"
    if re.search(r"trump.*iran|tehran|ceasefire|đàm phán.*iran", low):
        return "us_iran_talks"
    if _E10_TOPIC_RE.search(low):
        return "e10"
    if re.search(r"vn-index|vnindex|hqc|cổ phiếu", low):
        return "vn_equity"
    if re.search(r"bitcoin|crypto|vàng|etf", low):
        return "markets"
    if re.search(r"\bai\b|openai|nvidia|alphabet|microsoft.*ai|robot", low):
        return "ai_tech"
    if re.search(r"bđs|bất động sản|dự án.*tphcm", low):
        return "vn_real_estate"
    if re.search(r"lạm phát|cpi", low):
        return "inflation"
    if _SPACE_TECH_RE.search(low):
        return "space_tech"
    if re.search(r"tuyển sinh|lớp\s*10|giáo dục", low):
        return "education"
    return "general"


def _infer_tech_summary_hint(headline: str) -> str | None:
    low = str(headline or "").lower()
    if re.search(r"alphabet|google\s+owner", low) and re.search(
        r"sell|stock|capital|huy động|bn|spending|vốn",
        low,
    ):
        return "Cho thấy chi phí đầu tư AI và hạ tầng dữ liệu đang tăng mạnh."
    if re.search(r"microsoft", low) and re.search(
        r"model|openai|giảm phụ thuộc|chi phí",
        low,
    ):
        return (
            "Phản ánh nỗ lực giảm phụ thuộc mô hình bên ngoài "
            "và kiểm soát chi phí AI."
        )
    if re.search(r"trump", low) and re.search(
        r"sắc lệnh|executive order|quản trị|oversight",
        low,
    ) and re.search(r"\bai\b", low):
        return (
            "Tác động tới khung quản trị, quyền truy cập mô hình và quan hệ "
            "giữa chính phủ với doanh nghiệp AI."
        )
    if re.search(r"openai", low) and re.search(
        r"robot|humanoid|hình người|phần cứng",
        low,
    ):
        return "Cho thấy AI đang mở rộng từ phần mềm sang phần cứng và robot."
    if re.search(r"dppa|mua bán điện trực tiếp|trung tâm dữ liệu|data center", low):
        return (
            "Liên quan tới khả năng cung cấp điện sạch cho hạ tầng "
            "trung tâm dữ liệu tại Việt Nam."
        )
    if re.search(r"long march|tên lửa", low) and re.search(r"trung quốc|china", low):
        return "Phản ánh cuộc đua không gian và năng lực phóng vệ tinh của Trung Quốc."
    if re.search(r"project solara|agent-first|ưu tiên ai agent", low):
        return "Cho thấy hệ sinh thái AI agent và thiết bị đầu cuối mới đang được định hình."
    return None


def _infer_summary_hint(headline: str, sector_code: str) -> str:
    alpha = _infer_alphabet_digest_copy(headline)
    if alpha:
        return alpha[0]
    low = str(headline or "").lower()
    code = str(sector_code or "").strip().lower()
    if code == "tech" or re.search(r"\bai\b|openai|nvidia|alphabet|microsoft", low):
        tech_hint = _infer_tech_summary_hint(headline)
        if tech_hint:
            return tech_hint
    stream = _digest_topic_stream(headline)
    if stream == "vn_equity" or re.search(r"vn-index|vnindex|hqc", low):
        return (
            "Diễn biến cho thấy thị trường chứng khoán Việt Nam phân hóa: "
            "chỉ số chung giảm nhưng một số mã đầu cơ vẫn hút dòng tiền."
        )
    if stream == "us_iran_escalation":
        return (
            "Leo thang quân sự quanh Iran làm thị trường theo dõi giá dầu "
            "và tài sản phòng thủ."
        )
    if stream == "us_iran_talks":
        return (
            "Đàm phán Mỹ-Iran còn bế tắc, kéo theo rủi ro năng lượng và tâm lý risk-off."
        )
    if stream == "e10":
        return (
            "Chủ đề xăng E10 ảnh hưởng chi phí vận hành và kỳ vọng người tiêu dùng "
            "trong ngắn hạn."
        )
    if stream == "markets":
        return "Biến động tài sản rủi ro phản ánh khẩu vị nhà đầu tư trong 48 giờ qua."
    if stream == "vn_real_estate":
        return "Chính sách/tháo gỡ BĐS ảnh hưởng thanh khoản và niềm tin nhà đầu tư nội địa."
    if stream == "inflation":
        return "Số liệu lạm phát là biến số then chốt cho kỳ vọng lãi suất và điều hành."
    if stream == "space_tech":
        return "Sự kiện không gian/công nghệ ảnh hưởng kỳ vọng hạ tầng và chuỗi cung ứng."
    if stream == "education":
        return "Diễn biến giáo dục phản ánh áp lực xã hội và kỳ vọng gia đình học sinh."
    return _sector_summary_hint_fallback(code)


def _infer_reason_selected(headline: str, sector_code: str) -> str:
    alpha = _infer_alphabet_digest_copy(headline)
    if alpha:
        return alpha[1]
    stream = _digest_topic_stream(headline)
    labels = {
        "vn_equity": "Đại diện cho tâm lý ngắn hạn và độ phân hóa trên thị trường cổ phiếu trong nước.",
        "us_iran_escalation": "Đại diện cho luồng leo thang địa chính trị và rủi ro năng lượng toàn cầu.",
        "us_iran_talks": "Đại diện cho luồng đàm phán Mỹ-Iran và kỳ vọng giảm leo thang.",
        "e10": "Đại diện cho luồng chuyển đổi nhiên liệu và phản ứng người tiêu dùng Việt Nam.",
        "ai_tech": "Đại diện cho luồng đầu tư/chính sách AI định hình sector công nghệ.",
        "markets": "Đại diện cho luồng phân hóa tài sản rủi ro và dòng tiền toàn cầu.",
        "vn_real_estate": "Đại diện cho luồng tháo gỡ BĐS và thanh khoản thị trường Việt Nam.",
        "inflation": "Đại diện cho luồng vĩ mô lạm phát trong bức tranh 48h.",
        "space_tech": "Đại diện cho luồng công nghệ/khoa học không gian trong 48 giờ.",
        "education": "Đại diện cho luồng giáo dục-đời sống trong sector xu hướng.",
    }
    if stream in labels:
        return labels[stream]
    label = {
        "finance": "kinh tế - tài chính",
        "tech": "công nghệ",
        "news": "địa chính trị",
        "trends": "đời sống - xu hướng",
    }.get(sector_code, "bức tranh 48h")
    return f"Đại diện cho một luồng tin trong nhóm {label}."


def _sub_topic_cluster_key(headline: str, sector_code: str) -> str | None:
    hl = str(headline or "")
    if sector_code == "news":
        iran_key = _iran_cluster_key(hl)
        if iran_key:
            return iran_key
    e10_key = _e10_cluster_key(hl)
    if e10_key:
        for key, pat, _, sectors in _SUBTOPIC_CLUSTER_DEFS:
            if key == e10_key and sector_code in sectors:
                return key
    for key, pat, _, sectors in _SUBTOPIC_CLUSTER_DEFS:
        if sector_code not in sectors or key.startswith("e10_"):
            continue
        if pat.search(hl):
            return key
    return None


def _merge_cluster_rows(
    group: list[dict[str, Any]], cluster_headline: str, sector_code: str = "news"
) -> dict[str, Any]:
    indexed = [(i, r) for i, r in enumerate(group) if isinstance(r, dict)]
    indexed.sort(key=lambda pair: _sub_topic_sort_key(pair[1], pair[0]))
    base = dict(indexed[0][1])
    urls: list[str] = []
    for row in group:
        if not isinstance(row, dict):
            continue
        for u in row.get("source_urls") or []:
            s = str(u).strip()
            if s and s not in urls:
                urls.append(s)
    base["headline"] = cluster_headline
    base["source_urls"] = urls[:3]
    tier = "B"
    for row in group:
        t = str(row.get("priority_tier") or "").upper()[:1]
        if t == "A":
            tier = "A"
            break
        if t == "B" and tier != "A":
            tier = "B"
    base["priority_tier"] = tier
    hl = str(cluster_headline or "")
    infer_sector = str(sector_code or "news").strip().lower() or "news"
    e10k = _e10_cluster_key(hl)
    if e10k == "e10_consumer":
        infer_sector = "trends"
    elif e10k == "e10_policy":
        infer_sector = "news"
    return _recompute_digest_subtopic_copy({**base, "headline": hl}, infer_sector)


def _cluster_sub_topics_in_sector(
    rows: list[dict[str, Any]], sector_code: str
) -> list[dict[str, Any]]:
    clusters: dict[str, list[dict[str, Any]]] = {}
    unclustered: list[dict[str, Any]] = []
    titles = {key: title for key, _, title, _ in _SUBTOPIC_CLUSTER_DEFS}
    for row in rows:
        if not isinstance(row, dict):
            continue
        hl = str(row.get("headline") or row.get("title") or "").strip()
        ck = _sub_topic_cluster_key(hl, sector_code)
        if ck:
            clusters.setdefault(ck, []).append(row)
        else:
            unclustered.append(row)
    out: list[dict[str, Any]] = []
    for key, group in clusters.items():
        title = titles.get(key) or group[0].get("headline", "")
        if len(group) == 1:
            out.append(group[0])
        else:
            out.append(_merge_cluster_rows(group, str(title), sector_code))
    out.extend(unclustered)
    out.sort(key=lambda r: _sub_topic_sort_key(r, 0))
    return out


def _headline_match_key(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip().lower()[:140]


def _dedupe_sub_topics_by_headline(
    rows: list[dict[str, Any]], sector_code: str
) -> list[dict[str, Any]]:
    """Sau Việt hóa headline: gom trùng trong sector, merge source_urls."""
    seen: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        hl = str(row.get("headline") or row.get("title") or "").strip()
        key = _headline_match_key(hl)
        if not key:
            continue
        if key not in seen:
            seen[key] = dict(row)
            order.append(key)
            continue
        base = seen[key]
        urls: list[str] = [
            str(u).strip() for u in (base.get("source_urls") or []) if str(u).strip()
        ]
        for u in row.get("source_urls") or []:
            s = str(u).strip()
            if s and s not in urls:
                urls.append(s)
        base["source_urls"] = urls[:3]
        for tier in (str(row.get("priority_tier") or "").upper()[:1],):
            if tier == "A":
                base["priority_tier"] = "A"
                break
            if tier == "B" and str(base.get("priority_tier") or "").upper()[:1] != "A":
                base["priority_tier"] = "B"
        base = _recompute_digest_subtopic_copy(base, sector_code)
    out = [seen[k] for k in order]
    out.sort(key=lambda r: _sub_topic_sort_key(r, 0))
    return out


def _ensure_specific_digest_copy(
    row: dict[str, Any], sector_code: str, *, warn: bool = True
) -> dict[str, Any]:
    """Đảm bảo summary_hint/reason_selected không còn placeholder generic."""
    out = dict(row)
    hl = str(out.get("headline") or "").strip()
    hint = str(out.get("summary_hint") or "").strip()
    reason = str(out.get("reason_selected") or "").strip()
    if not hint or _is_generic_digest_copy(hint) or _is_weak_summary_hint(hint):
        if warn and hint:
            print(
                f"WARN digest polish: weak summary_hint → rewrite ({sector_code})",
                file=sys.stderr,
            )
        out["summary_hint"] = _infer_summary_hint(hl, sector_code)
    if not reason or _is_generic_digest_copy(reason):
        if warn and reason:
            print(
                f"WARN digest polish: generic reason_selected → rewrite ({sector_code})",
                file=sys.stderr,
            )
        out["reason_selected"] = _infer_reason_selected(hl, sector_code)
    return out


def _polish_sub_topic_fields(
    row: dict[str, Any],
    sector_code: str,
    *,
    warn_generic: bool = True,
    url_index: DigestUrlIndex | None = None,
) -> dict[str, Any]:
    out = dict(row)
    raw_hl = str(out.get("headline") or out.get("title") or "").strip()
    if raw_hl:
        hl = _editorialize_digest_headline(raw_hl)
        hl = _vietnamese_public_headline(hl, sector_code)
        out["headline"] = hl
    else:
        hl = ""
    tier = str(out.get("priority_tier") or "").strip().upper()[:1]
    out["priority_tier"] = tier if tier in ("A", "B", "C") else "B"
    out = _recompute_digest_subtopic_copy(out, sector_code)
    if warn_generic:
        hint = str(out.get("summary_hint") or "")
        if _is_generic_digest_copy(hint) or _is_weak_summary_hint(hint):
            print(
                f"WARN digest polish: weak summary_hint after recompute ({sector_code})",
                file=sys.stderr,
            )
            out = _recompute_digest_subtopic_copy(out, sector_code)
    out = _sanitize_sub_topic_urls(out, url_index, sector_code)
    return out


def _consolidate_e10_globally(
    summary: dict[str, Any], *, url_index: DigestUrlIndex | None = None
) -> dict[str, Any]:
    """Tối đa 2 cụm E10 toàn bài: chính sách (news/finance) + người tiêu dùng (trends)."""
    policy_rows: list[dict[str, Any]] = []
    consumer_rows: list[dict[str, Any]] = []
    for sec in summary.get("sectors") or []:
        if not isinstance(sec, dict):
            continue
        kept: list[dict[str, Any]] = []
        for row in sec.get("sub_topics") or []:
            if not isinstance(row, dict):
                continue
            hl = str(row.get("headline") or "")
            if not _E10_TOPIC_RE.search(hl):
                kept.append(row)
                continue
            key = _e10_cluster_key(hl)
            if key == "e10_consumer":
                consumer_rows.append(row)
            else:
                policy_rows.append(row)
        sec["sub_topics"] = kept

    titles = {key: title for key, _, title, _ in _SUBTOPIC_CLUSTER_DEFS}
    sector_map = {s.get("code"): s for s in summary.get("sectors") or [] if isinstance(s, dict)}

    def _inject(code: str, merged: dict[str, Any] | None) -> None:
        if not merged:
            return
        sec = sector_map.get(code)
        if not sec:
            return
        subs = sec.get("sub_topics") if isinstance(sec.get("sub_topics"), list) else []
        polished = _polish_sub_topic_fields(merged, code, warn_generic=False, url_index=url_index)
        subs.append(polished)
        sec["sub_topics"] = subs

    if policy_rows:
        _inject(
            "news" if sector_map.get("news") else "finance",
            _merge_cluster_rows(
                policy_rows,
                titles.get("e10_policy", policy_rows[0].get("headline", "")),
                "news",
            ),
        )
    if consumer_rows:
        _inject(
            "trends" if sector_map.get("trends") else "finance",
            _merge_cluster_rows(
                consumer_rows,
                titles.get("e10_consumer", consumer_rows[0].get("headline", "")),
                "trends",
            ),
        )
    return summary


def _enforce_digest_public_polish(
    summary: dict[str, Any], *, url_index: DigestUrlIndex | None = None
) -> dict[str, Any]:
    """Validation cuối: WARN + rewrite nếu còn generic hoặc headline EN."""
    for sec in summary.get("sectors") or []:
        if not isinstance(sec, dict):
            continue
        code = str(sec.get("code") or "").strip().lower()
        fixed: list[dict[str, Any]] = []
        for row in sec.get("sub_topics") or []:
            if not isinstance(row, dict):
                continue
            r = dict(row)
            hl = str(r.get("headline") or "")
            if _headline_is_mostly_english(hl):
                print(
                    f"WARN digest polish: headline EN → VI ({code}): {hl[:70]}",
                    file=sys.stderr,
                )
                r["headline"] = _vietnamese_public_headline(hl, code)
            r = _recompute_digest_subtopic_copy(r, code)
            r = _sanitize_sub_topic_urls(r, url_index, code)
            fixed.append(r)
        sec["sub_topics"] = _dedupe_sub_topics_by_headline(fixed, code)
        sec["sub_topics"] = [
            _sanitize_sub_topic_urls(r, url_index, code) for r in sec["sub_topics"] if isinstance(r, dict)
        ]
    for n in summary.get("notable_articles") or []:
        if not isinstance(n, dict):
            continue
        t = str(n.get("title") or "")
        if t and _headline_is_mostly_english(t):
            print(f"WARN digest polish: notable EN → VI: {t[:70]}", file=sys.stderr)
            n["title"] = _vietnamese_public_headline(_editorialize_digest_headline(t))
        n["why_notable"] = _infer_summary_hint(n.get("title") or t, "notable")
        sanitized = _sanitize_notable_url(n, url_index)
        n.clear()
        n.update(sanitized)
    return summary


def _scrub_digest_public_copy(
    summary: dict[str, Any], *, url_index: DigestUrlIndex | None = None
) -> dict[str, Any]:
    """Pass cuối: headline VI + không còn copy generic."""
    for sec in summary.get("sectors") or []:
        if not isinstance(sec, dict):
            continue
        code = str(sec.get("code") or "").strip().lower()
        polished: list[dict[str, Any]] = []
        for row in sec.get("sub_topics") or []:
            if isinstance(row, dict):
                polished.append(
                    _polish_sub_topic_fields(row, code, warn_generic=False, url_index=url_index)
                )
        sec["sub_topics"] = polished
    for n in summary.get("notable_articles") or []:
        if not isinstance(n, dict):
            continue
        title = str(n.get("title") or "").strip()
        if title:
            n["title"] = _vietnamese_public_headline(_editorialize_digest_headline(title))
        n["why_notable"] = _infer_summary_hint(title, "notable")
        sanitized = _sanitize_notable_url(n, url_index)
        n.clear()
        n.update(sanitized)
    return summary


def _editorialize_digest_headline(headline: str) -> str:
    """Fallback khi merge vẫn giữ headline crawl giật/thô."""
    h = re.sub(r"\s+", " ", str(headline or "").strip())
    if h and h[0].islower():
        h = h[0].upper() + h[1:]
    if not h or not _SENSATIONAL_HEADLINE_RE.search(h):
        return h
    low = h.lower()
    if "giá vàng" in low and ("sập" in low or "tháo chạy" in low):
        return "Giá vàng giảm mạnh khi kỳ vọng rủi ro được định giá lại"
    if "robot hình người" in low and "địa chấn" in low:
        return (
            "Robot hình người giá thấp làm nóng cuộc đua phần cứng AI "
            "(Hugging Face công bố thiết kế mở)"
        )
    if "máy in tiền" in low or ("thương hiệu việt" in low and "cổ đông" in low):
        return "Một số thương hiệu Việt lâu đời tiếp tục tạo dòng tiền ổn định cho cổ đông"
    out = h
    out = re.sub(r'["\']?\s*sập\s*["\']?', "giảm mạnh", out, flags=re.I)
    out = re.sub(r"tháo chạy", "dòng tiền rút", out, flags=re.I)
    out = re.sub(r"gây\s+địa chấn", "làm nóng cuộc đua", out, flags=re.I)
    out = re.sub(r"địa chấn", "tác động lớn", out, flags=re.I)
    out = re.sub(
        r"trở thành\s+['\"]?(?:máy in tiền|dòng tiền ổn định)['\"]?\s+cho",
        "tiếp tục tạo dòng tiền cho",
        out,
        flags=re.I,
    )
    out = re.sub(r"máy in tiền", "dòng tiền ổn định", out, flags=re.I)
    return out.strip()[:220]


def _overview_topic_bucket(text: str) -> str:
    blob = str(text or "").lower()
    for name, pat in _OVERVIEW_TOPIC_RULES:
        if pat.search(blob):
            return name
    return ""


def _bullets_overlap_semantically(a: str, b: str) -> bool:
    if SequenceMatcher(None, a.lower(), b.lower()).ratio() >= 0.58:
        return True
    ta, tb = _overview_topic_bucket(a), _overview_topic_bucket(b)
    return bool(ta and ta == tb)


def _normalize_executive_overview_bullets(raw: Any) -> list[str]:
    bullets: list[str] = []
    if isinstance(raw, list):
        for item in raw:
            line = str(item or "").strip()
            if line:
                bullets.append(line)
    elif isinstance(raw, str) and raw.strip():
        text = raw.strip()
        if re.search(r"(?m)^\s*[-•*]\s+", text):
            bullets = [
                re.sub(r"^\s*[-•*]\s+", "", ln).strip()
                for ln in text.splitlines()
                if ln.strip()
            ]
        else:
            bullets = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
            if len(bullets) <= 2:
                bullets = [
                    c.strip()
                    for c in re.split(
                        r"(?<=[.!?…])\s+(?=[\"'“‘(A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠƯ0-9])",
                        text,
                    )
                    if len(c.strip()) >= 24
                ] or [text]
    out: list[str] = []
    for b in bullets:
        if any(_bullets_overlap_semantically(b, kept) for kept in out):
            continue
        out.append(b)
        if len(out) >= DIGEST_PARSER_MAX_EXEC_BULLETS:
            break
    return out


def _coerce_sub_topic_row(row: dict[str, Any], sector_code: str = "") -> dict[str, Any]:
    return _polish_sub_topic_fields(row, sector_code or "news", warn_generic=False)


def _is_soft_entertainment_headline(headline: str) -> bool:
    return bool(_ENTERTAINMENT_HEADLINE_RE.search(str(headline or "")))


def _reroute_sector_code(headline: str, current_code: str) -> str:
    h = str(headline or "")
    code = str(current_code or "").strip().lower()
    if code == "news" and _AI_POLICY_RE.search(h):
        pure_politics = re.search(
            r"thủ tướng|quốc hội|bầu cử|ngoại giao|chiến tranh|ngừng bắn|hội nghị thượng đỉnh",
            h,
            re.I,
        )
        if not pure_politics or re.search(r"\bai\b|chip|openai|nvidia|llm|executive order", h, re.I):
            if re.search(r"\bai\b|chip|openai|nvidia|llm|executive order|oversight|semiconductor", h, re.I):
                return "tech"
    if code == "news" and _EDUCATION_TRENDS_RE.search(h):
        return "trends"
    if code == "news" and _SPACE_TECH_RE.search(h):
        if not re.search(
            r"thủ tướng|quốc hội|bầu cử|ngoại giao|chiến tranh|trừng phạt|sanction",
            h,
            re.I,
        ):
            return "tech"
    return code if code in DIGEST_SECTOR_CODES else "trends"


def _apply_digest_sector_hygiene(
    summary: dict[str, Any], *, url_index: DigestUrlIndex | None = None
) -> dict[str, Any]:
    """Routing, lọc giải trí, gom cluster, cap E10 toàn bài, polish fields."""
    sectors_in = {
        str(s.get("code") or "").strip().lower(): s
        for s in (summary.get("sectors") or [])
        if isinstance(s, dict) and str(s.get("code") or "").strip()
    }
    buckets: dict[str, list[dict[str, Any]]] = {code: [] for code, _ in DIGEST_FOUR_SECTORS}
    for code, _ in DIGEST_FOUR_SECTORS:
        sec = sectors_in.get(code, {})
        for row in sec.get("sub_topics") or []:
            if not isinstance(row, dict):
                continue
            headline = str(row.get("headline") or row.get("title") or "").strip()
            if (
                not headline
                or _is_soft_entertainment_headline(headline)
                or _is_low_value_digest_item(headline)
            ):
                if headline and _is_low_value_digest_item(headline):
                    print(
                        f"WARN digest polish: drop low-value item ({code}): {headline[:70]}",
                        file=sys.stderr,
                    )
                continue
            target = _reroute_sector_code(headline, code)
            buckets[target].append(row)
    out_sectors: list[dict[str, Any]] = []
    for code, label in DIGEST_FOUR_SECTORS:
        src = sectors_in.get(code, {})
        sector_rows = buckets[code]
        if code == "finance":
            sector_rows = _merge_bitcoin_finance_rows(sector_rows)
        rows = _cluster_sub_topics_in_sector(sector_rows, code)
        rows = [_polish_sub_topic_fields(r, code, url_index=url_index) for r in rows]
        rows = _dedupe_sub_topics_by_headline(rows, code)
        rows = [_sanitize_sub_topic_urls(r, url_index, code) for r in rows]
        rows.sort(key=lambda r: _sub_topic_sort_key(r, 0))
        out_sectors.append(
            {
                "code": code,
                "name": str(src.get("name") or "").strip() or label,
                "summary": str(src.get("summary") or "").strip(),
                "sub_topics": rows[:DIGEST_PARSER_MAX_SUB_TOPICS_PER_SECTOR],
            }
        )
    summary["sectors"] = out_sectors
    return _consolidate_e10_globally(summary, url_index=url_index)


def supplement_notable_from_sectors(
    summary: dict[str, Any], *, url_index: DigestUrlIndex | None = None
) -> dict[str, Any]:
    """Fallback notable khi Gemini trả quá ít nhưng sectors có A/B."""
    notable = [
        n for n in (summary.get("notable_articles") or []) if isinstance(n, dict)
    ]
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    for n in notable:
        u = str(n.get("url") or "").strip()
        t = _headline_dedupe_key(str(n.get("title") or ""))
        if u:
            seen_urls.add(u)
        if t:
            seen_titles.add(t)
    if len(notable) >= _NOTABLE_MIN_FALLBACK:
        summary["notable_articles"] = notable[:DIGEST_PARSER_MAX_NOTABLE]
        return summary

    ab_total = 0
    for sec in summary.get("sectors") or []:
        if not isinstance(sec, dict):
            continue
        for row in sec.get("sub_topics") or []:
            if isinstance(row, dict) and str(row.get("priority_tier") or "").upper()[:1] in (
                "A",
                "B",
            ):
                ab_total += 1
    if ab_total < _NOTABLE_MIN_FALLBACK:
        summary["notable_articles"] = notable[:DIGEST_PARSER_MAX_NOTABLE]
        return summary

    for sec in summary.get("sectors") or []:
        if not isinstance(sec, dict):
            continue
        if len(notable) >= _NOTABLE_TARGET_FALLBACK:
            break
        code = str(sec.get("code") or "")
        picked = 0
        for row in sec.get("sub_topics") or []:
            if not isinstance(row, dict) or picked >= 2:
                break
            tier = str(row.get("priority_tier") or "").upper()[:1]
            if tier not in ("A", "B"):
                continue
            headline = str(row.get("headline") or "").strip()
            urls = [str(u).strip() for u in (row.get("source_urls") or []) if str(u).strip()]
            u = urls[0] if urls else ""
            tkey = _headline_dedupe_key(headline)
            if (u and u in seen_urls) or (tkey and tkey in seen_titles):
                continue
            if u:
                seen_urls.add(u)
            if tkey:
                seen_titles.add(tkey)
            why_raw = str(row.get("summary_hint") or row.get("reason_selected") or "").strip()
            why_notable = (
                why_raw
                if why_raw and not _is_generic_digest_copy(why_raw)
                else _infer_summary_hint(headline, str(sec.get("code") or "notable"))
            )
            notable.append(
                {
                    "title": _vietnamese_public_headline(
                        _editorialize_digest_headline(headline), str(sec.get("code") or "")
                    ),
                    "source": "",
                    "url": u,
                    "why_notable": why_notable,
                    "priority_tier": tier,
                }
            )
            picked += 1
    summary["notable_articles"] = [
        _sanitize_notable_url(n, url_index) for n in notable[:DIGEST_PARSER_MAX_NOTABLE]
    ]
    return summary


def _infer_digest_sector_code(name: str) -> str:
    n = (name or "").lower()
    if any(k in n for k in ("công nghệ", "cong nghe", "ai", "khoa học", "bán dẫn", "tech", "chip")):
        return "tech"
    if any(k in n for k in ("chính trị", "thời sự", "ngoại giao", "địa chính", "quốc tế", "news")):
        return "news"
    if any(k in n for k in ("xu hướng", "đời sống", "quan điểm", "xã hội", "trends")):
        return "trends"
    if any(k in n for k in ("kinh tế", "tài chính", "chứng khoán", "bất động", "crypto", "finance")):
        return "finance"
    return "trends"


def _coerce_depth_level(raw: Any) -> str:
    d = str(raw or "").strip().lower()
    return d if d in NEWSROOM_DEPTH_LEVELS else "deep"


def _coerce_str_list(val: Any, *, max_items: int = 8) -> list[str]:
    if isinstance(val, list):
        out = [str(x).strip() for x in val if str(x).strip()]
    elif isinstance(val, str) and val.strip():
        out = [ln.strip() for ln in re.split(r"[\n;]+", val) if ln.strip()]
    else:
        out = []
    return out[:max_items]


def _sanitize_representative_sources(
    sources: Any,
    *,
    headline: str,
    index: DigestUrlIndex | None,
    sector_code: str,
    context: str = "",
    main_developments: list[str] | None = None,
) -> list[dict[str, str]]:
    from scripts.newsroom_source_match import sanitize_representative_sources as _nr_sanitize

    return _nr_sanitize(
        sources,
        headline=headline,
        index=index,
        sector_code=sector_code,
        context=context,
        main_developments=main_developments,
    )


def _sanitize_story_dossier(
    row: dict[str, Any],
    *,
    index: DigestUrlIndex | None,
    sector_code: str,
) -> dict[str, Any]:
    from scripts.newsroom_copy import soften_newsroom_text

    out = dict(row)
    title = str(out.get("title") or out.get("headline") or "").strip()
    if title:
        out["title"] = soften_newsroom_text(
            _vietnamese_public_headline(_editorialize_digest_headline(title))
        )

    out["summary"] = soften_newsroom_text(str(out.get("summary") or "").strip())
    out["depth_level"] = _coerce_depth_level(out.get("depth_level"))
    out["sub_sector"] = str(out.get("sub_sector") or "").strip()
    out["main_developments"] = [
        soften_newsroom_text(x)
        for x in _coerce_str_list(out.get("main_developments"), max_items=6)
    ]
    out["why_it_matters"] = soften_newsroom_text(str(out.get("why_it_matters") or "").strip())
    out["affected_groups"] = _coerce_str_list(out.get("affected_groups"), max_items=8)
    out["watch_next"] = _coerce_str_list(out.get("watch_next"), max_items=6)
    dossier_context = " ".join(
        part
        for part in (
            str(out.get("summary") or ""),
            str(out.get("why_it_matters") or ""),
            " ".join(out.get("main_developments") or []),
        )
        if part.strip()
    )
    out["representative_sources"] = _sanitize_representative_sources(
        out.get("representative_sources"),
        headline=title,
        index=index,
        sector_code=sector_code,
        context=dossier_context,
        main_developments=out.get("main_developments"),
    )
    try:
        out["rank"] = int(out.get("rank") or 0) or 999
    except (TypeError, ValueError):
        out["rank"] = 999
    return out


def _is_generic_watch_line(text: str) -> bool:
    t = str(text or "").strip().lower()
    if not t:
        return True
    generic = (
        "theo dõi diễn biến tiếp trong 24-72 giờ",
        "theo dõi diễn biến tiếp trong 24–72 giờ",
        "theo dõi diễn biến tiếp",
    )
    return any(g in t for g in generic)


def _strip_generic_watch_lines(lines: list[str]) -> list[str]:
    return [x for x in lines if not _is_generic_watch_line(x)]


def _sanitize_executive_briefing(
    val: Any, *, index: DigestUrlIndex | None = None
) -> dict[str, Any]:
    if isinstance(val, str):
        body = str(val).strip()
        return {
            "title": "Tóm tắt tổng quan 48h",
            "sections": {},
            "content": body,
            "representative_sources": [],
            "most_mentioned_topics": [],
            "hottest_topics": [],
            "emerging_signals": [],
            "watch_next": [],
        }
    src = val if isinstance(val, dict) else {}

    def _topic_rows(rows: Any, *, keys: tuple[str, ...]) -> list[dict[str, str]]:
        out_rows: list[dict[str, str]] = []
        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, dict):
                continue
            obj = {k: str(row.get(k) or "").strip() for k in keys}
            if any(obj.values()):
                out_rows.append(obj)
        return out_rows[:8]

    sec_src = src.get("sections") if isinstance(src.get("sections"), dict) else {}
    sections = {
        k: str(sec_src.get(k) or "").strip()
        for k in (
            "main_picture",
            "most_mentioned",
            "top_stories",
            "sector_impacts",
            "watch_24_72h",
        )
        if str(sec_src.get(k) or "").strip()
    }
    from scripts.newsroom_copy import soften_prose

    title = str(src.get("title") or "Tóm tắt tổng quan 48h").strip() or "Tóm tắt tổng quan 48h"
    content = soften_prose(str(src.get("content") or "").strip())
    sections = {k: soften_prose(v) for k, v in sections.items()}
    if not content and sections:
        ordered = [
            sections.get("main_picture", ""),
            sections.get("most_mentioned", ""),
            sections.get("top_stories", ""),
            sections.get("sector_impacts", ""),
            sections.get("watch_24_72h", ""),
        ]
        content = "\n\n".join(part.strip() for part in ordered if str(part).strip())
    rep_sources = _sanitize_representative_sources(
        src.get("representative_sources"),
        headline=title,
        index=index,
        sector_code="",
        context=content or " ".join(sections.values()),
    )
    return {
        "title": title,
        "sections": sections,
        "content": content,
        "representative_sources": rep_sources,
        "most_mentioned_topics": _topic_rows(
            src.get("most_mentioned_topics"),
            keys=("topic", "why_mentioned", "evidence_hint"),
        ),
        "hottest_topics": _topic_rows(
            src.get("hottest_topics"),
            keys=("topic", "why_hot", "impact", "evidence_hint"),
        ),
        "emerging_signals": _topic_rows(
            src.get("emerging_signals"),
            keys=("signal", "why_watch"),
        ),
        "watch_next": _strip_generic_watch_lines(
            _coerce_str_list(src.get("watch_next"), max_items=8)
        ),
    }


def _sanitize_subsector_briefs(
    rows: Any,
    *,
    index: DigestUrlIndex | None,
    sector_code: str,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip()
        overview = str(row.get("overview") or "").strip()
        if not name or not overview:
            continue
        srcs = _sanitize_representative_sources(
            row.get("representative_sources"),
            headline=name,
            index=index,
            sector_code=sector_code,
            context=overview,
        )
        if not srcs:
            continue
        out.append(
            {
                "name": name,
                "overview": overview,
                "key_points": _coerce_str_list(row.get("key_points"), max_items=8),
                "key_story_titles": _coerce_str_list(row.get("key_story_titles"), max_items=12),
                "representative_sources": srcs,
            }
        )
    return out[:10]


def _sanitize_front_page_item(
    row: dict[str, Any],
    *,
    index: DigestUrlIndex | None,
) -> dict[str, Any]:
    out = dict(row)
    title = str(out.get("title") or "").strip()
    if title:
        out["title"] = _vietnamese_public_headline(_editorialize_digest_headline(title))
    out["one_sentence"] = str(out.get("one_sentence") or "").strip()
    out["why_it_matters"] = str(out.get("why_it_matters") or "").strip()
    out["watch_next"] = str(out.get("watch_next") or "").strip()
    from scripts.newsroom_copy import soften_newsroom_text
    from scripts.newsroom_source_match import sanitize_front_page_sources

    for key in ("title", "one_sentence", "why_it_matters", "watch_next"):
        if out.get(key):
            out[key] = soften_newsroom_text(str(out[key]))
    ctx = " ".join(
        part
        for part in (
            str(out.get("one_sentence") or ""),
            str(out.get("why_it_matters") or ""),
        )
        if part.strip()
    )
    out["source_urls"] = sanitize_front_page_sources(
        [str(u) for u in (out.get("source_urls") or []) if str(u).strip()],
        headline=title,
        index=index,
        context=ctx,
    )
    try:
        out["rank"] = int(out.get("rank") or 0) or 999
    except (TypeError, ValueError):
        out["rank"] = 999
    return out


def normalize_newsroom_brief(
    summary: dict[str, Any], *, url_index: DigestUrlIndex | None = None
) -> dict[str, Any]:
    """Post-merge newsroom schema: sanitize URLs, sort ranks, parser caps."""
    out = dict(summary)
    out["brief_format"] = NEWSROOM_BRIEF_FORMAT
    out["title"] = str(out.get("title") or "").strip() or (
        "Tổng hợp tin tức toàn cầu và Việt Nam 48 giờ"
    )
    if not str(out.get("reading_time_minutes") or "").strip():
        out["reading_time_minutes"] = "auto"
    from scripts.newsroom_copy import soften_editor_note, soften_headline, soften_prose

    out["editor_note"] = soften_editor_note(str(out.get("editor_note") or "").strip())
    out["executive_briefing"] = _sanitize_executive_briefing(
        out.get("executive_briefing"), index=url_index
    )

    fp_raw = out.get("front_page") if isinstance(out.get("front_page"), list) else []
    front: list[dict[str, Any]] = []
    for row in fp_raw:
        if not isinstance(row, dict):
            continue
        item = _sanitize_front_page_item(row, index=url_index)
        if item.get("title"):
            front.append(item)
    front.sort(key=lambda r: int(r.get("rank") or 999))
    out["front_page"] = front[:DIGEST_PARSER_MAX_FRONT_PAGE]

    buckets: dict[str, dict[str, Any]] = {
        code: {
            "code": code,
            "name": label,
            "sector_thesis": "",
            "subsector_briefs": [],
            "story_dossiers": [],
        }
        for code, label in DIGEST_FOUR_SECTORS
    }
    for sec in out.get("sector_deep_briefs") or []:
        if not isinstance(sec, dict):
            continue
        code = str(sec.get("code") or "").strip().lower()
        if code not in buckets:
            code = _infer_digest_sector_code(str(sec.get("name") or ""))
        bucket = buckets[code]
        bucket["name"] = str(sec.get("name") or "").strip() or bucket["name"]
        thesis = str(sec.get("sector_thesis") or sec.get("summary") or "").strip()
        if thesis:
            bucket["sector_thesis"] = soften_prose(thesis)
        subs = _sanitize_subsector_briefs(
            sec.get("subsector_briefs"),
            index=url_index,
            sector_code=code,
        )
        bucket["subsector_briefs"].extend(subs)
        dossiers: list[dict[str, Any]] = []
        for d in sec.get("story_dossiers") or []:
            if not isinstance(d, dict):
                continue
            sd = _sanitize_story_dossier(d, index=url_index, sector_code=code)
            sd["watch_next"] = _strip_generic_watch_lines(sd.get("watch_next") or [])
            if sd.get("title"):
                dossiers.append(sd)
        dossiers.sort(key=lambda r: int(r.get("rank") or 999))
        bucket["story_dossiers"].extend(dossiers)

    norm_sectors: list[dict[str, Any]] = []
    for code, label in DIGEST_FOUR_SECTORS:
        b = buckets[code]
        seen_t: set[str] = set()
        deduped: list[dict[str, Any]] = []
        for d in b["story_dossiers"]:
            key = _headline_dedupe_key(str(d.get("title") or ""))
            if key and key in seen_t:
                continue
            if key:
                seen_t.add(key)
            deduped.append(d)
        b["story_dossiers"] = deduped[:DIGEST_PARSER_MAX_STORY_DOSSIERS_PER_SECTOR]
        seen_sub: set[str] = set()
        sub_clean: list[dict[str, Any]] = []
        for sb in b["subsector_briefs"]:
            nm = str(sb.get("name") or "").strip().lower()
            if not nm or nm in seen_sub:
                continue
            seen_sub.add(nm)
            sub_clean.append(sb)
        norm_sectors.append(
            {
                "code": code,
                "name": b["name"] or label,
                "sector_thesis": b["sector_thesis"],
                "subsector_briefs": sub_clean,
                "story_dossiers": b["story_dossiers"],
            }
        )
    out["sector_deep_briefs"] = norm_sectors

    watch: list[dict[str, Any]] = []
    for row in out.get("watchlist_24_72h") or []:
        if not isinstance(row, dict):
            continue
        watch.append(
            {
                "theme": str(row.get("theme") or "").strip(),
                "what_to_watch": str(row.get("what_to_watch") or "").strip(),
                "why": str(row.get("why") or "").strip(),
            }
        )
    out["watchlist_24_72h"] = [w for w in watch if w.get("theme")][:DIGEST_PARSER_MAX_WATCHLIST]

    desk: list[dict[str, Any]] = []
    for row in out.get("source_desk") or []:
        if not isinstance(row, dict):
            continue
        topic = str(row.get("topic") or "").strip()
        srcs = _sanitize_representative_sources(
            row.get("representative_sources"),
            headline=topic,
            index=url_index,
            sector_code="",
        )
        if topic and srcs:
            desk.append({"topic": topic, "representative_sources": srcs})
    out["source_desk"] = desk[:DIGEST_PARSER_MAX_SOURCE_DESK]
    out["gaps_and_limits"] = str(out.get("gaps_and_limits") or "").strip()
    from scripts.newsroom_main_quality import enforce_newsroom_main_editorial_quality

    return enforce_newsroom_main_editorial_quality(out, url_index=url_index)


_SECTOR_THESIS_STOPWORDS = frozenset(
    {
        "trong",
        "theo",
        "này",
        "được",
        "các",
        "cho",
        "với",
        "từ",
        "khi",
        "một",
        "nhiều",
        "thị",
        "trường",
        "ngành",
        "tin",
        "bài",
        "quá",
        "48h",
        "giờ",
    }
)

_SHALLOW_SECTOR_THESIS_MARKERS = (
    "tiếp tục là điểm sáng",
    "tiếp tục là động lực",
    "động lực tăng trưởng",
    "đang tập trung vào",
    "đẩy mạnh đầu tư",
    "điểm sáng thu hút vốn",
    "tâm điểm",
    "nổi bật vì",
)


def _sector_thesis_entity_count(text: str) -> int:
    return len(
        re.findall(
            r"\b(?:Bitcoin|Ethereum|Fed|VN-Index|Nvidia|OpenAI|SpaceX|Iran|Trump|FPT|"
            r"World Cup|Brent|Alphabet|Microsoft|Iran|Hormuz|"
            r"[A-ZÀ-Ỹ][\wÀ-ỹ]{2,})\b",
            text,
        )
    )


def _is_shallow_or_generic_sector_thesis(thesis: str) -> bool:
    t = thesis.strip()
    if not t:
        return False
    lower = t.lower()
    sentence_breaks = len(re.findall(r"[.!?…]", t))
    if sentence_breaks <= 1 and len(t) < 220:
        return True
    markers = sum(1 for m in _SHALLOW_SECTOR_THESIS_MARKERS if m in lower)
    entities = _sector_thesis_entity_count(t)
    if markers >= 1 and entities < 2 and len(t) < 420:
        return True
    return False


def _dossier_title_keywords(title: str) -> list[str]:
    words = re.findall(r"[\wÀ-ỹ]{5,}", str(title or ""))
    out: list[str] = []
    for w in words:
        lw = w.lower()
        if lw in _SECTOR_THESIS_STOPWORDS:
            continue
        out.append(lw)
    return out[:4]


def _sector_thesis_missing_dossier_clusters(thesis: str, dossiers: list[dict[str, Any]]) -> list[str]:
    """Dossier titles whose main keywords do not appear in sector_thesis."""
    lower = thesis.lower()
    missing: list[str] = []
    for d in dossiers:
        if not isinstance(d, dict):
            continue
        title = str(d.get("title") or "").strip()
        if not title:
            continue
        keys = _dossier_title_keywords(title)
        if keys and not any(k in lower for k in keys):
            missing.append(title)
    return missing


def _looks_english_heavy_public_copy(text: str) -> bool:
    raw = str(text or "").strip()
    if len(raw) < 48:
        return False
    latin_tokens = re.findall(r"[A-Za-z][A-Za-z'-]{2,}", raw)
    if len(latin_tokens) < 8:
        return False
    vi_chars = re.findall(
        r"[àáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]",
        raw,
        re.I,
    )
    return len(latin_tokens) >= max(8, len(vi_chars) * 2)


_PROPER_NOUN_KNOWN_RE = re.compile(
    r"\b(?:Bitcoin|Ethereum|Fed|VN-Index|VNIndex|Nvidia|OpenAI|SpaceX|Iran|Trump|FPT|"
    r"World Cup|Brent|Alphabet|Microsoft|Google|Apple|Tesla|Amazon|Meta|Cursor)\b"
)
# Cum 2-3 tu viet hoa lien tiep (vd "Donald Trump", "World Cup 2026") - it kha nang
# la dau cau tieng Viet thong thuong (chi 1 tu viet hoa dau cau). KHONG bat tu don
# le viet hoa de tranh false positive voi tu dau cau tieng Viet (vd "Trong", "Dong").
_PROPER_NOUN_MULTIWORD_RE = re.compile(
    r"\b[A-ZÀ-Ỹ][\wÀ-ỹ]{2,}(?:\s+[A-ZÀ-Ỹ][\wÀ-ỹ]{2,}){1,2}\b"
)

_ENTITY_GROUNDING_STOPWORDS = {
    "việt nam",
    "trung quốc",
    "hoa kỳ",
    "hà nội",
    "châu á",
    "đông nam á",
}


def _extract_candidate_entities(text: str, max_items: int = 12) -> list[str]:
    raw = str(text or "")
    hits = _PROPER_NOUN_KNOWN_RE.findall(raw) + _PROPER_NOUN_MULTIWORD_RE.findall(raw)
    out: list[str] = []
    seen: set[str] = set()
    for h in hits:
        h = h.strip()
        if len(h) < 4:
            continue
        key = h.lower()
        if key in _ENTITY_GROUNDING_STOPWORDS or key in seen:
            continue
        seen.add(key)
        out.append(h)
        if len(out) >= max_items:
            break
    return out


def find_ungrounded_entities(
    text: str,
    representative_sources: list[dict[str, Any]] | None = None,
    full_corpus_titles_blob: str = "",
) -> list[str]:
    """Best-effort lint: phát hiện thực thể trong `text` không thấy ở nguồn/corpus.

    Không phải parser ngữ nghĩa hoàn hảo — mục tiêu là bắt được trường hợp rõ
    như "SpaceX IPO"/"Cursor M&A" khi 2 cụm từ này không xuất hiện ở đâu trong
    input, không phải đối chiếu ngữ nghĩa chính xác tuyệt đối.
    """
    entities = _extract_candidate_entities(text)
    if not entities:
        return []
    src_blob = " ".join(
        f"{s.get('title', '')} {s.get('excerpt', '')}"
        for s in (representative_sources or [])
        if isinstance(s, dict)
    ).lower()
    corpus_blob = (full_corpus_titles_blob or "").lower()
    if not corpus_blob and not src_blob:
        return []
    missing: list[str] = []
    for ent in entities:
        low = ent.lower()
        if low in src_blob or low in corpus_blob:
            continue
        missing.append(ent)
    return missing


def validate_newsroom_brief(
    summary: dict[str, Any], corpus_titles_blob: str = ""
) -> list[str]:
    warnings: list[str] = []
    if not str(summary.get("editor_note") or "").strip():
        warnings.append("editor_note trống.")
    fp = summary.get("front_page") if isinstance(summary.get("front_page"), list) else []
    eb = summary.get("executive_briefing") if isinstance(summary.get("executive_briefing"), dict) else {}
    eb_content = str(eb.get("content") or "").strip()
    eb_sections = eb.get("sections") if isinstance(eb.get("sections"), dict) else {}
    section_text = " ".join(str(v).strip() for v in eb_sections.values() if str(v).strip())
    eb_total = len(eb_content) + len(section_text)
    if not eb_content and not section_text:
        warnings.append("executive_briefing trống (thiếu content và sections).")
    elif eb_total < 1500:
        warnings.append("executive_briefing quá ngắn (<1500 ký tự tổng — có thể giống outline).")
    for key, label in (
        ("main_picture", "main_picture"),
        ("most_mentioned", "most_mentioned"),
        ("top_stories", "top_stories"),
        ("sector_impacts", "sector_impacts"),
    ):
        sec_len = len(str(eb_sections.get(key) or "").strip())
        if sec_len and sec_len < 120:
            warnings.append(
                f"executive_briefing.sections.{label} quá ngắn ({sec_len} ký tự) — có thể giống outline."
            )
    if not (eb.get("representative_sources") or []):
        warnings.append("executive_briefing thiếu representative_sources.")
    generic_hits = sum(
        1
        for frag in ("đáng chú ý", "bức tranh 48h", "diễn biến phức tạp", "tác động lớn")
        if frag in eb_content.lower()
    )
    if generic_hits >= 2 and len(re.findall(r"[A-ZÀ-Ỹ][\wÀ-ỹ]{2,}", eb_content)) < 15:
        warnings.append("executive_briefing.content có dấu hiệu generic, thiếu actor/sự kiện cụ thể.")
    eb_ungrounded = find_ungrounded_entities(
        eb_content, eb.get("representative_sources"), corpus_titles_blob
    )
    if eb_ungrounded:
        warnings.append(
            "executive_briefing.content nhắc thực thể không thấy trong corpus/representative_sources "
            f"(có thể hallucinate): {', '.join(eb_ungrounded)}."
        )
    for i, item in enumerate(fp):
        if not isinstance(item, dict):
            continue
        if not str(item.get("why_it_matters") or "").strip():
            warnings.append(f"front_page[{i}] thiếu why_it_matters.")
        if not str(item.get("watch_next") or "").strip():
            warnings.append(f"front_page[{i}] thiếu watch_next.")
    sdb = summary.get("sector_deep_briefs") if isinstance(summary.get("sector_deep_briefs"), list) else []
    if len(sdb) < DIGEST_MIN_SECTORS_FINAL:
        warnings.append(f"sector_deep_briefs chỉ có {len(sdb)} sector.")
    total_dossiers_all = sum(
        len([d for d in (sec.get("story_dossiers") or []) if isinstance(d, dict)])
        for sec in sdb
        if isinstance(sec, dict)
    )
    if len(sdb) >= DIGEST_MIN_SECTORS_FINAL and total_dossiers_all == 0:
        warnings.append(
            "sector_deep_briefs có đủ 4 sector nhưng KHÔNG sector nào có story_dossiers "
            "— có dấu hiệu output bị rút gọn quá mức (rủi ro front_page/storyDossiers/sourceDesk đều trống)."
        )
    if not fp:
        rich_dossier_count = sum(
            1
            for sec in sdb
            if isinstance(sec, dict)
            for d in (sec.get("story_dossiers") or [])
            if isinstance(d, dict)
            and (
                str(d.get("depth_level") or "").strip().lower() == "major"
                or len(d.get("main_developments") or []) >= 3
            )
        )
        if total_dossiers_all >= 3 or rich_dossier_count >= 1:
            warnings.append(
                f"front_page trống dù sector_deep_briefs có {total_dossiers_all} dossier "
                f"({rich_dossier_count} dossier depth=major/nhiều ý) — khả năng cao có tin đạt tiêu chí "
                "highlight bị bỏ sót khỏi front_page."
            )
    for i, sec in enumerate(sdb):
        if not isinstance(sec, dict):
            continue
        code = str(sec.get("code") or "?")
        thesis = str(sec.get("sector_thesis") or "").strip()
        if not thesis:
            warnings.append(f"sector_deep_briefs[{i}] ({code}) thiếu sector_thesis.")
        dossiers = [d for d in (sec.get("story_dossiers") or []) if isinstance(d, dict)]
        rich_dossiers = sum(
            1
            for d in dossiers
            if str(d.get("why_it_matters") or "").strip()
            or len(d.get("main_developments") or []) >= 2
        )
        if rich_dossiers >= 2 and len(thesis) < 800:
            warnings.append(
                f"sector_deep_briefs[{i}] ({code}) sector_thesis quá ngắn "
                f"({len(thesis)} ký tự) dù có {rich_dossiers} dossier — có thể giống nối dossier rời."
            )
        if _is_shallow_or_generic_sector_thesis(thesis):
            warnings.append(
                f"sector_deep_briefs[{i}] ({code}) sector_thesis quá nông/generic — thiếu actor/sự kiện cụ thể."
            )
        elif len(thesis) >= 120 and _sector_thesis_entity_count(thesis) < 2:
            warnings.append(
                f"sector_deep_briefs[{i}] ({code}) sector_thesis thiếu thực thể/sự kiện cụ thể (tên, ticker, tổ chức)."
            )
        if rich_dossiers >= 2:
            missing_clusters = _sector_thesis_missing_dossier_clusters(thesis, dossiers)
            if len(missing_clusters) >= max(2, len(dossiers) // 2):
                sample = ", ".join(missing_clusters[:3])
                warnings.append(
                    f"sector_deep_briefs[{i}] ({code}) sector_thesis chưa phản ánh cụm dossier chính: {sample}."
                )
        sector_sources: list[dict[str, Any]] = []
        for d in dossiers:
            sector_sources.extend(
                s for s in (d.get("representative_sources") or []) if isinstance(s, dict)
            )
        sector_ungrounded = find_ungrounded_entities(thesis, sector_sources, corpus_titles_blob)
        if sector_ungrounded:
            warnings.append(
                f"sector_deep_briefs[{i}] ({code}) sector_thesis nhắc thực thể không thấy trong "
                f"corpus/representative_sources: {', '.join(sector_ungrounded)}."
            )
        leak_frags = (
            "chỉ nên xuất hiện",
            "không nên đưa vào",
            "theo rule",
            "theo prompt",
            "dữ liệu cho thấy lặp quá nhiều",
        )
        if any(frag in thesis.lower() for frag in leak_frags):
            warnings.append(
                f"sector_deep_briefs[{i}] ({code}) sector_thesis có dấu hiệu lộ rule/prompt nội bộ."
            )
        for k, sb in enumerate(sec.get("subsector_briefs") or []):
            if not isinstance(sb, dict):
                continue
            if not str(sb.get("overview") or "").strip():
                warnings.append(f"sector_deep_briefs[{i}] subsector_briefs[{k}] thiếu overview.")
            if (
                len(str(sb.get("overview") or "").strip()) > 180
                and not (sb.get("representative_sources") or [])
            ):
                warnings.append(
                    f"sector_deep_briefs[{i}] subsector_briefs[{k}] thiếu representative_sources."
                )
        for j, d in enumerate(sec.get("story_dossiers") or []):
            if not isinstance(d, dict):
                continue
            if not str(d.get("why_it_matters") or "").strip():
                warnings.append(f"sector_deep_briefs[{i}] dossiers[{j}] thiếu why_it_matters.")
            devs = d.get("main_developments") if isinstance(d.get("main_developments"), list) else []
            if len(devs) < 2:
                warnings.append(
                    f"sector_deep_briefs[{i}] dossiers[{j}] main_developments < 2 (headline-list risk)."
                )
            if _is_generic_digest_copy(str(d.get("why_it_matters") or "")):
                warnings.append(f"sector_deep_briefs[{i}] dossiers[{j}] why_it_matters generic.")
            if not (d.get("representative_sources") or []):
                warnings.append(f"sector_deep_briefs[{i}] dossiers[{j}] thiếu representative_sources.")
    return warnings


def newsroom_brief_to_legacy_sectors(summary: dict[str, Any]) -> list[dict[str, Any]]:
    """Map newsroom → legacy `sectors`/`sub_topics` cho build/compat."""
    legacy: list[dict[str, Any]] = []
    for sec in summary.get("sector_deep_briefs") or []:
        if not isinstance(sec, dict):
            continue
        code = str(sec.get("code") or "").strip().lower()
        subs: list[dict[str, Any]] = []
        for d in sec.get("story_dossiers") or []:
            if not isinstance(d, dict):
                continue
            urls = [
                str(s.get("url") or "").strip()
                for s in (d.get("representative_sources") or [])
                if isinstance(s, dict) and str(s.get("url") or "").strip()
            ]
            subs.append(
                {
                    "importance_rank": d.get("rank") or len(subs) + 1,
                    "priority_tier": "A" if d.get("depth_level") == "major" else "B",
                    "headline": str(d.get("title") or "").strip(),
                    "summary_hint": str(d.get("summary") or "").strip(),
                    "source_urls": urls[:3],
                    "reason_selected": str(d.get("why_it_matters") or "")[:280],
                }
            )
        legacy.append(
            {
                "code": code,
                "name": str(sec.get("name") or "").strip(),
                "summary": str(sec.get("sector_thesis") or "").strip(),
                "sub_topics": subs,
            }
        )
    return legacy


def normalize_digest_summary(
    summary: dict[str, Any], *, url_index: DigestUrlIndex | None = None
) -> dict[str, Any]:
    """Post-merge: sắp xếp & dedupe — không cắt quota editorial."""
    if _is_newsroom_brief(summary):
        return normalize_newsroom_brief(summary, url_index=url_index)
    if not isinstance(summary, dict):
        return summary
    out = dict(summary)
    out["title"] = str(out.get("title") or "").strip() or (
        "Tổng hợp tin tức toàn cầu và Việt Nam 48 giờ"
    )
    rt = str(out.get("reading_time_minutes") or "").strip()
    if not rt:
        out["reading_time_minutes"] = "auto"
    bullets = _normalize_executive_overview_bullets(out.get("executive_overview"))
    if bullets:
        out["executive_overview"] = bullets

    out = _apply_digest_sector_hygiene(out, url_index=url_index)
    out = supplement_notable_from_sectors(out, url_index=url_index)
    out = _scrub_digest_public_copy(out, url_index=url_index)
    out = _enforce_digest_public_polish(out, url_index=url_index)

    sectors = out.get("sectors") if isinstance(out.get("sectors"), list) else []
    norm_sectors: list[dict[str, Any]] = []
    for sec in sectors:
        if not isinstance(sec, dict):
            continue
        sec_copy = dict(sec)
        subs = sec_copy.get("sub_topics") if isinstance(sec_copy.get("sub_topics"), list) else []
        if subs:
            indexed = [(i, r) for i, r in enumerate(subs) if isinstance(r, dict)]
            indexed.sort(key=lambda pair: _sub_topic_sort_key(pair[1], pair[0]))
            sorted_rows = [r for _, r in indexed]
            if len(sorted_rows) > DIGEST_PARSER_MAX_SUB_TOPICS_PER_SECTOR:
                sorted_rows = sorted_rows[:DIGEST_PARSER_MAX_SUB_TOPICS_PER_SECTOR]
            sec_copy["sub_topics"] = sorted_rows
        norm_sectors.append(sec_copy)
    out["sectors"] = norm_sectors

    notable = out.get("notable_articles") if isinstance(out.get("notable_articles"), list) else []
    norm_notable: list[dict[str, Any]] = []
    for n in notable:
        if not isinstance(n, dict):
            continue
        nc = dict(n)
        title = str(nc.get("title") or "").strip()
        if title:
            nc["title"] = _vietnamese_public_headline(_editorialize_digest_headline(title))
        why = str(nc.get("why_notable") or "").strip()
        if not why or _is_generic_digest_copy(why):
            nc["why_notable"] = _infer_summary_hint(nc.get("title") or title, "notable")
        norm_notable.append(_sanitize_notable_url(nc, url_index))
    if len(norm_notable) > DIGEST_PARSER_MAX_NOTABLE:
        norm_notable = norm_notable[:DIGEST_PARSER_MAX_NOTABLE]
    out["notable_articles"] = norm_notable
    for sec in out.get("sectors") or []:
        if not isinstance(sec, dict):
            continue
        code = str(sec.get("code") or "").strip().lower()
        sec["sub_topics"] = [
            _sanitize_sub_topic_urls(r, url_index, code)
            for r in (sec.get("sub_topics") or [])
            if isinstance(r, dict)
        ]
    return out


def validate_digest_public_polish(summary: dict[str, Any]) -> list[str]:
    """Cảnh báo nếu public copy vẫn generic hoặc headline chủ yếu tiếng Anh."""
    warnings: list[str] = []
    for i, sec in enumerate(summary.get("sectors") or []):
        if not isinstance(sec, dict):
            continue
        code = str(sec.get("code") or "?")
        for j, row in enumerate(sec.get("sub_topics") or []):
            if not isinstance(row, dict):
                continue
            hl = str(row.get("headline") or "")
            hint_txt = str(row.get("summary_hint") or "")
            if _is_generic_digest_copy(hint_txt) or _is_weak_summary_hint(hint_txt):
                warnings.append(f"sectors[{i}] ({code}) sub_topics[{j}] summary_hint vẫn generic/yếu.")
            if _is_generic_digest_copy(str(row.get("reason_selected") or "")):
                warnings.append(f"sectors[{i}] ({code}) sub_topics[{j}] reason_selected vẫn generic.")
            if hl and _headline_is_mostly_english(hl):
                warnings.append(f"sectors[{i}] ({code}) sub_topics[{j}] headline vẫn chủ yếu tiếng Anh.")
    iran_count = 0
    news_sec = next(
        (s for s in (summary.get("sectors") or []) if isinstance(s, dict) and s.get("code") == "news"),
        None,
    )
    if news_sec:
        for row in news_sec.get("sub_topics") or []:
            if isinstance(row, dict) and _IRAN_TOPIC_RE.search(str(row.get("headline") or "")):
                iran_count += 1
        if iran_count > 3:
            warnings.append(f"news có {iran_count} sub_topics Iran (nên gom ≤2 cụm).")
    return warnings


def validate_digest_multisector_coverage(summary: dict[str, Any]) -> list[str]:
    """Cảnh báo nhẹ sau merge (không fail pipeline, không ép quota)."""
    warnings: list[str] = []
    sectors = summary.get("sectors") if isinstance(summary.get("sectors"), list) else []
    if len(sectors) < DIGEST_MIN_SECTORS_FINAL:
        warnings.append(
            f"sectors chỉ có {len(sectors)} mục (mong đợi ≥{DIGEST_MIN_SECTORS_FINAL})."
        )
    notable = summary.get("notable_articles") if isinstance(summary.get("notable_articles"), list) else []
    if len(notable) > DIGEST_PARSER_MAX_NOTABLE:
        warnings.append(
            f"notable_articles có {len(notable)} mục (parser cap {DIGEST_PARSER_MAX_NOTABLE})."
        )
    exec_bullets = _normalize_executive_overview_bullets(summary.get("executive_overview"))
    if len(exec_bullets) > DIGEST_PARSER_MAX_EXEC_BULLETS:
        warnings.append(
            f"executive_overview có {len(exec_bullets)} bullet (parser cap {DIGEST_PARSER_MAX_EXEC_BULLETS})."
        )
    codes_seen: set[str] = set()
    for i, sec in enumerate(sectors):
        if not isinstance(sec, dict):
            continue
        code = str(sec.get("code") or "").strip().lower()
        if code:
            codes_seen.add(code)
        subs = sec.get("sub_topics") if isinstance(sec.get("sub_topics"), list) else []
        label = code or sec.get("name", "?")
        ab_count = sum(
            1
            for r in subs
            if isinstance(r, dict)
            and str(r.get("priority_tier") or "").strip().upper()[:1] in ("A", "B")
        )
        if len(subs) < 4 and ab_count < 3:
            warnings.append(
                f"sectors[{i}] ({label}) chỉ {len(subs)} sub_topics "
                f"(coverage sanity: kiểm tra đã bỏ sót luồng A/B trong partials chưa)."
            )
        if len(subs) > DIGEST_PARSER_MAX_SUB_TOPICS_PER_SECTOR:
            warnings.append(
                f"sectors[{i}] ({label}) có {len(subs)} sub_topics (parser cap {DIGEST_PARSER_MAX_SUB_TOPICS_PER_SECTOR})."
            )
        for j, row in enumerate(subs):
            if not isinstance(row, dict):
                continue
            urls = [str(u).strip() for u in (row.get("source_urls") or []) if str(u).strip()]
            if not urls:
                warnings.append(
                    f"sectors[{i}] ({label}) sub_topics[{j}] thiếu source_urls."
                )
            if not str(row.get("priority_tier") or "").strip():
                warnings.append(f"sectors[{i}] sub_topics[{j}] thiếu priority_tier (đã coerce B).")
            if not str(row.get("summary_hint") or "").strip():
                warnings.append(f"sectors[{i}] sub_topics[{j}] thiếu summary_hint.")
            if not str(row.get("reason_selected") or "").strip():
                warnings.append(f"sectors[{i}] sub_topics[{j}] thiếu reason_selected.")
            if _is_generic_digest_copy(str(row.get("summary_hint") or "")):
                warnings.append(
                    f"sectors[{i}] sub_topics[{j}] summary_hint vẫn generic (đã cố infer)."
                )
            if _is_generic_digest_copy(str(row.get("reason_selected") or "")):
                warnings.append(
                    f"sectors[{i}] sub_topics[{j}] reason_selected vẫn generic (đã cố infer)."
                )
            hl = str(row.get("headline") or "")
            if hl and _headline_is_mostly_english(hl):
                warnings.append(
                    f"sectors[{i}] sub_topics[{j}] headline vẫn chủ yếu tiếng Anh."
                )
            if len(urls) > 3:
                warnings.append(
                    f"sectors[{i}] ({label}) sub_topics[{j}] có {len(urls)} source_urls (nên ≤3)."
                )
    missing = DIGEST_SECTOR_CODES - codes_seen
    if missing and len(sectors) < DIGEST_MIN_SECTORS_FINAL:
        warnings.append(f"thiếu mã sector: {', '.join(sorted(missing))}")
    return warnings


def _headline_dedupe_key(text: str) -> str:
    return str(text or "").strip().lower()[:120]


def aggregate_partial_notable_articles(
    partials: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    seen_urls: set[str] = set()
    out: list[dict[str, Any]] = []
    for batch in partials:
        if not isinstance(batch, dict):
            continue
        raw = batch.get("summary")
        if not isinstance(raw, dict):
            continue
        for row in raw.get("notable_articles") or []:
            if not isinstance(row, dict):
                continue
            url = str(row.get("url") or "").strip()
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            out.append(row)
    return out


def _candidate_urls(row: dict[str, Any]) -> list[str]:
    return [str(u).strip() for u in (row.get("source_urls") or []) if str(u).strip()]


def _candidate_to_rep_sources(
    row: dict[str, Any],
    *,
    headline: str,
    url_index: DigestUrlIndex | None,
) -> list[dict[str, str]]:
    rep: list[dict[str, str]] = []
    for url in _candidate_urls(row)[:3]:
        art = None
        if url_index:
            art = url_index.by_url.get(_canonical_digest_url(url))
        host = (urlparse(url).hostname or "").replace("www.", "")
        rep.append(
            {
                "title": str((art or {}).get("title") or headline or host or url),
                "source": str((art or {}).get("source") or host or ""),
                "url": url,
            }
        )
    return rep


def _newsroom_dossier_target(pool_size: int, current: int) -> int:
    if pool_size < 8:
        return max(current, min(2, pool_size))
    if pool_size < 20:
        return max(current, 4)
    if pool_size < 35:
        return min(
            DIGEST_PARSER_MAX_STORY_DOSSIERS_PER_SECTOR,
            max(current, 6, min(8, pool_size // 5)),
        )
    return min(
        DIGEST_PARSER_MAX_STORY_DOSSIERS_PER_SECTOR,
        max(current, 8, min(12, pool_size // 4)),
    )


def supplement_newsroom_from_partials(
    summary: dict[str, Any],
    partials: list[dict[str, Any]],
    *,
    url_index: DigestUrlIndex | None = None,
) -> dict[str, Any]:
    """Bổ sung front_page / dossiers từ candidate pools khi merge Gemini quá mỏng."""
    if not partials or not _is_newsroom_brief(summary):
        return summary
    out = dict(summary)
    pools = {p["code"]: p for p in aggregate_partial_sector_candidates(partials)}

    fp: list[dict[str, Any]] = [
        dict(x) for x in (out.get("front_page") or []) if isinstance(x, dict)
    ]
    fp_keys = {_headline_dedupe_key(x.get("title") or "") for x in fp}
    rank = max((int(x.get("rank") or 0) for x in fp), default=0) + 1

    for row in aggregate_partial_notable_articles(partials):
        if len(fp) >= 8:
            break
        title = str(row.get("title") or "").strip()
        key = _headline_dedupe_key(title)
        if not title or key in fp_keys:
            continue
        fp_keys.add(key)
        fp.append(
            {
                "rank": rank,
                "title": title,
                "one_sentence": str(row.get("why_notable") or "").strip(),
                "why_it_matters": str(row.get("why_notable") or "").strip(),
                "watch_next": str(row.get("why_notable") or "").strip()[:120],
                "source_urls": [str(row.get("url") or "").strip()]
                if str(row.get("url") or "").strip()
                else [],
            }
        )
        rank += 1

    if len(fp) < 5:
        for code, _ in DIGEST_FOUR_SECTORS:
            for row in (pools.get(code) or {}).get("candidates") or []:
                if len(fp) >= 8:
                    break
                tier = str(row.get("priority_tier") or "B").strip().upper()[:1]
                if tier not in ("A", "B"):
                    continue
                title = str(row.get("headline") or row.get("title") or "").strip()
                key = _headline_dedupe_key(title)
                if not title or key in fp_keys:
                    continue
                fp_keys.add(key)
                fp.append(
                    {
                        "rank": rank,
                        "title": title,
                        "one_sentence": str(row.get("summary_hint") or "").strip(),
                        "why_it_matters": str(
                            row.get("reason_selected") or row.get("summary_hint") or ""
                        ).strip(),
                        "watch_next": str(
                            row.get("reason_selected") or row.get("summary_hint") or ""
                        ).strip()[:120],
                        "source_urls": _candidate_urls(row)[:2],
                    }
                )
                rank += 1
    out["front_page"] = fp

    existing_by_code: dict[str, dict[str, Any]] = {}
    for sec in out.get("sector_deep_briefs") or []:
        if isinstance(sec, dict):
            code = str(sec.get("code") or "").strip().lower()
            if code:
                existing_by_code[code] = dict(sec)

    norm_sectors: list[dict[str, Any]] = []
    for code, label in DIGEST_FOUR_SECTORS:
        bucket = existing_by_code.get(code) or {
            "code": code,
            "name": label,
            "sector_thesis": "",
            "subsector_briefs": [],
            "story_dossiers": [],
        }
        dossiers: list[dict[str, Any]] = [
            dict(d)
            for d in (bucket.get("story_dossiers") or [])
            if isinstance(d, dict)
        ]
        d_keys = {_headline_dedupe_key(d.get("title") or "") for d in dossiers}
        pool = pools.get(code) or {}
        pool_size = int(pool.get("candidates_in_partials") or 0)
        target = _newsroom_dossier_target(pool_size, len(dossiers))
        d_rank = max((int(d.get("rank") or 0) for d in dossiers), default=0) + 1
        for row in pool.get("candidates") or []:
            if len(dossiers) >= target:
                break
            tier = str(row.get("priority_tier") or "B").strip().upper()[:1]
            if tier not in ("A", "B"):
                continue
            title = str(row.get("headline") or row.get("title") or "").strip()
            key = _headline_dedupe_key(title)
            if not title or key in d_keys:
                continue
            d_keys.add(key)
            hint = str(row.get("summary_hint") or "").strip()
            reason = str(row.get("reason_selected") or hint).strip()
            rep = _candidate_to_rep_sources(row, headline=title, url_index=url_index)
            if not rep:
                continue
            watch_hint = str(row.get("reason_selected") or hint).strip()
            dossiers.append(
                {
                    "rank": d_rank,
                    "depth_level": "deep" if tier == "A" else "brief",
                    "title": title,
                    "summary": hint,
                    "main_developments": [hint] if hint else [],
                    "why_it_matters": reason,
                    "affected_groups": [],
                    "watch_next": [watch_hint[:120]] if watch_hint else [],
                    "representative_sources": rep,
                }
            )
            d_rank += 1
        norm_sectors.append(
            {
                "code": code,
                "name": str(bucket.get("name") or label),
                "sector_thesis": str(bucket.get("sector_thesis") or "").strip(),
                "subsector_briefs": bucket.get("subsector_briefs") or [],
                "story_dossiers": dossiers,
            }
        )
    out["sector_deep_briefs"] = norm_sectors

    watch = [
        dict(w)
        for w in (out.get("watchlist_24_72h") or [])
        if isinstance(w, dict) and str(w.get("theme") or "").strip()
    ]
    if len(watch) < 4:
        seen_themes: set[str] = {str(w.get("theme") or "").strip().lower() for w in watch}
        for item in fp[:6]:
            theme = str(item.get("title") or "").strip()
            if not theme or theme.lower() in seen_themes:
                continue
            seen_themes.add(theme.lower())
            watch.append(
                {
                    "theme": theme,
                    "what_to_watch": str(item.get("watch_next") or "").strip(),
                    "why": str(item.get("why_it_matters") or "").strip(),
                }
            )
            if len(watch) >= 6:
                break
    out["watchlist_24_72h"] = watch

    return out


def supplement_digest_sectors_from_partials(
    summary: dict[str, Any],
    partials: list[dict[str, Any]],
) -> dict[str, Any]:
    """Nếu merge co quá ít nhưng partials còn A/B — bổ sung từ candidate (không bịa)."""
    if not partials or not isinstance(summary.get("sectors"), list):
        return summary
    pools = {p["code"]: p for p in aggregate_partial_sector_candidates(partials)}
    for sec in summary["sectors"]:
        if not isinstance(sec, dict):
            continue
        code = str(sec.get("code") or "").strip().lower()
        pool = pools.get(code) or {}
        candidates = pool.get("candidates") if isinstance(pool.get("candidates"), list) else []
        pool_size = int(pool.get("candidates_in_partials") or len(candidates))
        subs = [r for r in (sec.get("sub_topics") or []) if isinstance(r, dict)]
        keys = {_headline_dedupe_key(r.get("headline") or r.get("title")) for r in subs}
        ab_extra: list[dict[str, Any]] = []
        for row in candidates:
            tier = str(row.get("priority_tier") or "B").strip().upper()[:1]
            if tier not in ("A", "B"):
                continue
            hl = str(row.get("headline") or row.get("title") or "").strip()
            key = _headline_dedupe_key(hl)
            if not key or key in keys:
                continue
            keys.add(key)
            ab_extra.append(row)
        if not ab_extra:
            continue
        n = len(subs)
        if pool_size < 12 or n >= 4:
            continue
        # Pool giàu + merge <4: bổ sung A/B cho đến ~6–10 luồng (không vượt parser cap)
        target = min(
            DIGEST_PARSER_MAX_SUB_TOPICS_PER_SECTOR,
            max(6, min(10, n + len(ab_extra))),
        )
        if pool_size >= 40:
            target = min(DIGEST_PARSER_MAX_SUB_TOPICS_PER_SECTOR, max(8, target))
        for row in ab_extra:
            if len(subs) >= target:
                break
            subs.append(row)
        subs.sort(key=lambda r: _sub_topic_sort_key(r, 0))
        sec["sub_topics"] = subs
    return summary


def finalize_digest_summary(
    summary: dict[str, Any] | None,
    *,
    partials: list[dict[str, Any]] | None = None,
    input_articles: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    if not isinstance(summary, dict):
        return summary
    url_index = DigestUrlIndex(input_articles or []) if input_articles else None
    corpus_titles_blob = " ".join(
        str(a.get("title") or "") for a in (input_articles or []) if isinstance(a, dict)
    ).lower()
    if _is_newsroom_brief(summary):
        if partials:
            summary = supplement_newsroom_from_partials(
                summary, partials, url_index=url_index
            )
        normalized = normalize_newsroom_brief(summary, url_index=url_index)
        for w in validate_newsroom_brief(normalized, corpus_titles_blob):
            print(f"WARN newsroom brief: {w}", file=sys.stderr)
        for w in validate_digest_url_whitelist(normalized, url_index):
            print(f"WARN digest URL whitelist: {w}", file=sys.stderr)
        return normalized
    if partials:
        summary = supplement_digest_sectors_from_partials(summary, partials)
    normalized = normalize_digest_summary(summary, url_index=url_index)
    for w in validate_digest_public_polish(normalized):
        print(f"WARN digest polish: {w}", file=sys.stderr)
    for w in validate_digest_url_whitelist(normalized, url_index):
        print(f"WARN digest URL whitelist: {w}", file=sys.stderr)
    for w in validate_digest_multisector_coverage(normalized):
        print(f"WARN digest coverage: {w}", file=sys.stderr)
    return normalized


class ArticleTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._capture_tag: str | None = None
        self._buffer: list[str] = []
        self.paragraphs: list[str] = []
        self.meta_description = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
            return

        attr_map = {key.lower(): value or "" for key, value in attrs}
        if tag == "meta":
            name = attr_map.get("name", "").lower()
            prop = attr_map.get("property", "").lower()
            if name == "description" or prop == "og:description":
                self.meta_description = clean_text(attr_map.get("content", ""))
            return

        if tag in {"p", "h1", "h2", "h3", "li"} and self._skip_depth == 0:
            self._capture_tag = tag
            self._buffer = []

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
            return

        if self._capture_tag == tag:
            text = clean_text(" ".join(self._buffer))
            if len(text) >= 40:
                self.paragraphs.append(text)
            self._capture_tag = None
            self._buffer = []

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0 and self._capture_tag:
            self._buffer.append(data)


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    text = unescape(value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        clean_key = key.strip()
        if not os.environ.get(clean_key):
            os.environ[clean_key] = value.strip().strip('"').strip("'")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_article_text(url: str, timeout: int, max_chars: int) -> tuple[str, str]:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"

    html = raw.decode(charset, errors="replace")
    extractor = ArticleTextExtractor()
    extractor.feed(html)

    paragraphs = []
    seen: set[str] = set()
    for paragraph in extractor.paragraphs:
        key = paragraph.lower()
        if key in seen:
            continue
        seen.add(key)
        paragraphs.append(paragraph)

    content = "\n".join(paragraphs)
    if not content and extractor.meta_description:
        content = extractor.meta_description

    text = clean_text(content)
    if max_chars > 0:
        text = text[:max_chars]
    return text, "html"


def text_from_article_record(article: dict[str, Any], max_chars: int | None) -> str:
    for key in ("text", "content_for_ai", "article_text", "summary"):
        raw = str(article.get(key) or "").strip()
        if raw:
            if max_chars is not None and max_chars > 0:
                return raw[:max_chars]
            return raw
    return ""


def stratified_sample_articles(
    articles: list[dict[str, Any]],
    max_articles: int,
) -> list[dict[str, Any]]:
    """Spread picks across sources so one outlet does not dominate the digest."""
    if max_articles <= 0 or len(articles) <= max_articles:
        return list(articles)

    by_source: dict[str, list[dict[str, Any]]] = {}
    for art in articles:
        src = str(art.get("source") or "unknown")
        by_source.setdefault(src, []).append(art)

    for group in by_source.values():
        group.sort(key=lambda a: str(a.get("published_at") or ""), reverse=True)

    sources = sorted(by_source.keys(), key=lambda s: len(by_source[s]), reverse=True)
    picked: list[dict[str, Any]] = []
    idx = 0
    while len(picked) < max_articles:
        progressed = False
        for src in sources:
            group = by_source[src]
            if idx < len(group):
                picked.append(group[idx])
                progressed = True
                if len(picked) >= max_articles:
                    break
        if not progressed:
            break
        idx += 1

    picked.sort(key=lambda a: str(a.get("published_at") or ""), reverse=True)
    return picked


def estimate_tokens_from_chars(char_count: int) -> int:
    return max(1, char_count // 4)


def model_input_token_limit(model: str) -> int:
    return MODEL_INPUT_TOKEN_LIMIT.get(model, 1_048_576)


def resolve_max_input_tokens_per_request(
    model: str,
    explicit: int,
    tpm_limit: int,
) -> int:
    """Max input tokens per API call (model context + optional --tpm-limit ceiling)."""
    context_cap = (
        model_input_token_limit(model)
        - OUTPUT_TOKEN_RESERVE
        - PROMPT_TEMPLATE_TOKEN_SLACK
    )
    per_request = DEFAULT_MAX_INPUT_TOKENS_PER_REQUEST
    if explicit > 0:
        per_request = explicit
    if tpm_limit > 0:
        per_request = min(per_request, int(tpm_limit))
    return min(context_cap, per_request)


def article_digest_payload_tokens(article: dict[str, Any]) -> int:
    payload = json.dumps(compact_for_gemini([article], mode="digest"), ensure_ascii=False)
    return estimate_tokens_from_chars(len(payload))


def estimate_digest_chunk_prompt_tokens(
    chunk: list[dict[str, Any]],
    *,
    batch_index: int,
    batch_total: int,
    total_articles: int,
    window_meta: dict[str, Any],
    global_outline: dict[str, Any] | None,
) -> int:
    prompt = build_digest_chunk_prompt(
        chunk,
        batch_index=batch_index,
        batch_total=batch_total,
        total_articles=total_articles,
        window_meta=window_meta,
        global_outline=global_outline,
    )
    return estimate_tokens_from_chars(len(prompt))


def chunk_digest_prompt_overhead_tokens(
    *,
    batch_total: int,
    total_articles: int,
    window_meta: dict[str, Any],
    global_outline: dict[str, Any] | None,
) -> int:
    """Template + outline block size (no article bodies)."""
    return estimate_digest_chunk_prompt_tokens(
        [],
        batch_index=1,
        batch_total=max(1, batch_total),
        total_articles=total_articles,
        window_meta=window_meta,
        global_outline=global_outline,
    )


def chunk_enriched_articles_by_tokens(
    enriched: list[dict[str, Any]],
    max_input_tokens: int,
    *,
    total_articles: int,
    window_meta: dict[str, Any],
    global_outline: dict[str, Any] | None,
) -> list[list[dict[str, Any]]]:
    """Pack articles so each chunk prompt stays under max_input_tokens."""
    if not enriched:
        return []
    overhead = chunk_digest_prompt_overhead_tokens(
        batch_total=999,
        total_articles=total_articles,
        window_meta=window_meta,
        global_outline=global_outline,
    )
    max_body_tokens = max(10_000, max_input_tokens - overhead)
    chunks: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_body = 0

    for article in enriched:
        one = article_digest_payload_tokens(article)
        if current and current_body + one > max_body_tokens:
            chunks.append(current)
            current = []
            current_body = 0
        current.append(article)
        current_body += one

    if current:
        chunks.append(current)
    return chunks


def load_existing_outline(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    outline = data.get("outline")
    return outline if isinstance(outline, dict) else None


def load_existing_partials(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    partials = data.get("partials")
    return partials if isinstance(partials, list) else []


def wait_between_gemini_requests(seconds: float, min_interval: float) -> None:
    delay = max(float(seconds), float(min_interval))
    if delay > 0:
        time.sleep(delay)


def fit_enriched_to_prompt_budget(
    articles: list[dict[str, Any]],
    *,
    mode: str,
    total_in_window: int,
    window_meta: dict[str, Any],
    max_articles: int,
    max_article_chars: int,
    fetch_timeout: int,
    refetch_urls: bool,
    max_prompt_chars: int,
) -> tuple[list[dict[str, Any]], str, int]:
    """Shrink article count until digest/macro prompt fits token budget."""
    article_cap = max_articles
    min_cap = 40 if mode == "digest" else 20
    prompt = ""
    enriched: list[dict[str, Any]] = []

    while True:
        enriched = enrich_articles(
            articles,
            article_cap,
            max_article_chars,
            fetch_timeout,
            refetch_urls=refetch_urls,
        )
        if mode == "digest":
            prompt = build_digest_prompt(
                enriched, total_in_window=total_in_window, window_meta=window_meta
            )
        else:
            prompt = build_macro_prompt(enriched)

        if len(prompt) <= max_prompt_chars or article_cap <= min_cap:
            return enriched, prompt, article_cap

        next_cap = max(min_cap, int(article_cap * 0.75))
        if next_cap >= article_cap:
            next_cap = article_cap - 5
        print(
            f"Prompt {len(prompt)} chars (~{estimate_tokens_from_chars(len(prompt))} tok) "
            f"exceeds budget {max_prompt_chars}; reducing articles {article_cap} -> {next_cap}",
            file=sys.stderr,
        )
        article_cap = next_cap


def enrich_articles(
    articles: list[dict[str, Any]],
    max_articles: int,
    max_article_chars: int,
    timeout: int,
    *,
    refetch_urls: bool,
    quiet: bool = False,
) -> list[dict[str, Any]]:
    if max_articles is None or max_articles <= 0:
        pool = list(articles)
    else:
        pool = stratified_sample_articles(articles, max_articles)
    enriched = []
    total = len(pool)
    log_every = max(50, total // 20) if total > 100 else 1

    for index, article in enumerate(pool, start=1):
        url = str(article.get("url", ""))
        local_text = text_from_article_record(article, max_article_chars)
        fetch_status = "json_text"
        content_for_ai = local_text

        if refetch_urls and url and len(local_text) < 400:
            try:
                fetched, fetch_status = fetch_article_text(url, timeout, max_article_chars)
                if fetched:
                    content_for_ai = fetched
            except (HTTPError, URLError, TimeoutError, UnicodeError, ValueError) as error:
                fetch_status = f"fetch_error: {error}"
                content_for_ai = local_text or ""

        if not content_for_ai:
            fetch_status = "empty_content"

        enriched_article = {
            **article,
            "content_for_ai": content_for_ai,
            "content_chars": len(content_for_ai),
            "fetch_status": fetch_status,
        }
        enriched.append(enriched_article)
        if not quiet or index == 1 or index == total or index % log_every == 0:
            title = str(article.get("title") or "")[:80]
            try:
                print(f"{index}/{total} {fetch_status}: {title}")
            except UnicodeEncodeError:
                print(f"{index}/{total} {fetch_status}: {title.encode('ascii', 'replace').decode()}")

    return enriched


def compact_for_gemini(articles: list[dict[str, Any]], *, mode: str) -> list[dict[str, Any]]:
    compacted = []
    for article in articles:
        if mode == "digest":
            compacted.append(
                {
                    "title": article.get("title", ""),
                    "source": article.get("source", ""),
                    "published_at": article.get("published_at", ""),
                    "category": article.get("category", ""),
                    "region": article.get("region", ""),
                    "url": article.get("url", ""),
                    "text": article.get("content_for_ai", ""),
                }
            )
        else:
            compacted.append(
                {
                    "title": article.get("title", ""),
                    "source": article.get("source", ""),
                    "category": article.get("category", ""),
                    "region": article.get("region", ""),
                    "published_at": article.get("published_at", ""),
                    "url": article.get("url", ""),
                    "macro_score": article.get("macro_score"),
                    "rss_summary": article.get("summary", ""),
                    "article_text": article.get("content_for_ai", ""),
                }
            )
    return compacted


def build_digest_prompt(
    enriched_articles: list[dict[str, Any]],
    *,
    total_in_window: int,
    window_meta: dict[str, Any],
) -> str:
    article_json = json.dumps(compact_for_gemini(enriched_articles, mode="digest"), ensure_ascii=False)
    window_desc = json.dumps(window_meta, ensure_ascii=False)
    sent = len(enriched_articles)
    return f"""
Bạn là biên tập viên tổng hợp tin cho LEON Quant Labs.

## Nguồn dữ liệu (bắt buộc)
- CHỈ được dùng JSON bài viết đính kèm bên dưới (các trường title, source, published_at, url, text).
- TUYỆT ĐỐI KHÔNG: mở URL, crawl web, tìm kiếm internet, hoặc bổ sung sự kiện/số liệu không có trong text.
- Không có trong dữ liệu → ghi rõ "chưa có trong dữ liệu"; không suy diễn, không bịa.

## Bối cảnh tập tin
- Cửa sổ thời gian: {window_desc}
- Số bài trong payload (toàn bộ tin đã crawl, đọc hết): {sent}
- Khái quát bức tranh tin **48 giờ / 2 ngày gần nhất** từ **toàn bộ** các bài dưới đây.

## Mục tiêu (adaptive editorial — một pass)
{_digest_four_sector_rules_block(for_merge=True)}

Trả về DUY NHẤT JSON:
{{
  "title": "Tổng hợp tin tức toàn cầu và Việt Nam 48 giờ",
  "reading_time_minutes": "auto",
  "executive_overview": ["bullet adaptive, không lặp ý"],
  "sectors": [
{_digest_sector_json_schema_fragment()}
  ],
  "vietnam_highlights": "Đủ ý cụ thể — adaptive theo dữ liệu VN",
  "international_highlights": "Đủ ý cụ thể — adaptive theo dữ liệu quốc tế",
  "notable_articles": [{{
    "title": "...",
    "source": "...",
    "url": "...",
    "why_notable": "...",
    "priority_tier": "A"
  }}],
  "gaps_and_limits": "Ngắn nếu có"
}}

Dữ liệu bài viết:
{article_json}
""".strip()


def compact_catalog_for_outline(articles: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Lightweight index of ALL articles (fits one 1M-context call for ~2500 items)."""
    catalog: list[dict[str, str]] = []
    for article in articles:
        catalog.append(
            {
                "title": str(article.get("title") or "")[:500],
                "url": str(article.get("url") or ""),
            }
        )
    return catalog


def build_digest_outline_prompt(
    catalog: list[dict[str, str]],
    *,
    total_articles: int,
    window_meta: dict[str, Any],
) -> str:
    catalog_json = json.dumps(catalog, ensure_ascii=False)
    window_desc = json.dumps(window_meta, ensure_ascii=False)
    return f"""
Bạn là tổng biên tập tin. Nhiệm vụ: đọc **TOÀN BỘ** danh mục {total_articles} bài (chỉ title, url) và vẽ **bản đồ chủ đề** 48 giờ — **không** biến title đơn thành sự kiện chắc chắn.

## Quy tắc
- CHỈ dùng danh mục bên dưới. KHÔNG mở URL, KHÔNG tìm web.
- `dominant_themes` dựa trên **độ lặp nguồn** hoặc **tác động rõ**, không chỉ headline giật.
- Một nguồn yếu/clone không được quyết định toàn bộ panorama nếu thiếu nguồn khác.
- Claim lớn (IPO, ngừng bắn, xếp hạng tín nhiệm, ETF tỷ USD…): ghi `confidence_hint` / `source_quality_hint` / `risk_of_overstatement`.
- JSON gọn: tối đa {DIGEST_MAX_OUTLINE_THEMES} theme; tối đa 3 `timeline_sketch`; không liệt kê từng bài.
{_digest_four_sector_rules_block()}

Cửa sổ: {window_desc}

Trả về DUY NHẤT JSON:
{{
  "total_articles": {total_articles},
  "panorama_summary": "2-3 đoạn khung (thận trọng, không phóng đại)",
  "dominant_themes": [
    {{
      "theme": "Tên chủ đề",
      "why_dominant": "Lặp nguồn / tác động",
      "approx_article_count": "ước lượng",
      "source_quality_hint": "high|medium|low",
      "confidence_hint": "high|medium|low",
      "risk_of_overstatement": "nếu title giật nhưng nguồn mỏng",
      "regions": ["vietnam", "international"],
      "sectors": ["finance", "tech", "news", "trends"]
    }}
  ],
  "vietnam_vs_global": "So sánh trọng tâm VN và thế giới",
  "timeline_sketch": [
    {{"date": "YYYY-MM-DD", "top_headlines": ["tiêu đề/sự kiện — không khẳng định nếu chưa chắc"]}}
  ],
  "sources_most_active": ["domain1", "domain2"],
  "gaps": "Mảng tin thiếu hoặc cần xác minh (nếu có)"
}}

Danh mục đầy đủ ({total_articles} bài):
{catalog_json}
""".strip()


def chunk_enriched_articles(
    enriched: list[dict[str, Any]],
    max_chunk_chars: int,
) -> list[list[dict[str, Any]]]:
    """Split articles so each chunk's JSON payload stays under max_chunk_chars."""
    chunks: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_chars = 0
    for article in enriched:
        one = len(json.dumps(compact_for_gemini([article], mode="digest"), ensure_ascii=False))
        if current and current_chars + one > max_chunk_chars:
            chunks.append(current)
            current = []
            current_chars = 0
        current.append(article)
        current_chars += one
    if current:
        chunks.append(current)
    return chunks


def build_digest_chunk_prompt(
    chunk: list[dict[str, Any]],
    *,
    batch_index: int,
    batch_total: int,
    total_articles: int,
    window_meta: dict[str, Any],
    global_outline: dict[str, Any] | None,
) -> str:
    article_json = json.dumps(compact_for_gemini(chunk, mode="digest"), ensure_ascii=False)
    window_desc = json.dumps(window_meta, ensure_ascii=False)
    outline_block = ""
    if global_outline:
        outline_block = (
            "\n## Khung toàn cảnh (đã quét HẾT "
            f"{total_articles} tiêu đề — dùng để không lệch chủ đề)\n"
            + json.dumps(global_outline, ensure_ascii=False)
            + "\n"
        )
    return f"""
Bạn là **chuyên gia phân tích tin** (kinh tế–thị trường–chính sách) cho LEON Quant Labs. Đây là **phần {batch_index}/{batch_total}** của bản tin 48 giờ.

## Quy tắc
- CHỈ dùng JSON bài viết + khung (nếu có). KHÔNG mở URL, KHÔNG bịa.
- Ghi nhận **candidate** đạt tiêu chuẩn; số lượng **tự nhiên** theo phần — không fill, không quota.
- `sector_notes` đủ 4 mã; mỗi mục: `priority_tier`, headline, `summary_hint`, 1 URL, `reason_selected`.
- `notable_articles`: chỉ tin tier A thật nổi bật trong phần (không cố đủ số).
{_digest_four_sector_rules_block()}
- Chunk `summary`: nháp **luồng + mối liên hệ** trong phần (merge viết briefing/dossier chính).
- `summary_hint` / `reason_selected`: cụ thể actor+sự kiện — material cho merge viết prose, không câu rule.
- `key_excerpt`: 2–4 câu trích yếu CỤ THỂ từ chính text bài báo vừa đọc trong chunk này — phải có dữ kiện thực (số liệu, tên riêng, trích dẫn ngắn, mốc thời gian), KHÔNG được là câu chung như `summary_hint`; đây là nguyên liệu DUY NHẤT merge có để viết sâu, vì merge sẽ KHÔNG đọc lại text gốc. Chỉ điền cho sub_topic đã được giữ (đạt tier A/B/C) — không ép điền cho mọi bài.
{_digest_gemini_writing_rules_block()}
{outline_block}
## Cửa sổ: {window_desc}

Trả về DUY NHẤT JSON:
{{
  "batch_index": {batch_index},
  "batch_total": {batch_total},
  "articles_in_batch": {len(chunk)},
  "sector_notes": [
    {{
      "code": "finance|tech|news|trends",
      "name": "Tên tiếng Việt",
      "summary": "Nháp luồng + mối liên hệ trong phần — đủ ý, adaptive",
      "sub_topics": [{{
        "importance_rank": 1,
        "priority_tier": "A|B|C",
        "headline": "...",
        "summary_hint": "...",
        "key_excerpt": "2-4 câu trích yếu cụ thể từ text bài báo - số liệu/tên/trích dẫn, KHÔNG phải câu chung",
        "source_urls": ["url1", "url2"],
        "reason_selected": "..."
      }}]
    }}
  ],
  "vietnam_notes": "Tin VN trong phần này",
  "international_notes": "Tin quốc tế trong phần này",
  "notable_articles": [
    {{"title": "...", "source": "...", "url": "...", "why_notable": "..."}}
  ]
}}

Dữ liệu phần {batch_index}:
{article_json}
""".strip()


def aggregate_partial_sector_candidates(
    partials: list[dict[str, Any]],
    *,
    max_candidates_per_sector: int = 48,
) -> list[dict[str, Any]]:
    """Gom candidate từ mọi partial — merge nhận pool rõ ràng thay vì JSON partial khổng lồ.

    Mỗi candidate giữ nguyên tất cả field từ chunk (bao gồm `key_excerpt` nếu có) —
    merge dùng field này để viết sâu hơn mà không cần đọc lại text gốc.
    """
    buckets: dict[str, list[dict[str, Any]]] = {code: [] for code, _ in DIGEST_FOUR_SECTORS}
    seen_keys: dict[str, set[str]] = {code: set() for code in buckets}

    for batch in partials:
        if not isinstance(batch, dict):
            continue
        raw = batch.get("summary")
        if not isinstance(raw, dict):
            continue
        for sn in raw.get("sector_notes") or []:
            if not isinstance(sn, dict):
                continue
            code = str(sn.get("code") or "").strip().lower()
            if code not in buckets:
                continue
            for row in sn.get("sub_topics") or []:
                if not isinstance(row, dict):
                    continue
                headline = str(row.get("headline") or row.get("title") or "").strip()
                if not headline:
                    continue
                key = headline.lower()[:120]
                if key in seen_keys[code]:
                    continue
                seen_keys[code].add(key)
                # row la sub_topic nguyen ven tu chunk, bao gom ca field moi nhu
                # key_excerpt neu co - KHONG loc field o day.
                buckets[code].append(row)

    out: list[dict[str, Any]] = []
    for code, label in DIGEST_FOUR_SECTORS:
        rows = buckets[code]
        rows.sort(key=lambda r: _sub_topic_sort_key(r, 0))
        out.append(
            {
                "code": code,
                "name": label,
                "candidates_in_partials": len(rows),
                "candidates": rows[:max_candidates_per_sector],
            }
        )
    return out


def _digest_partial_candidate_stats(partials: list[dict[str, Any]]) -> str:
    """Đếm candidate sub_topics trong partials — nhắc merge không co quá mức."""
    counts: dict[str, int] = {code: 0 for code, _ in DIGEST_FOUR_SECTORS}
    for batch in partials:
        raw = batch.get("summary") if isinstance(batch, dict) else None
        if not isinstance(raw, dict):
            continue
        for sn in raw.get("sector_notes") or []:
            if not isinstance(sn, dict):
                continue
            code = str(sn.get("code") or "").strip().lower()
            if code in counts:
                subs = sn.get("sub_topics") if isinstance(sn.get("sub_topics"), list) else []
                counts[code] += len(subs)
    lines = [
        f'- `{code}`: ~{counts[code]} candidate trong {len(partials)} partial'
        for code, _ in DIGEST_FOUR_SECTORS
    ]
    return (
        "## Thống kê candidate (partials — KHÔNG phải số final bắt buộc)\n"
        + "\n".join(lines)
        + "\n- Với input lớn, final thường **6–12+** `sub_topics`/sector nếu có đủ luồng A/B khác nhau; **không** chỉ 2–3 khi partials giàu."
    )


def build_digest_merge_prompt(
    partials: list[dict[str, Any]],
    *,
    total_articles: int,
    window_meta: dict[str, Any],
    global_outline: dict[str, Any] | None,
) -> str:
    sector_pools = aggregate_partial_sector_candidates(partials)
    merge_payload = {
        "partial_batch_count": len(partials),
        "sector_candidate_pools": sector_pools,
    }
    partial_json = json.dumps(merge_payload, ensure_ascii=False)
    window_desc = json.dumps(window_meta, ensure_ascii=False)
    outline_block = ""
    if global_outline:
        outline_block = (
            "\n## Khung toàn cảnh (từ TOÀN BỘ "
            f"{total_articles} tiêu đề — ưu tiên giữ đúng bức tranh tổng)\n"
            + json.dumps(global_outline, ensure_ascii=False)
            + "\n"
        )
    partial_stats = _digest_partial_candidate_stats(partials)
    return f"""
{_digest_newsroom_voice_block()}

Đã có {len(partials)} partial từ {total_articles} bài. Cửa sổ: {window_desc}.
{outline_block}
{partial_stats}

**Không có quota cố định** số story/dossier. Nếu 48h có 5 story lớn → 5 dossier sâu; nếu có 20 → giữ ~20 (gom cụm, không một bài một dòng vụn).
**Không fill** tin yếu. **Không cắt** story quan trọng chỉ vì muốn gọn.
Đối chiếu **toàn bộ** `sector_notes` / `candidates[]` từ mọi partial trước khi kết thúc.

{_digest_front_page_criteria_block()}

## Minimum chất lượng (BẮT BUỘC khi candidate pools giàu)
- `front_page` BẮT BUỘC có ít nhất các tin đạt tiêu chí highlight (xem '## Tiêu chí tin nổi bật'); KHÔNG để trống dù executive_briefing/sector_thesis đã viết đủ — đây là 2 mục đích khác nhau, không thay thế nhau.
- Mọi `front_page` / `story_dossiers` nếu được sinh ra thì phải có URL từ pools (`source_urls` / `representative_sources`); không tạo filler để ép số lượng.
- Khi pools tổng **≥ 80** candidates: `executive_briefing` phải là **prose có mạch** (sections + content) — không outline một câu/mục; độ dài adaptive theo mức quan trọng.
- Headline tiếng Việt, viết hoa chữ đầu, không copy thô từ RSS.
- Khi candidate có `key_excerpt`: đây là dữ kiện chi tiết nhất từ text gốc bạn có được — PHẢI khai thác để viết executive_briefing/sector_thesis/dossier sâu hơn, không chỉ dựa vào headline/summary_hint.

{_digest_four_sector_rules_block(for_merge=True)}
{_digest_story_dossier_rules_block()}
{_digest_source_urls_block()}
- `editor_note`: **để trống** hoặc rất ngắn — UI không hiển thị Lời biên tập riêng; nội lực đổ vào `executive_briefing`.
- `executive_briefing`: **bài briefing thật** (xem quy tắc trên) — không outline; sections mỗi mục nhiều đoạn khi pools dày.
- **Không** viết thêm section văn xuôi "điểm nóng" trong executive_briefing (giữ điểm nóng tích hợp trong prose như đã hướng dẫn) — nhưng `front_page` (dạng list có rank) vẫn BẮT BUỘC điền khi có tin đạt tiêu chí, đây là 2 cơ chế hiển thị khác nhau.
- `sector_deep_briefs`: đúng **4** sector; `sector_thesis` = bài tóm tắt ngành có mạch (không nối dossier rời).
- Mọi `representative_sources` quan trọng: thêm `excerpt` trích yếu biên tập — độ dài adaptive, đủ ý.
- Trong `story_dossiers`, cố gắng gắn `sub_sector` khi có căn cứ dữ liệu (không ép cho đủ).
- `watchlist_24_72h`: **4–8** chủ đề theo dõi 24–72h.
- `source_desk`: **3–8** nhóm nguồn đại diện theo chủ đề lớn.

{_digest_newsroom_prose_example_block()}

CHỈ dùng dữ liệu được cung cấp. **Cấm** tự tạo URL.

Trả về DUY NHẤT JSON (schema newsroom):
{_digest_newsroom_json_schema_fragment()}

## Candidate pools (đã gom từ mọi partial)
Gom candidates thành `story_dossiers` + `front_page` (front_page hiển thị public khi có tin đạt tiêu chí highlight) + `executive_briefing`/`sector_thesis` (bài viết liền mạch).

{partial_json}
""".strip()


_DIGEST_SHALLOW_WARNING_MARKERS = (
    "quá ngắn",
    "quá nông",
    "chưa phản ánh cụm dossier chính",
    "có dấu hiệu generic",
    "thiếu representative_sources",
    "khả năng cao có tin đạt tiêu chí",
    "KHÔNG sector nào có story_dossiers",
    "có thể hallucinate",
)


def _is_shallow_digest_warning(warning: str) -> bool:
    return any(marker in warning for marker in _DIGEST_SHALLOW_WARNING_MARKERS)


def _digest_shallow_retry_feedback_block(
    warnings: list[str], previous_draft: dict[str, Any]
) -> str:
    warn_lines = "\n".join(f"- {w}" for w in warnings)
    draft_excerpt = json.dumps(
        {
            "executive_briefing": previous_draft.get("executive_briefing"),
            "sector_deep_briefs": [
                {"name": s.get("name"), "sector_thesis": s.get("sector_thesis")}
                for s in (previous_draft.get("sector_deep_briefs") or [])
                if isinstance(s, dict)
            ],
        },
        ensure_ascii=False,
    )
    return f"""
## PHẢN HỒI CHẤT LƯỢNG — VIẾT LẠI PHẦN BỊ LỖI (BẮT BUỘC)
Bản nháp trước đã bị từ chối vì các lý do cụ thể sau:
{warn_lines}

Bản nháp trước (chỉ phần liên quan, để bạn biết tránh lặp lại lỗi tương tự — không copy nguyên văn):
{draft_excerpt}

Viết lại TOÀN BỘ JSON theo đúng schema và quy tắc đã nêu ở trên, sửa cụ thể từng lỗi liệt kê —
đặc biệt: `executive_briefing.content` và `sector_thesis` phải phủ đủ các cụm tin tier A/B đã có
trong candidate pools, không nén ngắn hơn bản trước, không generic, không thiếu actor/sự kiện cụ thể.
""".strip()


def _run_merge_with_quality_retry(
    partials: list[dict[str, Any]],
    *,
    total_articles: int,
    window_meta: dict[str, Any],
    global_outline: dict[str, Any] | None,
    model: str,
    api_key: str,
    gemini_timeout: int,
    min_request_interval: float,
) -> dict[str, Any] | None:
    """Gọi merge Gemini; nếu validate phát hiện output nông/ngắn dù pools giàu, retry 1 lần với phản hồi cụ thể."""
    sorted_summaries = [
        p["summary"] for p in sorted(partials, key=lambda p: int(p.get("batch_index") or 0))
    ]
    merge_prompt = build_digest_merge_prompt(
        sorted_summaries,
        total_articles=total_articles,
        window_meta=window_meta,
        global_outline=global_outline,
    )
    print(f"Merge prompt ~{estimate_tokens_from_chars(len(merge_prompt))} tokens")
    final = call_gemini(
        merge_prompt,
        model,
        api_key,
        timeout=gemini_timeout,
        min_retry_interval=min_request_interval,
        max_output_tokens=DIGEST_MERGE_MAX_OUTPUT_TOKENS,
    )
    if not isinstance(final, dict):
        return final
    try:
        if not _is_newsroom_brief(final):
            return final
        # Best-effort: dung title cua candidate da gom tu partials lam corpus blob
        # xap xi (khong co full corpus o day) - du de bat hallucination ro rang,
        # finalize_digest_summary() se check lai voi corpus day du sau cung.
        retry_corpus_blob = " ".join(
            str(row.get("headline") or row.get("title") or "")
            for pool in aggregate_partial_sector_candidates(partials)
            for row in pool.get("candidates", [])
        ).lower()
        shallow_warnings = [
            w
            for w in validate_newsroom_brief(final, retry_corpus_blob)
            if _is_shallow_digest_warning(w)
        ]
    except Exception as exc:
        print(f"WARN newsroom brief: bỏ qua bước kiểm tra nông/ngắn do lỗi: {exc}", file=sys.stderr)
        return final
    if not shallow_warnings:
        return final
    print(
        f"WARN newsroom brief: output nông/ngắn ({len(shallow_warnings)} cảnh báo) — "
        "retry merge 1 lần với phản hồi cụ thể.",
        file=sys.stderr,
    )
    try:
        retry_prompt = merge_prompt + "\n\n" + _digest_shallow_retry_feedback_block(
            shallow_warnings, final
        )
        wait_between_gemini_requests(0, min_request_interval)
        retried = call_gemini(
            retry_prompt,
            model,
            api_key,
            timeout=gemini_timeout,
            min_retry_interval=min_request_interval,
            max_output_tokens=DIGEST_MERGE_MAX_OUTPUT_TOKENS,
        )
    except Exception as exc:
        print(f"WARN newsroom brief: retry merge lỗi, giữ bản đầu: {exc}", file=sys.stderr)
        return final
    if isinstance(retried, dict):
        return retried
    return final


def run_batch_digest(
    enriched_articles: list[dict[str, Any]],
    *,
    model: str,
    api_key: str,
    window_meta: dict[str, Any],
    total_articles: int,
    max_input_tokens_per_request: int,
    batch_chunk_chars: int,
    gemini_timeout: int,
    api_pause_seconds: float,
    min_request_interval: float,
    partials_path: Path,
    outline_path: Path,
    outline_first: bool,
    use_existing_outline: bool,
    resume_partials: bool,
    merge_only: bool,
    max_api_calls: int,
    dry_run: bool,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], int]:
    global_outline: dict[str, Any] | None = None
    api_calls = 0

    if merge_only:
        global_outline = load_existing_outline(outline_path)
        if global_outline:
            print(f"Loaded outline for merge-only -> {outline_path}")
        else:
            print(f"WARN: no outline at {outline_path}; merge without panorama skeleton.", file=sys.stderr)
        partials = load_existing_partials(partials_path)
        if not partials:
            print(f"ERROR: --merge-only needs partials in {partials_path}", file=sys.stderr)
            return None, [], 0
        batch_total = int(partials[0].get("batch_total") or 0) or len(partials)
        if len(partials) < batch_total:
            print(
                f"ERROR: only {len(partials)}/{batch_total} partials; finish chunks first.",
                file=sys.stderr,
            )
            return None, partials, 0
        print(f"Merge-only: {len(partials)} partials, re-running merge with multisector prompts.")
        if dry_run:
            mp = build_digest_merge_prompt(
                [p["summary"] for p in sorted(partials, key=lambda p: int(p.get("batch_index") or 0))],
                total_articles=total_articles,
                window_meta=window_meta,
                global_outline=global_outline,
            )
            print(f"Dry-run merge prompt ~{estimate_tokens_from_chars(len(mp))} tokens")
            return None, partials, 1
        wait_between_gemini_requests(api_pause_seconds, min_request_interval)
        final = _run_merge_with_quality_retry(
            partials,
            total_articles=total_articles,
            window_meta=window_meta,
            global_outline=global_outline,
            model=model,
            api_key=api_key,
            gemini_timeout=gemini_timeout,
            min_request_interval=min_request_interval,
        )
        if isinstance(final, dict):
            final = finalize_digest_summary(
                final, partials=partials, input_articles=enriched_articles
            )
        return final, partials, 1

    if use_existing_outline:
        global_outline = load_existing_outline(outline_path)
        if global_outline:
            print(f"Loaded existing outline -> {outline_path}")
            outline_first = False

    if outline_first:
        catalog = compact_catalog_for_outline(enriched_articles)
        outline_prompt = build_digest_outline_prompt(
            catalog, total_articles=total_articles, window_meta=window_meta
        )
        est_outline = estimate_tokens_from_chars(len(outline_prompt))
        print(f"Outline pass: {total_articles} headlines, prompt ~{est_outline} tokens")
        if not dry_run:
            global_outline = call_gemini(
                outline_prompt,
                model,
                api_key,
                timeout=gemini_timeout,
                min_retry_interval=min_request_interval,
            )
            api_calls += 1
            outline_path.write_text(
                json.dumps(
                    {
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "total_articles": total_articles,
                        "outline": global_outline,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            print(f"Wrote outline -> {outline_path}")
            wait_between_gemini_requests(api_pause_seconds, min_request_interval)

    if batch_chunk_chars > 0:
        chunks = chunk_enriched_articles(enriched_articles, batch_chunk_chars)
        print(f"Batch digest: {len(chunks)} chunk(s), legacy char cap ~{batch_chunk_chars}")
    else:
        chunks = chunk_enriched_articles_by_tokens(
            enriched_articles,
            max_input_tokens_per_request,
            total_articles=total_articles,
            window_meta=window_meta,
            global_outline=global_outline,
        )
        overhead = chunk_digest_prompt_overhead_tokens(
            batch_total=max(1, len(chunks)),
            total_articles=total_articles,
            window_meta=window_meta,
            global_outline=global_outline,
        )
        print(
            f"Batch digest: {len(chunks)} chunk(s), "
            f"max ~{max_input_tokens_per_request} input tokens/request "
            f"(prompt overhead ~{overhead}, model={model})"
        )

    partials: list[dict[str, Any]] = []
    done_indices: set[int] = set()
    if resume_partials:
        partials = load_existing_partials(partials_path)
        for p in partials:
            idx = int(p.get("batch_index") or 0)
            if idx:
                done_indices.add(idx)
        if partials:
            print(f"Resumed {len(partials)} partial(s) from {partials_path}")

    for idx, chunk in enumerate(chunks, start=1):
        if idx in done_indices:
            print(f"  Chunk {idx}/{len(chunks)}: skip (already in partials)")
            continue

        chunk_prompt = build_digest_chunk_prompt(
            chunk,
            batch_index=idx,
            batch_total=len(chunks),
            total_articles=total_articles,
            window_meta=window_meta,
            global_outline=global_outline,
        )
        est = estimate_tokens_from_chars(len(chunk_prompt))
        print(f"  Chunk {idx}/{len(chunks)}: {len(chunk)} articles, prompt ~{est} tokens")

        if dry_run:
            continue

        wait_between_gemini_requests(api_pause_seconds, min_request_interval)

        partial = call_gemini(
            chunk_prompt,
            model,
            api_key,
            timeout=gemini_timeout,
            min_retry_interval=min_request_interval,
            max_output_tokens=16_384,
        )
        api_calls += 1
        entry = {
            "batch_index": idx,
            "batch_total": len(chunks),
            "articles_in_batch": len(chunk),
            "summary": partial,
        }
        partials = [p for p in partials if int(p.get("batch_index") or 0) != idx]
        partials.append(entry)
        partials.sort(key=lambda p: int(p.get("batch_index") or 0))
        partials_path.write_text(
            json.dumps(
                {"generated_at": datetime.now(timezone.utc).isoformat(), "partials": partials},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"  Saved partial {idx}/{len(chunks)} -> {partials_path}")
        if max_api_calls > 0 and api_calls >= max_api_calls:
            print(f"Stopping after {api_calls} API call(s) (--max-api-calls).")
            return None, partials, api_calls

    if dry_run:
        extra = 0 if (use_existing_outline and global_outline) else (1 if outline_first else 0)
        pending = len(chunks) - len(done_indices)
        return None, partials, extra + pending + 1

    if len(partials) < len(chunks):
        print(
            f"ERROR: only {len(partials)}/{len(chunks)} partials ready; cannot merge yet.",
            file=sys.stderr,
        )
        return None, partials, api_calls

    print(f"Wrote partials -> {partials_path}")

    wait_between_gemini_requests(api_pause_seconds, min_request_interval)
    final = _run_merge_with_quality_retry(
        partials,
        total_articles=total_articles,
        window_meta=window_meta,
        global_outline=global_outline,
        model=model,
        api_key=api_key,
        gemini_timeout=gemini_timeout,
        min_request_interval=min_request_interval,
    )
    api_calls += 1
    if isinstance(final, dict):
        final = finalize_digest_summary(
            final, partials=partials, input_articles=enriched_articles
        )
    return final, partials, api_calls


def build_macro_prompt(enriched_articles: list[dict[str, Any]]) -> str:
    article_json = json.dumps(compact_for_gemini(enriched_articles, mode="macro"), ensure_ascii=False)
    return f"""
Bạn là analyst vĩ mô và thị trường cấp cao cho LEON Quant Labs. Phong cách ghi chú đầu tư: súc tích, ưu tiên kênh truyền và hàm ý thị trường, không khẩu hiệu.

Nhiệm vụ:
- Đọc dữ liệu bài viết đã crawl bên dưới. Mỗi bài có title, nguồn, URL, RSS summary và article_text nếu lấy được.
- Tổng hợp bằng tiếng Việt theo logic: (1) sự kiện/tin vĩ mô toàn cầu nổi bật, (2) kênh ảnh hưởng tới thị trường quốc tế, (3) hàm ý tới Việt Nam (TTCK, hệ thống tài chính–ngân hàng, tỷ giá/lạm phát, hàng hóa liên quan VN, dòng vốn).
- executive_summary: one-liner hoặc 2 câu cực ngắn tóm "trọng tâm hôm nay".
- Chỉ dùng dữ liệu được cung cấp. Không bịa số liệu, không suy diễn quá mức.
- Nếu dữ liệu mâu thuẫn hoặc thiếu ngữ cảnh, ghi rõ "chưa đủ dữ liệu".
- Ưu tiên: vĩ mô, lãi suất, tín dụng, ngân hàng, chứng khoán, hàng hóa/vàng/dầu, dòng vốn, chính sách, rủi ro địa chính trị.
- Loại bỏ tin nhiễu không liên quan đến kinh tế vĩ mô.

Trả về DUY NHẤT JSON hợp lệ theo schema:
{{
  "title": "Macro Daily Brief",
  "executive_summary": "1-3 câu trọng tâm tuyệt đối ngắn",
  "market_impact": "Risk-on | Risk-off | Neutral | Mixed",
  "key_themes": [
    {{
      "theme": "Tên chủ đề",
      "summary": "Tóm tắt 2-4 câu; nên phản ánh bối cảnh global và/hoặc kênh truyền sang VN nếu có trong dữ liệu",
      "impact": "High | Medium | Low",
      "source_urls": ["URL liên quan"]
    }}
  ],
  "vietnam_watch": "Góc Việt Nam (ngắn gọn, có thể tách khác executive nếu cần)",
  "global_watch": "Góc quốc tế (ngắn)",
  "risks_to_watch": ["Rủi ro 1", "Rủi ro 2"],
  "important_articles": [
    {{
      "title": "Tiêu đề bài",
      "source": "Nguồn",
      "why_it_matters": "Vì sao quan trọng",
      "url": "URL"
    }}
  ],
  "data_quality_notes": "Nêu rõ bài nào thiếu nội dung/summary nếu ảnh hưởng chất lượng"
}}

Dữ liệu bài viết:
{article_json}
""".strip()


def parse_gemini_json_text(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```\s*$", "", cleaned)

    def _loads(candidate: str) -> dict[str, Any]:
        parsed = json.loads(candidate)
        if not isinstance(parsed, dict):
            raise json.JSONDecodeError("expected JSON object", candidate, 0)
        return parsed

    try:
        return _loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            sliced = cleaned[start : end + 1]
            try:
                return _loads(sliced)
            except json.JSONDecodeError:
                repaired = re.sub(r",\s*([}\]])", r"\1", sliced)
                return _loads(repaired)
        raise


def call_gemini(
    prompt: str,
    model: str,
    api_key: str,
    timeout: int = 600,
    *,
    max_retries: int = 8,
    min_retry_interval: float = MIN_REQUEST_INTERVAL_SECONDS,
    max_output_tokens: int | None = None,
) -> dict[str, Any]:
    url = GEMINI_GENERATE_URL.format(model=model) + "?" + urlencode({"key": api_key})
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
            "maxOutputTokens": max_output_tokens or MODEL_OUTPUT_TOKEN_LIMIT_DEFAULT,
        },
    }
    body = json.dumps(payload).encode("utf-8")
    last_error: Exception | None = None

    for attempt in range(max_retries):
        request = Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
            content = response_payload["candidates"][0]["content"]["parts"][0]["text"]
            return parse_gemini_json_text(content)
        except HTTPError as error:
            last_error = error
            if error.code not in (429, 500, 503) or attempt >= max_retries - 1:
                raise
            retry_after = error.headers.get("Retry-After")
            wait = int(retry_after) if retry_after and str(retry_after).isdigit() else min(180, 20 * (2**attempt))
            wait = max(wait, min_retry_interval)
            print(
                f"Gemini HTTP {error.code}, retry in {wait}s "
                f"({attempt + 1}/{max_retries}) model={model}",
                file=sys.stderr,
            )
            time.sleep(wait)
        except (json.JSONDecodeError, KeyError, IndexError) as error:
            last_error = error
            if attempt >= max_retries - 1:
                raise
            print(
                f"Gemini response parse error, retry in 10s "
                f"({attempt + 1}/{max_retries}): {error}",
                file=sys.stderr,
            )
            time.sleep(10)

    if last_error:
        raise last_error
    raise RuntimeError("call_gemini failed without exception")


def write_summary(path: Path, summary: dict[str, Any], meta: dict[str, Any]) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "meta": meta,
        "summary": summary,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_enriched(path: Path, source_payload: dict[str, Any], articles: list[dict[str, Any]]) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_generated_at": source_payload.get("generated_at"),
        "count": len(articles),
        "articles": articles,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Summarize crawled news JSON with Gemini (no web fetch by default)."
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_FILE),
        help="Input JSON (default: news_for_ai.json full text)",
    )
    parser.add_argument("--enriched-output", default=str(DEFAULT_ENRICHED_FILE), help="Path to enriched article JSON")
    parser.add_argument("--output", default=None, help="Gemini summary JSON (default by --mode)")
    parser.add_argument(
        "--mode",
        choices=("digest", "macro"),
        default="digest",
        help="digest = multi-sector 48h read; macro = legacy macro brief",
    )
    parser.add_argument(
        "--max-articles",
        type=int,
        default=None,
        help="Cap articles sent to Gemini (stratified by source). Default: 0 = all. Macro default: 40.",
    )
    parser.add_argument(
        "--max-article-chars",
        type=int,
        default=None,
        help="Cap chars of text per article. Default: 0 = full text from JSON. Macro default: 6000.",
    )
    parser.add_argument("--fetch-timeout", type=int, default=20, help="Seconds per article fetch if --refetch-url")
    parser.add_argument(
        "--refetch-url",
        action="store_true",
        help="Re-fetch URLs when local text is short (default: only use JSON text field)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Gemini model id (default: gemini-1.5-flash for digest, gemini-2.5-flash for macro)",
    )
    parser.add_argument(
        "--cap-prompt",
        action="store_true",
        help="Shrink article count until prompt fits --max-prompt-chars (off by default for digest)",
    )
    parser.add_argument(
        "--max-prompt-chars",
        type=int,
        default=700_000,
        help="Used only with --cap-prompt",
    )
    parser.add_argument(
        "--batch-digest",
        action="store_true",
        help="Split full news_for_ai.json into chunks, summarize each, then merge (fits 1M context)",
    )
    parser.add_argument(
        "--batch-chunk-chars",
        type=int,
        default=BATCH_DIGEST_CHUNK_CHARS_DEFAULT,
        help="Legacy: max chars/chunk (0 = auto token budget from model + --tpm-limit)",
    )
    parser.add_argument(
        "--max-input-tokens-per-request",
        type=int,
        default=0,
        help="Cap input tokens per API call (0 = default 100000, free tier)",
    )
    parser.add_argument(
        "--tpm-limit",
        type=int,
        default=DEFAULT_FREE_TPM_LIMIT,
        help="Optional ceiling per request (0 = use 100k default for free tier)",
    )
    parser.add_argument(
        "--min-request-interval",
        type=float,
        default=MIN_REQUEST_INTERVAL_SECONDS,
        help="Minimum seconds between successful Gemini requests (default 60)",
    )
    parser.add_argument(
        "--use-existing-outline",
        action="store_true",
        help="Load gemini_digest_outline.json and skip outline API call",
    )
    parser.add_argument(
        "--resume-partials",
        action="store_true",
        help="Resume chunk passes from gemini_digest_partials.json",
    )
    parser.add_argument(
        "--merge-only",
        action="store_true",
        help="Chỉ chạy lại bước merge (cần đủ partials; ~1 API call)",
    )
    parser.add_argument(
        "--max-api-calls",
        type=int,
        default=0,
        help="Stop after N Gemini calls this run (1 = one chunk/merge step; 0 = all)",
    )
    parser.add_argument(
        "--batch-partials-output",
        type=Path,
        default=PROJECT_DIR / "gemini_digest_partials.json",
        help="Intermediate batch summaries JSON",
    )
    parser.add_argument(
        "--outline-output",
        type=Path,
        default=PROJECT_DIR / "gemini_digest_outline.json",
        help="Global panorama outline from all headlines (outline-first pass)",
    )
    parser.add_argument(
        "--no-outline-first",
        action="store_true",
        help="Skip global outline pass (faster but less holistic merge)",
    )
    parser.add_argument(
        "--api-pause",
        type=float,
        default=MIN_REQUEST_INTERVAL_SECONDS,
        help="Seconds to sleep between Gemini API calls (min = --min-request-interval)",
    )
    parser.add_argument(
        "--gemini-timeout",
        type=int,
        default=1800,
        help="Seconds for Gemini API call (large full-file digest may need long timeout)",
    )
    parser.add_argument("--update-content", action="store_true", help="Update content.json for the website")
    parser.add_argument("--dry-run", action="store_true", help="Prepare prompt only; do not call Gemini")
    args = parser.parse_args()

    load_env_file(DEFAULT_ENV_FILE)
    api_key = os.environ.get("GEMINI_API_KEY", "")

    if not args.dry_run and not api_key:
        print("Missing GEMINI_API_KEY. Add it to .env or set environment variable.", file=sys.stderr)
        return 2

    input_path = Path(args.input)
    news_payload = load_json(input_path)
    articles = news_payload.get("articles", [])
    window_meta = news_payload.get("window") or {}

    if args.max_articles is not None:
        max_articles = args.max_articles
    elif args.mode == "digest":
        max_articles = 0
    else:
        max_articles = 40

    if args.max_article_chars is not None:
        max_article_chars = args.max_article_chars
    elif args.mode == "digest":
        max_article_chars = 0
    else:
        max_article_chars = 6000

    if args.model:
        model = args.model
    elif os.environ.get("GEMINI_MODEL"):
        model = os.environ["GEMINI_MODEL"]
    elif args.mode == "digest":
        model = DIGEST_DEFAULT_MODEL
    else:
        model = "gemini-2.5-flash"

    output_path = Path(args.output) if args.output else (
        DEFAULT_DIGEST_OUTPUT_FILE if args.mode == "digest" else DEFAULT_OUTPUT_FILE
    )

    if args.cap_prompt:
        enriched_articles, prompt, max_articles = fit_enriched_to_prompt_budget(
            articles,
            mode=args.mode,
            total_in_window=len(articles),
            window_meta=window_meta,
            max_articles=max_articles if max_articles > 0 else 300,
            max_article_chars=max_article_chars if max_article_chars > 0 else 1200,
            fetch_timeout=args.fetch_timeout,
            refetch_urls=args.refetch_url,
            max_prompt_chars=args.max_prompt_chars,
        )
    else:
        enriched_articles = enrich_articles(
            articles,
            max_articles,
            max_article_chars,
            args.fetch_timeout,
            refetch_urls=args.refetch_url,
            quiet=args.mode == "digest",
        )
        if args.batch_digest and args.mode == "digest":
            prompt = "(batch-digest: multiple chunk prompts + one merge)"
        elif args.mode == "digest":
            prompt = build_digest_prompt(
                enriched_articles,
                total_in_window=len(articles),
                window_meta=window_meta,
            )
        else:
            prompt = build_macro_prompt(enriched_articles)
    if not (args.merge_only and args.batch_digest):
        write_enriched(Path(args.enriched_output), news_payload, enriched_articles)

    print(f"Input file: {input_path}")
    print(f"Mode: {args.mode}")
    print(f"Batch digest: {args.batch_digest}")
    print(f"Refetch URLs: {args.refetch_url}")
    print(f"Input articles: {len(articles)}")
    print(f"Articles sent to Gemini: {len(enriched_articles)}")

    outline_path = Path(args.outline_output)
    use_existing_outline = args.use_existing_outline or outline_path.is_file()
    outline_first = (not args.no_outline_first) and not (
        use_existing_outline and load_existing_outline(outline_path)
    )
    max_input_per_request = resolve_max_input_tokens_per_request(
        model,
        args.max_input_tokens_per_request,
        args.tpm_limit,
    )
    existing_outline = load_existing_outline(outline_path) if use_existing_outline else None

    if args.batch_digest and args.mode == "digest":
        if args.batch_chunk_chars > 0:
            chunks = chunk_enriched_articles(enriched_articles, args.batch_chunk_chars)
        else:
            chunks = chunk_enriched_articles_by_tokens(
                enriched_articles,
                max_input_per_request,
                total_articles=len(articles),
                window_meta=window_meta,
                global_outline=existing_outline,
            )
        outline_tok = 0
        if outline_first:
            catalog = compact_catalog_for_outline(enriched_articles)
            outline_tok = estimate_tokens_from_chars(
                len(
                    build_digest_outline_prompt(
                        catalog, total_articles=len(articles), window_meta=window_meta
                    )
                )
            )
        chunk_tokens = sum(
            estimate_digest_chunk_prompt_tokens(
                c,
                batch_index=i,
                batch_total=len(chunks),
                total_articles=len(articles),
                window_meta=window_meta,
                global_outline=existing_outline,
            )
            for i, c in enumerate(chunks, start=1)
        )
        est_tokens = outline_tok + chunk_tokens + estimate_tokens_from_chars(50_000)
        outline_extra = 1 if outline_first else 0
        pending_partials = len(chunks)
        if args.resume_partials:
            pending_partials = max(
                0,
                len(chunks) - len({int(p.get("batch_index") or 0) for p in load_existing_partials(Path(args.batch_partials_output))}),
            )
        api_est = outline_extra + pending_partials + (0 if args.dry_run else 1)
        wall_min = api_est * max(args.api_pause, args.min_request_interval) / 60
        print(
            f"Model context: {model_input_token_limit(model)} input tokens; "
            f"cap {max_input_per_request}/request (tpm_limit={args.tpm_limit})"
        )
        print(
            f"Batch: outline={outline_extra} + {len(chunks)} chunks "
            f"({pending_partials} pending) + 1 merge "
            f"~{api_est} API calls, est. input tokens ~{est_tokens}, "
            f"~{wall_min:.0f} min min spacing"
        )
    else:
        print(f"Prompt chars: {len(prompt)}")
        est_tokens = estimate_tokens_from_chars(len(prompt))
    print(f"Model: {model}")
    print(f"Estimated input tokens: ~{est_tokens} (chars={len(prompt)})")
    print(f"Output: {output_path}")
    print(f"Enriched output: {args.enriched_output}")

    if args.dry_run:
        if args.batch_digest and args.mode == "digest":
            run_batch_digest(
                enriched_articles,
                model=model,
                api_key=api_key or "dry-run",
                window_meta=window_meta,
                total_articles=len(articles),
                max_input_tokens_per_request=max_input_per_request,
                batch_chunk_chars=args.batch_chunk_chars,
                gemini_timeout=args.gemini_timeout,
                api_pause_seconds=0,
                min_request_interval=0,
                partials_path=Path(args.batch_partials_output),
                outline_path=outline_path,
                outline_first=outline_first,
                use_existing_outline=use_existing_outline,
                resume_partials=args.resume_partials,
                merge_only=args.merge_only,
                max_api_calls=args.max_api_calls,
                dry_run=True,
            )
        else:
            dry_prompt_path = PROJECT_DIR / "prompts" / "last_gemini_prompt.txt"
            dry_prompt_path.parent.mkdir(parents=True, exist_ok=True)
            dry_prompt_path.write_text(prompt, encoding="utf-8")
            print(f"Dry-run prompt saved: {dry_prompt_path}")
        return 0

    try:
        api_calls = 1
        if args.batch_digest and args.mode == "digest":
            summary, partials, api_calls = run_batch_digest(
                enriched_articles,
                model=model,
                api_key=api_key,
                window_meta=window_meta,
                total_articles=len(articles),
                max_input_tokens_per_request=max_input_per_request,
                batch_chunk_chars=args.batch_chunk_chars,
                gemini_timeout=args.gemini_timeout,
                api_pause_seconds=args.api_pause,
                min_request_interval=args.min_request_interval,
                partials_path=Path(args.batch_partials_output),
                outline_path=outline_path,
                outline_first=outline_first,
                use_existing_outline=use_existing_outline,
                resume_partials=args.resume_partials,
                merge_only=args.merge_only,
                max_api_calls=args.max_api_calls,
                dry_run=False,
            )
        else:
            summary = call_gemini(prompt, model, api_key, timeout=args.gemini_timeout)
    except (HTTPError, URLError, TimeoutError, KeyError, json.JSONDecodeError) as error:
        print(f"Gemini API error: {error}", file=sys.stderr)
        return 1

    if summary is None:
        if args.batch_digest and args.max_api_calls > 0:
            print(
                f"Incremental step done ({api_calls} API call(s)). "
                "Run again with --resume-partials (or scripts/run_digest_loop.py)."
            )
            return 0
        print("Digest incomplete (missing partials or merge). Re-run with --resume-partials.", file=sys.stderr)
        return 1

    if args.mode == "digest" and isinstance(summary, dict):
        partials_for_finalize: list[dict[str, Any]] | None = None
        if args.batch_digest:
            partials_for_finalize = load_existing_partials(Path(args.batch_partials_output))
        summary = finalize_digest_summary(
            summary,
            partials=partials_for_finalize,
            input_articles=enriched_articles,
        )

    meta = {
        "input_file": str(input_path.resolve()),
        "enriched_file": str(Path(args.enriched_output).resolve()),
        "model": model,
        "estimated_input_tokens": est_tokens,
        "prompt_chars": len(prompt) if not args.batch_digest else None,
        "mode": args.mode,
        "batch_digest": args.batch_digest,
        "outline_first": args.batch_digest and not args.no_outline_first,
        "api_calls": api_calls,
        "refetch_urls": args.refetch_url,
        "input_article_count": len(articles),
        "sent_article_count": len(enriched_articles),
        "window": window_meta,
    }
    write_summary(output_path, summary, meta)

    if args.update_content:
        articles_path = Path(args.enriched_output)
        if not articles_path.is_file():
            articles_path = input_path
        if args.mode == "digest" or output_path.name.startswith("gemini_digest"):
            n = rebuild_content_from_digest(
                output_path,
                articles_path,
                DEFAULT_CONTENT_FILE,
                fetch_images=True,
                metadata_timeout=12,
            )
        else:
            n = rebuild_content_from_digest(
                output_path,
                articles_path,
                DEFAULT_CONTENT_FILE,
                fetch_images=True,
                metadata_timeout=12,
            )
        print(f"Website content: {n} article cards -> {DEFAULT_CONTENT_FILE}")

    print(f"Done: summary written to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
