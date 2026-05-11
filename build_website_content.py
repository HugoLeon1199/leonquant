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
DEFAULT_MARKET_SNAPSHOT_FILE = PROJECT_DIR / "market_snapshot.json"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 LEONQuantLabs/1.0"
)


class MetadataExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.image_url = ""
        self.description = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key.lower(): value or "" for key, value in attrs}

        if tag == "meta":
            prop = attr_map.get("property", "").lower()
            name = attr_map.get("name", "").lower()
            content = attr_map.get("content", "")
            if not content:
                return

            if prop in {"og:image", "og:image:url", "twitter:image"} and not self.image_url:
                self.image_url = content.strip()
            elif name in {"twitter:image", "twitter:image:src"} and not self.image_url:
                self.image_url = content.strip()
            elif (
                prop in {"og:description", "twitter:description"}
                or name
                in {
                    "description",
                    "twitter:description",
                }
            ) and not self.description:
                self.description = clean_text(content)
            return

        if tag == "link":
            rel = attr_map.get("rel", "").lower()
            href = attr_map.get("href", "")
            if rel == "image_src" and href and not self.image_url:
                self.image_url = href.strip()


def load_market_snapshot_json(path: Path | None = None) -> dict[str, Any]:
    """Đọc market_snapshot.json; không raise. Trả về skeleton nếu thiếu/lỗi."""
    p = path or DEFAULT_MARKET_SNAPSHOT_FILE
    if not p.exists():
        return {
            "generated_at": "",
            "assets": [],
            "coverage_note": "Chưa có market_snapshot.json — chạy fetch_market_snapshot.py trước bước GPT.",
        }
    try:
        data = load_json(p)
        if not isinstance(data, dict):
            raise ValueError("not an object")
        data.setdefault("generated_at", "")
        data.setdefault("assets", [])
        if not isinstance(data.get("assets"), list):
            data["assets"] = []
        data.setdefault("coverage_note", "")
        return data
    except (json.JSONDecodeError, OSError, ValueError):
        return {
            "generated_at": "",
            "assets": [],
            "coverage_note": "Không đọc được market_snapshot.json (JSON lỗi hoặc file hỏng).",
        }


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


def _heatmap_rows_from_new(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in summary.get("asset_impact_heatmap", []) or []:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "group": row.get("asset", "—"),
                "impact_today": f"{row.get('direction', '')} · {row.get('strength', '')}".strip(" ·"),
                "main_reason": str(row.get("main_reason", "") or ""),
            }
        )
    return rows


def _has_macro_intelligence_schema(summary: dict[str, Any]) -> bool:
    """Schema mới (Daily Macro Intelligence): có ít nhất một khối chính."""
    mr = summary.get("market_regime") if isinstance(summary.get("market_regime"), dict) else {}
    if mr and (
        str(mr.get("regime", "")).strip()
        or str(mr.get("primary_driver", "")).strip()
    ):
        return True
    if str(summary.get("daily_thesis", "") or "").strip():
        return True
    if str(summary.get("what_changed", "") or "").strip():
        return True
    tmd = summary.get("top_macro_drivers")
    if isinstance(tmd, list) and len(tmd) > 0:
        return True
    heat = summary.get("asset_impact_heatmap")
    if isinstance(heat, list) and len(heat) > 0:
        return True
    vil = summary.get("vietnam_investor_lens") if isinstance(summary.get("vietnam_investor_lens"), dict) else {}
    ch = vil.get("channels") if isinstance(vil.get("channels"), list) else []
    if vil and (str(vil.get("summary", "")).strip() or len(ch) > 0):
        return True
    sm = summary.get("scenario_map") if isinstance(summary.get("scenario_map"), dict) else {}
    if sm and all(k in sm for k in ("base_case", "bull_case", "bear_case")):
        return True
    kvw = summary.get("key_variables_to_watch")
    if isinstance(kvw, list) and len(kvw) > 0:
        return True
    if str(summary.get("final_takeaway", "") or "").strip():
        return True
    return False


