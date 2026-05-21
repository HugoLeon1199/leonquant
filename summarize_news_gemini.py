import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from build_website_content import rebuild_content_from_digest, rebuild_content_json

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

# Đa ngành: taxonomy + ngưỡng tối thiểu (merge không được gom còn 2–3 mảng).
DIGEST_SECTOR_TAXONOMY: tuple[str, ...] = (
    "Kinh tế & tài chính",
    "Chính trị & địa chính trị",
    "Xã hội & pháp luật",
    "Công nghệ & khoa học",
    "Y tế & sức khỏe",
    "Môi trường & năng lượng",
    "Thể thao & giải trí",
    "Văn hóa & giáo dục",
    "Lao động & doanh nghiệp",
    "An ninh & quốc phòng",
)
DIGEST_MIN_SECTORS_FINAL = 6
DIGEST_MIN_NOTABLE_FINAL = 12
DIGEST_MAX_OUTLINE_THEMES = 18
DIGEST_MERGE_MAX_OUTPUT_TOKENS = 32_768


def _digest_multisector_rules_block(*, for_merge: bool = False) -> str:
    names = " | ".join(DIGEST_SECTOR_TAXONOMY)
    lines = [
        "## Phạm vi đa ngành (bắt buộc)",
        f"- Quét và ghi nhận **mọi** lĩnh vực có tin trong dữ liệu — không chỉ hạ tầng / chứng khoán / AI.",
        f"- Nhóm chuẩn (dùng đúng hoặc gần tên): {names}.",
        "- Mỗi nhóm **có tin** → phải có mục riêng (sector / sector_notes / dominant_theme); **không** gộp hết vào 2–3 mục chung.",
        "- Tin VN và quốc tế đều phải được phân bổ vào đúng lĩnh vực.",
    ]
    if for_merge:
        lines.extend(
            [
                f"- **`sectors` cuối cùng: tối thiểu {DIGEST_MIN_SECTORS_FINAL}** mục (nếu dữ liệu có đủ chủ đề).",
                f"- Mỗi sector: **4–8** `key_points`, **2+** `source_urls` khi có trong partials.",
                f"- **`notable_articles`: tối thiểu {DIGEST_MIN_NOTABLE_FINAL}**, đa dạng lĩnh vực (không chỉ kinh tế).",
                "- Mọi `dominant_themes` trong khung toàn cảnh **phải** được phản ánh trong `sectors` hoặc highlights — không bỏ theme chỉ vì gọn JSON.",
                "- `executive_overview` + `sectors` ≈ **2.000–3.500 từ** tổng (đọc ~10–15 phút).",
            ]
        )
    else:
        lines.extend(
            [
                f"- Outline: **tối đa {DIGEST_MAX_OUTLINE_THEMES}** `dominant_themes`, mỗi theme gắn `sectors` phù hợp.",
                "- Mỗi chunk: ghi **đủ** `sector_notes` cho mọi lĩnh vực có tin trong phần đó (tối đa 10 nhóm/chunk).",
            ]
        )
    return "\n".join(lines)


def validate_digest_multisector_coverage(summary: dict[str, Any]) -> list[str]:
    """Cảnh báo sau merge nếu output quá hẹp (không fail pipeline)."""
    warnings: list[str] = []
    sectors = summary.get("sectors") if isinstance(summary.get("sectors"), list) else []
    if len(sectors) < DIGEST_MIN_SECTORS_FINAL:
        warnings.append(
            f"sectors chỉ có {len(sectors)} mục (mong đợi ≥{DIGEST_MIN_SECTORS_FINAL} — chạy lại merge hoặc chỉnh prompt)."
        )
    notable = summary.get("notable_articles") if isinstance(summary.get("notable_articles"), list) else []
    if len(notable) < DIGEST_MIN_NOTABLE_FINAL:
        warnings.append(
            f"notable_articles chỉ có {len(notable)} mục (mong đợi ≥{DIGEST_MIN_NOTABLE_FINAL})."
        )
    for i, sec in enumerate(sectors):
        if not isinstance(sec, dict):
            continue
        kps = sec.get("key_points") if isinstance(sec.get("key_points"), list) else []
        if len(kps) < 3:
            warnings.append(f"sectors[{i}] ({sec.get('name', '?')}) chỉ có {len(kps)} key_points.")
    return warnings


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

## Mục tiêu đầu ra
- Viết bằng **tiếng Việt**, mạch lạc, đủ chi tiết để người đọc **5–10 phút** nắm **toàn cảnh** tin tức (khoảng 1.500–2.500 từ ở phần narrative chính).
- **Đa ngành bắt buộc:** tối thiểu {DIGEST_MIN_SECTORS_FINAL} mục `sectors` nếu dữ liệu có đủ chủ đề; không thu hẹp còn hạ tầng/chứng khoán/AI.
{_digest_multisector_rules_block()}
- Ưu tiên sự kiện lặp lại, tin nhiều nguồn, hoặc hàm ý rộng; gom chủ đề trùng.
- Mỗi ý quan trọng nên kèm URL từ dữ liệu khi có thể.

