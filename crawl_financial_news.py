import argparse
import json
import re
import sys
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCES_FILE = PROJECT_DIR / "news_sources.json"
DEFAULT_OUTPUT_FILE = PROJECT_DIR / "news_output.json"
DEFAULT_FINAL_FILE = PROJECT_DIR / "final_summary.json"
DEFAULT_ENRICHED_FILE = PROJECT_DIR / "enriched_news.json"
DEFAULT_CONTENT_FILE = PROJECT_DIR / "content.json"

USER_AGENT = (
    "LEONQuantLabsNewsCrawler/0.1 "
    "(personal research; contact: local-dev)"
)

MACRO_CATEGORY_SCORES = {
    "central-banks": 4,
    "macro": 4,
    "economy": 4,
    "commodities": 3,
    "banking": 3,
    "finance": 3,
    "markets": 2,
    "stocks": 2,
    "regulation": 2,
}

MACRO_KEYWORDS = [
    "adb",
    "bank of england",
    "bank of japan",
    "boj",
    "bond",
    "bonds",
    "budget",
    "central bank",
    "china economy",
    "commodity",
    "commodities",
    "cpi",
    "credit",
    "currency",
    "debt",
    "deficit",
    "ecb",
    "economic growth",
    "economy",
    "employment",
    "export",
    "fed",
    "federal reserve",
    "fiscal",
    "fpi",
    "gdp",
    "gold",
    "growth",
    "import",
    "inflation",
    "interest rate",
    "jobless",
    "labour market",
    "liquidity",
    "market cap",
    "monetary",
    "oil",
    "pmi",
    "policy",
    "rate cut",
    "rate hike",
    "recession",
    "tariff",
    "trade",
    "treasury",
    "unemployment",
    "usd",
    "yield",
    "bất động sản thế chấp",
    "cán cân",
    "chính sách",
    "chứng khoán",
    "dòng tiền",
    "đầu tư công",
    "địa chính trị",
    "giá vàng",
    "gdp",
    "hàng hóa",
    "kinh tế",
    "lãi suất",
    "lạm phát",
    "ngân hàng",
    "ngân hàng nhà nước",
    "nợ công",
    "nợ nhóm",
    "nợ xấu",
    "tài khóa",
    "tăng trưởng",
    "thị trường",
    "thương mại",
    "tín dụng",
    "tỷ giá",
    "vàng",
    "vĩ mô",
    "xuất khẩu",
]

NON_MACRO_KEYWORDS = [
    "athlete",
    "boxing",
    "breakup",
    "celebrity",
    "cruise ship",
    "football",
    "hantavirus",
    "lakers",
    "movie",
    "plane",
    "roland garros",
    "sports",
    "tennis",
    "ufc",
    "weedkiller",
    "đời sống",
    "nhà phố",
    "ngôi nhà",
    "sân cắm trại",
    "thể thao",
]


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    text = unescape(value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError):
        return clean_text(value)


def sortable_date(value: str | None) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)


def first_text(node: ElementTree.Element, names: list[str]) -> str:
    for name in names:
        found = node.find(name)
        if found is not None and found.text:
            return clean_text(found.text)

    # RSS feeds often include namespaces. Match by local tag name as fallback.
    for child in node:
        local_name = child.tag.rsplit("}", 1)[-1]
        if local_name in names and child.text:
            return clean_text(child.text)
    return ""


def first_link(node: ElementTree.Element) -> str:
    link = first_text(node, ["link"])
    if link:
        return link

    for child in node:
        local_name = child.tag.rsplit("}", 1)[-1]
        if local_name == "link":
            href = child.attrib.get("href", "")
            if href:
                return href.strip()
    return ""


def fetch_url(url: str, timeout: int = 20) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def parse_xml_root(xml_bytes: bytes) -> ElementTree.Element:
    try:
        return ElementTree.fromstring(xml_bytes)
    except ElementTree.ParseError:
        # Some feeds declare the wrong encoding or contain invalid control chars.
        text = xml_bytes.decode("utf-8-sig", errors="replace")
        text = re.sub(r"<\?xml[^>]*\?>", "", text, count=1).lstrip()
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
        text = re.sub(
            r"&(?!amp;|lt;|gt;|quot;|apos;|#[0-9]+;|#x[0-9a-fA-F]+;)",
            "&amp;",
            text,
        )
        return ElementTree.fromstring(text)


