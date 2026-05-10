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


def build_article_lookup(enriched_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lookup = {}
    for article in enriched_payload.get("articles", []):
        url = str(article.get("url", ""))
        if url:
            lookup[url] = article
    return lookup


def collect_source_urls(summary: dict[str, Any]) -> list[tuple[str, str, str]]:
    urls = []
    for point in summary.get("key_points", []):
        if not isinstance(point, dict):
            continue
        theme = str(point.get("title", "Tin liên quan"))
        impact = str(point.get("impact", "Medium"))
        for url in point.get("sources", []):
            if url:
                urls.append((str(url), theme, impact))
    return urls


def build_featured_articles(
    summary: dict[str, Any],
    enriched_payload: dict[str, Any],
    max_articles: int,
    fetch_images: bool,
    timeout: int,
) -> list[dict[str, Any]]:
    lookup = build_article_lookup(enriched_payload)
    seen: set[str] = set()
    featured = []

    for url, theme, impact in collect_source_urls(summary):
        if url in seen or len(featured) >= max_articles:
            continue
        seen.add(url)

        article = lookup.get(url, {})
        metadata = fetch_metadata(url, timeout) if fetch_images else {"image_url": "", "description": "", "metadata_status": "skipped"}
        summary_text = clean_text(str(article.get("summary") or metadata.get("description") or ""))

        featured.append(
            {
                "title": article.get("title", "Tin liên quan"),
                "url": url,
                "source": article.get("source", "Nguồn gốc"),
                "category": article.get("category", "macro"),
                "region": article.get("region", "unknown"),
                "published_at": article.get("published_at", ""),
                "summary": summary_text,
                "theme": theme,
                "impact": impact,
                "image_url": metadata.get("image_url", ""),
                "metadata_status": metadata.get("metadata_status", ""),
            }
        )

    return featured


def build_sections(summary: dict[str, Any], featured_articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for article in featured_articles:
        buckets.setdefault(str(article.get("theme", "Tin liên quan")), []).append(article)

    sections = []
    for title, articles in buckets.items():
        sections.append({"title": title, "items": articles})
    return sections


def build_payload(final_payload: dict[str, Any], enriched_payload: dict[str, Any], featured_articles: list[dict[str, Any]]) -> dict[str, Any]:
    summary = final_payload.get("summary", {})
    generated_at = final_payload.get("generated_at") or datetime.now(timezone.utc).isoformat()
    key_points = summary.get("key_points", [])
    risks = summary.get("risks_to_watch", [])

    return {
        "siteTitle": "LEON Quant Labs",
        "sectionLabel": "Daily Macro Intelligence",
        "generatedAt": generated_at,
        "chatSectionTitle": summary.get("title", "Macro Daily Brief"),
        "marketImpact": summary.get("market_impact", "Mixed"),
        "executiveSummary": summary.get("executive_summary", ""),
        "keyPoints": key_points,
        "vietnamWatch": summary.get("vietnam_watch", ""),
        "globalWatch": summary.get("global_watch", ""),
        "risksToWatch": risks,
        "editorNotes": summary.get("editor_notes", ""),
        "featuredArticles": featured_articles,
        "newsSections": build_sections(summary, featured_articles),
        "stats": {
            "articlesAnalyzed": enriched_payload.get("count", len(enriched_payload.get("articles", []))),
            "featuredLinks": len(featured_articles),
            "pipeline": "Public sources + editorial review",
        },
        "chatItems": [
            {
                "title": summary.get("title", "Macro Daily Brief"),
                "content": (
                    f"{summary.get('executive_summary', '')}\n\n"
                    f"Market impact: {summary.get('market_impact', 'Mixed')}"
                ).strip(),
            },
            {
                "title": "Điểm chính",
                "content": "\n\n".join(
                    f"- {item.get('title', 'Ý chính')}: {item.get('detail', '')} "
                    f"(Impact: {item.get('impact', 'N/A')})"
                    for item in key_points
                    if isinstance(item, dict)
                ),
            },
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build public website content from final summary and source articles.")
    parser.add_argument("--final-input", default=str(DEFAULT_FINAL_FILE), help="Path to final_summary.json")
    parser.add_argument("--enriched-input", default=str(DEFAULT_ENRICHED_FILE), help="Path to enriched_news.json")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_FILE), help="Path to content.json")
    parser.add_argument("--max-featured", type=int, default=12, help="Max source links to feature")
    parser.add_argument("--metadata-timeout", type=int, default=8, help="Seconds per image metadata fetch")
    parser.add_argument("--skip-images", action="store_true", help="Do not fetch original image metadata")
    args = parser.parse_args()

    final_payload = load_json(Path(args.final_input))
    enriched_payload = load_json(Path(args.enriched_input))
    summary = final_payload.get("summary", {})
    featured_articles = build_featured_articles(
        summary,
        enriched_payload,
        args.max_featured,
        not args.skip_images,
        args.metadata_timeout,
    )
    payload = build_payload(final_payload, enriched_payload, featured_articles)
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Done: {len(featured_articles)} featured links -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