def build_payload(
    final_payload: dict[str, Any],
    enriched_payload: dict[str, Any],
    all_articles: list[dict[str, Any]],
    *,
    market_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = final_payload.get("summary", {})
    generated_at = (
        str(summary.get("generated_at", "")).strip()
        or final_payload.get("generated_at")
        or datetime.now(timezone.utc).isoformat()
    )
    t303 = str(summary.get("thirty_second_summary", "") or "").strip()
    exec_lead = str(summary.get("executive_summary", "") or "").strip()
    if not t303 and exec_lead:
        t303 = exec_lead
    web_ver = summary.get("web_verification") if isinstance(summary.get("web_verification"), dict) else {}
    risks = summary.get("risks_to_watch", [])

    def _list(key: str) -> list[Any]:
        v = summary.get(key)
        return v if isinstance(v, list) else []

    asset_impacts = _list("asset_impacts")
    actual_vs = _list("actual_vs_forecast")
    heat_labels = _list("macro_heat_labels")
    brief_stories = _list("brief_stories")
    asset_impact_table = _list("asset_impact_table")

    new_intel = _has_macro_intelligence_schema(summary)
    if new_intel:
        brief_stories = []
        asset_impact_table = []
        mw = ""
        vm = ""
        narrative_fallback = ""
    else:
        mw = _macro_world(summary)
        vm = _vietnam_macro(summary)
        narrative_fallback = "\n\n".join(p for p in (mw, vm) if p).strip()
    daily_thesis = str(summary.get("daily_thesis", "") or "").strip()
    what_changed = str(summary.get("what_changed", "") or "").strip()
    final_take = str(summary.get("final_takeaway", "") or "").strip()
    disclaimer = str(summary.get("disclaimer", "") or "").strip()

    market_regime = summary.get("market_regime") if isinstance(summary.get("market_regime"), dict) else {}
    top_macro_drivers = summary.get("top_macro_drivers") if isinstance(summary.get("top_macro_drivers"), list) else []
    asset_impact_heatmap = (
        summary.get("asset_impact_heatmap") if isinstance(summary.get("asset_impact_heatmap"), list) else []
    )
    vietnam_lens = (
        summary.get("vietnam_investor_lens") if isinstance(summary.get("vietnam_investor_lens"), dict) else {}
    )
    scenario_map = summary.get("scenario_map") if isinstance(summary.get("scenario_map"), dict) else {}
    key_vars = (
        summary.get("key_variables_to_watch") if isinstance(summary.get("key_variables_to_watch"), list) else []
    )
    source_quality = summary.get("source_quality") if isinstance(summary.get("source_quality"), dict) else {}
    brief_date = str(summary.get("date", "") or "").strip()

    chat_title = summary.get("title", "LEON Quant Labs — Daily Macro Intelligence")
    if not new_intel and asset_impact_heatmap and not asset_impact_table:
        asset_impact_table = _heatmap_rows_from_new(summary)

    mr_for_impact = market_regime if isinstance(market_regime, dict) else {}
    regime_line = str(mr_for_impact.get("regime", "") or "").strip()
    market_impact_val = regime_line or str(summary.get("market_impact", "") or "").strip() or "Mixed"

    ms_payload = market_snapshot if market_snapshot is not None else load_market_snapshot_json()

    return {
        "siteTitle": "LEON Quant Labs",
        "sectionLabel": "Daily Macro Intelligence for Serious Investors",
        "title": chat_title,
        "date": brief_date,
        "generatedAt": generated_at,
        "briefDate": brief_date,
        "chatSectionTitle": chat_title,
        "marketImpact": market_impact_val,
        "executiveSummary": exec_lead,
        "thirtySecondSummary": t303,
        "briefStories": brief_stories,
        "assetImpactTable": asset_impact_table,
        "macroWorld": mw,
        "vietnamMacro": vm,
        "macroGlobal": summary.get("macro_global", ""),
        "internationalMarkets": summary.get("international_markets", ""),
        "vietnamImplications": summary.get("vietnam_implications", ""),
        "soWhatChain": str(summary.get("so_what_chain", "") or "").strip(),
        "worldToVietnam": str(summary.get("world_to_vietnam", "") or "").strip(),
        "assetImpacts": asset_impacts,
        "actualVsForecast": actual_vs,
        "macroHeatLabels": heat_labels,
        "webVerification": web_ver,
        "risksToWatch": risks if isinstance(risks, list) else [],
        "marketRegime": market_regime,
        "dailyThesis": daily_thesis,
        "whatChanged": what_changed,
        "topMacroDrivers": top_macro_drivers,
        "assetImpactHeatmap": asset_impact_heatmap,
        "vietnamInvestorLens": vietnam_lens,
        "scenarioMap": scenario_map,
        "keyVariablesToWatch": key_vars,
        "sourceQuality": source_quality,
        "marketSnapshot": ms_payload,
        "finalTakeaway": final_take,
        "disclaimer": disclaimer,
        "schemaVersion": "macro-intelligence-v1",
        "legacyProBrief": False,
        "allArticles": all_articles,
        "featuredArticles": all_articles,
        "stats": {
            "articlesCrawled": len(all_articles),
            "articlesInEnriched": enriched_payload.get("count", len(enriched_payload.get("articles", []))),
            "pipeline": "Crawl → Market snapshot → Gemini → GPT (Macro Intelligence) → content.json",
        },
        "chatItems": [
            {
                "title": chat_title,
                "content": (
                    "\n\n".join(
                        p
                        for p in (
                            daily_thesis or t303,
                            what_changed,
                            final_take,
                            f"Market regime: {regime_line}" if regime_line else "",
                        )
                        if str(p).strip()
                    ).strip()
                    or narrative_fallback
                ),
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
        default=10,
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
    payload = build_payload(
        final_payload,
        enriched_payload,
        all_cards,
        market_snapshot=load_market_snapshot_json(),
    )
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
    market_snapshot_path: Path | None = None,
) -> int:
    """Dựng đủ payload website (macro + toàn bộ bài enriched) từ final_summary hoặc gemini_summary."""
    final_payload = load_json(final_payload_path)
    enriched_payload = load_json(enriched_path)
    all_cards = build_all_article_cards(
        enriched_payload,
        fetch_images,
        metadata_timeout,
    )
    ms = load_market_snapshot_json(market_snapshot_path)
    payload = build_payload(final_payload, enriched_payload, all_cards, market_snapshot=ms)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(all_cards)


if __name__ == "__main__":
    raise SystemExit(main())