def load_sources(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    return payload.get("sources", [])


def parse_rss(xml_bytes: bytes, source: dict[str, str], limit: int) -> list[dict[str, Any]]:
    root = parse_xml_root(xml_bytes)
    items = root.findall(".//item")

    # Atom feeds use <entry> instead of <item>.
    if not items:
        items = [
            node for node in root.iter()
            if node.tag.rsplit("}", 1)[-1] == "entry"
        ]

    articles: list[dict[str, Any]] = []
    selected_items = items if limit <= 0 else items[:limit]
    for item in selected_items:
        title = first_text(item, ["title"])
        link = first_link(item)
        summary = first_text(item, ["description", "summary", "content"])
        published = first_text(item, ["pubDate", "published", "updated"])

        if not title or not link:
            continue

        articles.append(
            {
                "title": title,
                "url": link,
                "summary": summary,
                "published_at": parse_date(published),
                "source": source.get("name", "Unknown"),
                "category": source.get("category", "general"),
                "region": source.get("region", "unknown"),
            }
        )
    return articles


def dedupe_articles(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []

    for article in articles:
        key = article.get("url") or article.get("title", "").lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(article)
    return unique


def filter_articles_by_local_date(articles: list[dict[str, Any]], target_date: date) -> list[dict[str, Any]]:
    filtered = []
    for article in articles:
        published_at = article.get("published_at")
        if not published_at:
            continue
        parsed_date = sortable_date(published_at)
        if parsed_date == datetime.min.replace(tzinfo=timezone.utc):
            continue
        try:
            article_date = parsed_date.astimezone().date()
        except OSError:
            continue
        if article_date == target_date:
            filtered.append(article)
    return filtered


def macro_relevance_score(article: dict[str, Any]) -> int:
    category = str(article.get("category", "")).lower()
    title = str(article.get("title", ""))
    summary = str(article.get("summary", ""))
    source = str(article.get("source", ""))
    text = f"{title} {summary} {source}".lower()

    score = MACRO_CATEGORY_SCORES.get(category, 0)
    score += sum(1 for keyword in MACRO_KEYWORDS if keyword in text)
    score -= 2 * sum(1 for keyword in NON_MACRO_KEYWORDS if keyword in text)
    return score


def filter_macro_articles(articles: list[dict[str, Any]], min_score: int) -> list[dict[str, Any]]:
    filtered = []
    for article in articles:
        score = macro_relevance_score(article)
        if score >= min_score:
            article["macro_score"] = score
            filtered.append(article)
    return filtered


def sort_and_limit_articles(articles: list[dict[str, Any]], max_total: int | None) -> list[dict[str, Any]]:
    sorted_articles = sorted(
        articles,
        key=lambda article: sortable_date(article.get("published_at")),
        reverse=True,
    )
    if max_total and max_total > 0:
        return sorted_articles[:max_total]
    return sorted_articles


def crawl(sources: list[dict[str, str]], per_source_limit: int) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    all_articles: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for source in sources:
        name = source.get("name", "Unknown")
        url = source.get("url", "")
        if not url:
            continue

        try:
            xml_bytes = fetch_url(url)
            articles = parse_rss(xml_bytes, source, per_source_limit)
            all_articles.extend(articles)
            print(f"OK: {name} -> {len(articles)} articles")
        except (HTTPError, URLError, TimeoutError, ElementTree.ParseError) as error:
            errors.append({"source": name, "url": url, "error": str(error)})
            print(f"ERROR: {name} -> {error}", file=sys.stderr)

    return dedupe_articles(all_articles), errors


def write_output(path: Path, articles: list[dict[str, Any]], errors: list[dict[str, str]]) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(articles),
        "source_error_count": len(errors),
        "articles": articles,
        "errors": errors,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_content_json(path: Path, articles: list[dict[str, Any]]) -> None:
    items = []
    for article in articles[:10]:
        content_parts = []
        if article.get("summary"):
            content_parts.append(article["summary"])
        content_parts.append(f"Source: {article.get('source', 'Unknown')}")
        content_parts.append(f"URL: {article.get('url', '')}")

        items.append(
            {
                "title": article.get("title", "Untitled"),
                "content": "\n".join(content_parts),
            }
        )

    payload = {
        "chatSectionTitle": "Cập nhật tin tức hàng ngày",
        "chatItems": items,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Crawl public finance/crypto RSS feeds.")
    parser.add_argument("--sources", default=str(DEFAULT_SOURCES_FILE), help="Path to news_sources.json")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_FILE), help="Path to output JSON")
    parser.add_argument("--per-source-limit", type=int, default=0, help="Max items per source. Use 0 for no limit.")
    parser.add_argument("--max-total", type=int, default=0, help="Max unique items in final output. Use 0 for no limit.")
    parser.add_argument("--today-only", action="store_true", help="Only keep articles published today in local time.")
    parser.add_argument("--date", help="Only keep articles published on this local date, format YYYY-MM-DD.")
    parser.add_argument("--macro-only", action="store_true", help="Only keep macro/economic market-relevant articles.")
    parser.add_argument("--macro-min-score", type=int, default=3, help="Minimum relevance score for --macro-only.")
    parser.add_argument(
        "--update-content",
        action="store_true",
        help="Also update content.json for the local website fallback.",
    )
    args = parser.parse_args()

    sources = load_sources(Path(args.sources))
    articles, errors = crawl(sources, args.per_source_limit)

    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        articles = filter_articles_by_local_date(articles, target_date)
    elif args.today_only:
        target_date = datetime.now().astimezone().date()
        articles = filter_articles_by_local_date(articles, target_date)

    if args.macro_only:
        articles = filter_macro_articles(articles, args.macro_min_score)

    articles = sort_and_limit_articles(articles, args.max_total)
    write_output(Path(args.output), articles, errors)

    if args.update_content:
        if DEFAULT_FINAL_FILE.is_file() and DEFAULT_ENRICHED_FILE.is_file():
            from build_website_content import rebuild_content_json

            n = rebuild_content_json(
                DEFAULT_FINAL_FILE,
                DEFAULT_ENRICHED_FILE,
                DEFAULT_CONTENT_FILE,
                fetch_images=False,
                metadata_timeout=6,
            )
            print(f"Website content: {n} article cards -> {DEFAULT_CONTENT_FILE}")
        else:
            write_content_json(DEFAULT_CONTENT_FILE, articles)

    print(f"Done: {len(articles)} unique articles -> {args.output}")
    if errors:
        print(f"Warnings: {len(errors)} source(s) failed. See output JSON for details.")


if __name__ == "__main__":
    main()