Trả về DUY NHẤT JSON hợp lệ theo schema:
{{
  "title": "Bản tin tổng hợp 48 giờ",
  "reading_time_minutes": "5-10",
  "executive_overview": "2-4 đoạn: bức tranh chung hai ngày qua",
  "sectors": [
    {{
      "name": "Tên lĩnh vực (vd. Kinh tế & tài chính)",
      "summary": "Tóm tắt chi tiết 1-3 đoạn ngắn cho lĩnh vực này",
      "key_points": ["Điểm 1", "Điểm 2"],
      "source_urls": ["url1", "url2"]
    }}
  ],
  "vietnam_highlights": "Tin Việt Nam nổi bật (nếu có trong dữ liệu)",
  "international_highlights": "Tin quốc tế nổi bật (nếu có)",
  "timeline": [
    {{
      "date": "YYYY-MM-DD",
      "headlines": ["Sự kiện/tin chính trong ngày theo dữ liệu"]
    }}
  ],
  "notable_articles": [
    {{
      "title": "Tiêu đề",
      "source": "nguồn",
      "url": "url",
      "why_notable": "1 câu"
    }}
  ],
  "gaps_and_limits": "Bài thiếu text hoặc trùng chủ đề (nếu có)"
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
Bạn là tổng biên tập tin. Nhiệm vụ: đọc **TOÀN BỘ** danh mục {total_articles} bài (chỉ title, nguồn, ngày, url) và vẽ **bức tranh toàn cảnh** 48 giờ qua.

## Quy tắc
- CHỈ dùng danh mục bên dưới. KHÔNG mở URL, KHÔNG tìm web.
- Phát hiện chủ đề lặp lại trên nhiều nguồn, tin VN vs quốc tế, sự kiện nổi bật nhất.
- Đây là bước **khung xương**; các bước sau sẽ đọc nội dung chi tiết từng phần — khung phải phản ánh **đủ** {total_articles} bài.
- JSON gọn: **tối đa {DIGEST_MAX_OUTLINE_THEMES}** `dominant_themes` (phủ **đủ** các nhóm lĩnh vực có trong danh mục), **tối đa 3** mục `timeline_sketch`, **không** liệt kê từng bài trong output (chỉ ước lượng số lượng).
{_digest_multisector_rules_block()}

Cửa sổ: {window_desc}

Trả về DUY NHẤT JSON:
{{
  "total_articles": {total_articles},
  "panorama_summary": "2-3 đoạn: bức tranh tổng thể 48h",
  "dominant_themes": [
    {{
      "theme": "Tên chủ đề/sự kiện",
      "why_dominant": "Vì sao nổi bật (nhiều bài/nguồn)",
      "approx_article_count": "ước lượng số bài liên quan trong danh mục",
      "regions": ["vietnam", "international"],
      "sectors": ["kinh tế", "chính trị", "xã hội", "công nghệ", "thể thao", "..."]
    }}
  ],
  "vietnam_vs_global": "So sánh trọng tâm VN và thế giới",
  "timeline_sketch": [
    {{"date": "YYYY-MM-DD", "top_headlines": ["5-10 tiêu đề hoặc sự kiện chính"]}}
  ],
  "sources_most_active": ["domain1", "domain2"],
  "gaps": "Mảng tin có vẻ thiếu trong danh mục (nếu có)"
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
Bạn là biên tập viên tổng hợp tin. Đây là **phần {batch_index}/{batch_total}** của bản tin 48 giờ (LEON Quant Labs).

## Quy tắc
- CHỈ dùng JSON bài viết bên dưới + khung toàn cảnh (nếu có). KHÔNG mở URL, KHÔNG tìm web, KHÔNG bịa.
- Toàn bộ pipeline có {total_articles} bài; bạn thấy phần này — ghi nhận đủ sự kiện **trong phần được giao**, đối chiếu khung để biết phần này thuộc chủ đề lớn nào.
- **JSON hợp lệ:** mỗi `summary` tối đa 150 từ; **tối đa 10** `sector_notes` (mỗi lĩnh vực có tin trong phần này phải có 1 mục); mỗi sector **4–8** `key_points`; `notable_articles` tối đa **8**; không lặp URL.
{_digest_multisector_rules_block()}
{outline_block}
## Cửa sổ: {window_desc}

Trả về DUY NHẤT JSON:
{{
  "batch_index": {batch_index},
  "batch_total": {batch_total},
  "articles_in_batch": {len(chunk)},
  "sector_notes": [
    {{
      "name": "Lĩnh vực (kinh tế, chính trị, xã hội, công nghệ, thể thao, ...)",
      "summary": "Tóm tắt chi tiết từ phần bài này",
      "key_points": ["..."],
      "source_urls": ["..."]
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


def build_digest_merge_prompt(
    partials: list[dict[str, Any]],
    *,
    total_articles: int,
    window_meta: dict[str, Any],
    global_outline: dict[str, Any] | None,
) -> str:
    partial_json = json.dumps(partials, ensure_ascii=False)
    window_desc = json.dumps(window_meta, ensure_ascii=False)
    outline_block = ""
    if global_outline:
        outline_block = (
            "\n## Khung toàn cảnh (từ TOÀN BỘ "
            f"{total_articles} tiêu đề — ưu tiên giữ đúng bức tranh tổng)\n"
            + json.dumps(global_outline, ensure_ascii=False)
            + "\n"
        )
    return f"""
Bạn là biên tập viên tổng hợp tin LEON Quant Labs.

Đã có {len(partials)} bản tóm tắt **phần** (chi tiết nội dung) từ tổng {total_articles} bài tin 48h. Cửa sổ: {window_desc}.
{outline_block}
Nhiệm vụ: **Gộp** thành **một** bản tin duy nhất, tiếng Việt, đọc **10–15 phút** (~2.000–3.500 từ), **toàn cảnh đa ngành** (VN + quốc tế).
- Khung toàn cảnh = xương sống (chủ đề trội trên toàn bộ {total_articles} bài).
- Partials = chi tiết từng phần — **gộp KHÔNG được làm mất** chủ đề lớn trong khung; **cấm** chỉ giữ 2–3 sector (hạ tầng, CK, AI) nếu partials/outline còn nhiều lĩnh vực khác.
- Gom `sector_notes` trùng tên lĩnh vực; **không** nhồi mọi thứ vào một mục "Khác".
{_digest_multisector_rules_block(for_merge=True)}
CHỈ dùng dữ liệu được cung cấp — không bổ sung từ bên ngoài.

Trả về DUY NHẤT JSON:
{{
  "title": "Bản tin tổng hợp 48 giờ",
  "reading_time_minutes": "10-15",
  "executive_overview": "3-5 đoạn bức tranh chung (đủ lĩnh vực, không chỉ kinh tế)",
  "sectors": [
    {{
      "name": "Tên lĩnh vực (theo taxonomy)",
      "summary": "1-3 đoạn cho lĩnh vực này",
      "key_points": ["ít nhất 4 ý, mỗi ý 1 câu cụ thể"],
      "source_urls": ["url1", "url2", "..."]
    }}
  ],
  "vietnam_highlights": "...",
  "international_highlights": "...",
  "timeline": [{{"date": "YYYY-MM-DD", "headlines": ["..."]}}],
  "notable_articles": [{{"title": "...", "source": "...", "url": "...", "why_notable": "..."}}],
  "gaps_and_limits": "Điểm còn mờ sau khi gộp batch (nếu có)"
}}

Các partial batch:
{partial_json}
""".strip()


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
        merge_prompt = build_digest_merge_prompt(
            [p["summary"] for p in sorted(partials, key=lambda p: int(p.get("batch_index") or 0))],
            total_articles=total_articles,
            window_meta=window_meta,
            global_outline=global_outline,
        )
        final = call_gemini(
            merge_prompt,
            model,
            api_key,
            timeout=gemini_timeout,
            min_retry_interval=min_request_interval,
            max_output_tokens=DIGEST_MERGE_MAX_OUTPUT_TOKENS,
        )
        if isinstance(final, dict):
            for w in validate_digest_multisector_coverage(final):
                print(f"WARN digest coverage: {w}", file=sys.stderr)
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

    merge_prompt = build_digest_merge_prompt(
        [p["summary"] for p in sorted(partials, key=lambda p: int(p.get("batch_index") or 0))],
        total_articles=total_articles,
        window_meta=window_meta,
        global_outline=global_outline,
    )
    print(f"Merge prompt ~{estimate_tokens_from_chars(len(merge_prompt))} tokens")
    wait_between_gemini_requests(api_pause_seconds, min_request_interval)

    final = call_gemini(
        merge_prompt,
        model,
        api_key,
        timeout=gemini_timeout,
        min_retry_interval=min_request_interval,
        max_output_tokens=DIGEST_MERGE_MAX_OUTPUT_TOKENS,
    )
    api_calls += 1
    if isinstance(final, dict):
        for w in validate_digest_multisector_coverage(final):
            print(f"WARN digest coverage: {w}", file=sys.stderr)
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
            f"≈ {api_est} API calls, est. input tokens ~{est_tokens}, "
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
            n = rebuild_content_json(
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
