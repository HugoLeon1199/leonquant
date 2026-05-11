import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT_FILE = PROJECT_DIR / "news_output.json"
DEFAULT_ENRICHED_FILE = PROJECT_DIR / "enriched_news.json"
DEFAULT_OUTPUT_FILE = PROJECT_DIR / "gemini_summary.json"
DEFAULT_CONTENT_FILE = PROJECT_DIR / "content.json"
DEFAULT_ENV_FILE = PROJECT_DIR / ".env"
GEMINI_GENERATE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
USER_AGENT = "LEONQuantLabsArticleFetcher/0.1 (personal research; contact: local-dev)"


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

    return clean_text(content)[:max_chars], "html"


def enrich_articles(
    articles: list[dict[str, Any]],
    max_articles: int,
    max_article_chars: int,
    timeout: int,
) -> list[dict[str, Any]]:
    selected = articles if max_articles <= 0 else articles[:max_articles]
    enriched = []

    for index, article in enumerate(selected, start=1):
        url = str(article.get("url", ""))
        full_text = ""
        fetch_status = "missing_url"
        if url:
            try:
                full_text, fetch_status = fetch_article_text(url, timeout, max_article_chars)
                if not full_text:
                    fetch_status = "empty_content"
            except (HTTPError, URLError, TimeoutError, UnicodeError, ValueError) as error:
                fetch_status = f"fetch_error: {error}"

        fallback_summary = str(article.get("summary", ""))
        content_for_ai = full_text or fallback_summary
        enriched_article = {
            **article,
            "content_for_ai": content_for_ai,
            "content_chars": len(content_for_ai),
            "fetch_status": fetch_status,
        }
        enriched.append(enriched_article)
        print(f"{index}/{len(selected)} {fetch_status}: {article.get('source')} - {article.get('title')}")

    return enriched


def compact_for_gemini(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compacted = []
    for article in articles:
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


def build_prompt(enriched_articles: list[dict[str, Any]]) -> str:
    article_json = json.dumps(compact_for_gemini(enriched_articles), ensure_ascii=False)
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


def call_gemini(prompt: str, model: str, api_key: str, timeout: int = 120) -> dict[str, Any]:
    url = GEMINI_GENERATE_URL.format(model=model) + "?" + urlencode({"key": api_key})
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=timeout) as response:
        response_payload = json.loads(response.read().decode("utf-8"))

    content = response_payload["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(content)


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


def write_content_json(path: Path, summary: dict[str, Any]) -> None:
    cards = [
        {
            "title": summary.get("title", "Macro Daily Brief"),
            "content": (
                f"{summary.get('executive_summary', '')}\n\n"
                f"Market impact: {summary.get('market_impact', 'Mixed')}"
            ).strip(),
        }
    ]

    key_themes = summary.get("key_themes", [])
    if key_themes:
        cards.append(
            {
                "title": "Chủ đề chính",
                "content": "\n\n".join(
                    f"- {item.get('theme', 'Theme')}: {item.get('summary', '')} "
                    f"(Impact: {item.get('impact', 'N/A')})"
                    for item in key_themes
                    if isinstance(item, dict)
                ),
            }
        )

    if summary.get("vietnam_watch"):
        cards.append({"title": "Việt Nam watch", "content": summary["vietnam_watch"]})

    if summary.get("global_watch"):
        cards.append({"title": "Global watch", "content": summary["global_watch"]})

    risks = summary.get("risks_to_watch", [])
    if risks:
        cards.append({"title": "Rủi ro cần theo dõi", "content": "\n".join(f"- {risk}" for risk in risks)})

    payload = {
        "chatSectionTitle": "Cập nhật macro từ Gemini",
        "chatItems": cards,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch article details and summarize with Gemini API.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT_FILE), help="Path to news_output.json")
    parser.add_argument("--enriched-output", default=str(DEFAULT_ENRICHED_FILE), help="Path to enriched article JSON")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_FILE), help="Path to Gemini summary JSON")
    parser.add_argument("--max-articles", type=int, default=40, help="Max articles to fetch/summarize. Use 0 for all.")
    parser.add_argument("--max-article-chars", type=int, default=6000, help="Max extracted chars per article")
    parser.add_argument("--fetch-timeout", type=int, default=20, help="Seconds per article fetch")
    parser.add_argument("--model", default=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"))
    parser.add_argument("--update-content", action="store_true", help="Update content.json for the website")
    parser.add_argument("--dry-run", action="store_true", help="Fetch/enrich only; do not call Gemini")
    args = parser.parse_args()

    load_env_file(DEFAULT_ENV_FILE)
    api_key = os.environ.get("GEMINI_API_KEY", "")

    if not args.dry_run and not api_key:
        print("Missing GEMINI_API_KEY. Add it to .env or set environment variable.", file=sys.stderr)
        return 2

    news_payload = load_json(Path(args.input))
    articles = news_payload.get("articles", [])
    enriched_articles = enrich_articles(articles, args.max_articles, args.max_article_chars, args.fetch_timeout)
    write_enriched(Path(args.enriched_output), news_payload, enriched_articles)

    prompt = build_prompt(enriched_articles)
    print(f"Input articles: {len(articles)}")
    print(f"Articles sent to Gemini: {len(enriched_articles)}")
    print(f"Prompt chars: {len(prompt)}")
    print(f"Model: {args.model}")
    print(f"Enriched output: {args.enriched_output}")

    if args.dry_run:
        return 0

    try:
        summary = call_gemini(prompt, args.model, api_key)
    except (HTTPError, URLError, TimeoutError, KeyError, json.JSONDecodeError) as error:
        print(f"Gemini API error: {error}", file=sys.stderr)
        return 1

    meta = {
        "input_file": str(Path(args.input).resolve()),
        "enriched_file": str(Path(args.enriched_output).resolve()),
        "model": args.model,
        "input_article_count": len(articles),
        "sent_article_count": len(enriched_articles),
    }
    write_summary(Path(args.output), summary, meta)

    if args.update_content:
        write_content_json(DEFAULT_CONTENT_FILE, summary)

    print(f"Done: summary written to {args.output}")
    if args.update_content:
        print(f"Website content updated: {DEFAULT_CONTENT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
