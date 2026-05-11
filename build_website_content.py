import argparse
import json
import re
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_FINAL_FILE = PROJECT_DIR / "final_summary.json"
DEFAULT_ENRICHED_FILE = PROJECT_DIR / "enriched_news.json"
DEFAULT_OUTPUT_FILE = PROJECT_DIR / "content.json"
USER_AGENT = "LEONQuantLabsMetadataFetcher/0.1 (personal research; contact: local-dev)"


class MetadataExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.image_url = ""
        self.description = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "meta":
            return

        attr_map = {key.lower(): value or "" for key, value in attrs}
        prop = attr_map.get("property", "").lower()
        name = attr_map.get("name", "").lower()
        content = attr_map.get("content", "")

        if prop in {"og:image", "twitter:image"} and content and not self.image_url:
            self.image_url = content.strip()
        elif (prop == "og:description" or name == "description") and content and not self.description:
            self.description = clean_text(content)


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    text = unescape(value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_metadata(url: str, timeout: int) -> dict[str, str]:
    try:
        request = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(request, timeout=timeout) as response:
            raw = response.read(300_000)
            charset = response.headers.get_content_charset() or "utf-8"
        html = raw.decode(charset, errors="replace")
        extractor = MetadataExtractor()
        extractor.feed(html)
        return {
            "image_url": extractor.image_url,
            "description": extractor.description,
            "metadata_status": "ok",
        }
    except (HTTPError, URLError, TimeoutError, UnicodeError, ValueError) as error:
        return {
            "image_url": "",
            "description": "",
            "metadata_status": f"error: {error}",
        }


def _macro_world(summary: dict[str, Any]) -> str:
    s = str(summary.get("macro_world", "") or "").strip()
    if s:
        return s
    parts = [summary.get("macro_global"), summary.get("international_markets")]
    merged = "\n\n".join(str(p).strip() for p in parts if str(p or "").strip())
    if merged:
        return merged
    return str(summary.get("global_watch", "") or "").strip()


def _vietnam_macro(summary: dict[str, Any]) -> str:
    s = str(summary.get("vietnam_macro", "") or "").strip()
    if s:
        return s
    vi = str(summary.get("vietnam_implications", "") or "").strip()
    if vi:
        return vi
    return str(summary.get("vietnam_watch", "") or "").strip()


def build_all_article_cards(
    enriched_payload: dict[str, Any],
    fetch_images: bool,
    timeout: int,
) -> list[dict[str, Any]]:
    """Mọi bài trong enriched_news.json: minh bạch, có ảnh/ mô tả khi fetch được."""
    articles = list(enriched_payload.get("articles", []))

    def sort_key(a: dict[str, Any]) -> str:
        return str(a.get("published_at") or "")

    articles.sort(key=sort_key, reverse=True)
    cards: list[dict[str, Any]] = []

    for article in articles:
        url = str(article.get("url", ""))
        if not url:
            continue
        metadata = (
            fetch_metadata(url, timeout)
            if fetch_images
            else {"image_url": "", "description": "", "metadata_status": "skipped"}
        )
        summary_text = clean_text(str(article.get("summary") or metadata.get("description") or ""))
        cards.append(
            {
                "title": article.get("title", "Tin"),
                "url": url,
                "source": article.get("source", ""),
                "category": article.get("category", ""),
                "region": article.get("region", ""),
                "published_at": article.get("published_at", ""),
                "summary": summary_text,
                "image_url": metadata.get("image_url", ""),
                "metadata_status": metadata.get("metadata_status", ""),
            }
        )
    return cards


def build_payload(
    final_payload: dict[str, Any],
    enriched_payload: dict[str, Any],
    all_articles: list[dict[str, Any]],
) -> dict[str, Any]:
    summary = final_payload.get("summary", {})
    generated_at = final_payload.get("generated_at") or datetime.now(timezone.utc).isoformat()
    mw = _macro_world(summary)
    vm = _vietnam_macro(summary)
    exec_lead = str(summary.get("executive_summary", "") or "").strip()
    web_ver = summary.get("web_verification") if isinstance(summary.get("web_verification"), dict) else {}
    risks = summary.get("risks_to_watch", [])

    narrative_fallback = "\n\n".join(p for p in (mw, vm) if p).strip()

    return {
        "siteTitle": "LEON Quant Labs",
        "sectionLabel": "Daily Macro Intelligence",
        "generatedAt": generated_at,
        "chatSectionTitle": summary.get("title", "Macro Daily Brief"),
        "marketImpact": summary.get("market_impact", "Mixed"),
        "executiveSummary": exec_lead,
        "macroWorld": mw,
        "vietnamMacro": vm,
        "macroGlobal": summary.get("macro_global", ""),
        "internationalMarkets": summary.get("international_markets", ""),
        "vietnamImplications": summary.get("vietnam_implications", ""),
        "webVerification": web_ver,
        "risksToWatch": risks if isinstance(risks, list) else [],
        "allArticles": all_articles,
        "featuredArticles": all_articles,
        "stats": {
            "articlesCrawled": len(all_articles),
            "articlesInEnriched": enriched_payload.get("count", len(enriched_payload.get("articles", []))),
            "pipeline": "Crawl + Gemini + GPT (2 khối) + đủ link trong ngày",
        },
        "chatItems": [
            {
                "title": summary.get("title", "Macro Daily Brief"),
                "content": "\n\n".join(
                    p
                    for p in (
                        exec_lead,
                        mw,
                        vm,
                        f"Market impact: {summary.get('market_impact', 'Mixed')}",
                    )
                    if str(p).strip()
                ).strip()
                or narrative_fallback,
            },
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build content.json: 2 khối vĩ mô + toàn bộ tin crawl trong ngày.",
    )
    parser.add_argument("--final-input", default=str(DEFAULT_FINAL_FILE), help="Path to final_summary.json")
    parser.add_argument("--enriched-input", default=str(DEFAULT_ENRICHED_FILE), help="Path to enriched_news.json")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_FILE), help="Path to content.json")
    parser.add_argument(
        "--metadata-timeout",
        type=int,
        default=6,
        help="Seconds per URL when fetching og:image/description",
    )
    parser.add_argument("--skip-images", action="store_true", help="Do not fetch og metadata (faster)")
    args = parser.parse_args()

    final_payload = load_json(Path(args.final_input))
    enriched_payload = load_json(Path(args.enriched_input))
    all_cards = build_all_article_cards(
        enriched_payload,
        not args.skip_images,
        args.metadata_timeout,
    )
    payload = build_payload(final_payload, enriched_payload, all_cards)
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Done: {len(all_cards)} article cards -> {args.output}")
    return 0


def rebuild_content_json(
    final_payload_path: Path,
    enriched_path: Path,
    output_path: Path,
    *,
    fetch_images: bool = True,
    metadata_timeout: int = 6,
) -> int:
    """Dựng đủ payload website (macro + toàn bộ bài enriched) từ final_summary hoặc gemini_summary."""
    final_payload = load_json(final_payload_path)
    enriched_payload = load_json(enriched_path)
    all_cards = build_all_article_cards(
        enriched_payload,
        fetch_images,
        metadata_timeout,
    )
    payload = build_payload(final_payload, enriched_payload, all_cards)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(all_cards)


if __name__ == "__main__":
    raise SystemExit(main())
