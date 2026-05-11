import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


from build_website_content import rebuild_content_json


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_GEMINI_FILE = PROJECT_DIR / "gemini_summary.json"
DEFAULT_ENRICHED_FILE = PROJECT_DIR / "enriched_news.json"
DEFAULT_OUTPUT_FILE = PROJECT_DIR / "final_summary.json"
DEFAULT_CONTENT_FILE = PROJECT_DIR / "content.json"
DEFAULT_ENV_FILE = PROJECT_DIR / ".env"
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
VERIFY_USER_AGENT = "LEONQuantLabsWebVerify/0.1 (editorial pipeline; facts check)"


def strip_html_to_text(html: str, max_chars: int) -> str:
    text = unescape(re.sub(r"(?is)<script[^>]*>.*?</script>", " ", html))
    text = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def extract_title_from_html(html: str) -> str:
    match = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
    if not match:
        return ""
    return strip_html_to_text(match.group(1), 300)


def extract_og_description(html: str) -> str:
    match = re.search(
        r'(?is)<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
        html,
    ) or re.search(
        r'(?is)<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:description["\']',
        html,
    )
    if not match:
        match = re.search(
            r'(?is)<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
            html,
        )
    if not match:
        return ""
    return strip_html_to_text(match.group(1), 1200)


def fetch_live_page_snippet(url: str, timeout: int, max_body_chars: int) -> dict[str, str]:
    try:
        request = Request(url, headers={"User-Agent": VERIFY_USER_AGENT})
        with urlopen(request, timeout=timeout) as response:
            raw = response.read(220_000)
            charset = response.headers.get_content_charset() or "utf-8"
        html = raw.decode(charset, errors="replace")
        title_live = extract_title_from_html(html)
        og = extract_og_description(html)
        body = strip_html_to_text(html, max_body_chars)
        excerpt = og or body
        return {
            "url": url,
            "fetch_status": "ok",
            "title_live": title_live,
            "excerpt": excerpt,
        }
    except (HTTPError, URLError, TimeoutError, UnicodeError, ValueError) as error:
        return {
            "url": url,
            "fetch_status": f"error: {error}",
            "title_live": "",
            "excerpt": "",
        }


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


def article_lookup(enriched_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lookup = {}
    for article in enriched_payload.get("articles", []):
        url = str(article.get("url", ""))
        if url:
            lookup[url] = article
    return lookup


def compact_evidence(gemini_summary: dict[str, Any], enriched_payload: dict[str, Any], max_evidence_chars: int) -> list[dict[str, str]]:
    summary = gemini_summary.get("summary", {})
    lookup = article_lookup(enriched_payload)
    evidence_urls: list[str] = []

    for theme in summary.get("key_themes", []):
        if isinstance(theme, dict):
            evidence_urls.extend(str(url) for url in theme.get("source_urls", []) if url)

    for item in summary.get("important_articles", []):
        if isinstance(item, dict) and item.get("url"):
            evidence_urls.append(str(item["url"]))

    seen: set[str] = set()
    compacted = []
    for url in evidence_urls:
        if url in seen:
            continue
        seen.add(url)
        article = lookup.get(url)
        if not article:
            continue
        text = str(article.get("content_for_ai") or article.get("summary") or "")
        compacted.append(
            {
                "title": str(article.get("title", "")),
                "source": str(article.get("source", "")),
                "category": str(article.get("category", "")),
                "region": str(article.get("region", "")),
                "published_at": str(article.get("published_at", "")),
                "url": url,
                "evidence_text": text[:max_evidence_chars],
            }
        )
    return compacted


def verification_urls_from_evidence(evidence: list[dict[str, str]], max_urls: int) -> list[str]:
    seen: set[str] = set()
    urls: list[str] = []
    for row in evidence:
        url = str(row.get("url", ""))
        if not url or url in seen:
            continue
        seen.add(url)
        urls.append(url)
        if len(urls) >= max_urls:
            break
    return urls


def verification_urls_fill(
    enriched_payload: dict[str, Any],
    evidence: list[dict[str, str]],
    max_urls: int,
) -> list[str]:
    """Ưu tiên URL trong evidence (Gemini), sau đó lấy thêm từ toàn bộ crawl cho đủ slot kiểm chứng."""
    urls = verification_urls_from_evidence(evidence, max_urls)
    if len(urls) >= max_urls:
        return urls
    seen = set(urls)
    for article in enriched_payload.get("articles", []):
        u = str(article.get("url", ""))
        if not u or u in seen:
            continue
        seen.add(u)
        urls.append(u)
        if len(urls) >= max_urls:
            break
    return urls


def build_prompt(
    gemini_payload: dict[str, Any],
    enriched_payload: dict[str, Any],
    max_evidence_chars: int,
    live_page_snippets: list[dict[str, str]],
) -> str:
    gemini_summary = gemini_payload.get("summary", {})
    evidence = compact_evidence(gemini_payload, enriched_payload, max_evidence_chars)
    payload = {
        "gemini_summary": gemini_summary,
        "evidence_articles": evidence,
        "live_web_snippets": live_page_snippets,
    }

    checks_cap = len(live_page_snippets)
    return f"""
Bạn là biên tập cuối của LEON Quant Labs. Viết tiếng Việt súc tích, kiểu ghi chú cho nhà đầu tư bận rộn:
không khẩu hiệu, không mục lục, không tạo nhiều lớp "watch / góc bổ sung / ghi chú biên tập" — chỉ hai khối chữ chính.

Trên web: (1) vĩ mô thế giới, (2) vĩ mô Việt Nam; phía dưới là danh sách đầy đủ link bài crawl (hệ thống tự liệt kê). Không liệt kê URL trong bài trừ khi trích số liệu.

Input:
1. Bản Gemini (có thể lệch nguồn).
2. evidence_articles — trích crawl đã lưu.
3. live_web_snippets — đoạn fetch lại từ web. Dùng kiểm chỉnh claim; ghi ngắn trong web_verification.checks. Không cần kiểm hết URL.

Nhiệm vụ:
- Tổng hợp Gemini + evidence; đối chiếu live_web_snippets khi có.
- Không bịa số liệu; thiếu dữ liệu thì nói "chưa đủ dữ liệu xác nhận".
- CHỈ hai khối nội dung dài:
  + macro_world: Vĩ mô thế giới trong ngày + truyền sang thị trường quốc tế (USD, lãi suất, risk, hàng hóa) — một đoạn 4–8 câu, súc tích (không lan man).
  + vietnam_macro: Việt Nam — tác động từ thế giới và trong nước (TTCK, NH/tín dụng, tỷ giá, hàng hóa, dòng vốn) — 4–8 câu; nhắc lãi trong nước / SBV khi có căn cứ trong evidence.
- executive_summary: 0 hoặc 1 câu dẫn; có thể "".
- market_impact: Risk-on | Risk-off | Neutral | Mixed

"Tác động" (bắt buộc):
- so_what_chain: MỘT dòng chuỗi nhân quả kiểu "A → B → C" (ví dụ: dữ liệu/góc thế giới → DXY hoặc lợi suất → hệ quả lên Vàng / USD-VND / TTCK). Dùng mũi tên →, không bullet dài.
- asset_impacts: 4–6 mục, mỗi mục: asset (tên ngắn: Vàng, DXY/USD, TTCK VN, USD/VND, Lãi suất VN, Hàng hóa, v.v.), bias (bullish | bearish | neutral | mixed), note (một câu "vì sao" với ND).

Kết nối Việt Nam (bắt buộc):
- world_to_vietnam: đúng MỘT câu: tin/kênh thế giới trong ngày tác động trực tiếp thế nào lên VN (tỷ giá, thanh khoản NH, chính sách SBV hoặc lãi suất trong nước khi có trong evidence).

Trực quan — thực tế vs dự báo:
- actual_vs_forecast: tối đa 4 dòng, CHỈ khi evidence/live snippet có số cụ thể; mỗi dòng: indicator (tên chỉ báo), actual (số hoặc chuỗi ngắn), forecast (kỳ vọng), actual_pct và forecast_pct là hai số 0–100 để vẽ thanh so sánh (cùng thang: quy ước max của ngày = 100, hoặc hai giá trị tương đối trong cùng chỉ báo). Nếu không đủ số: trả mảng rỗng [].
- macro_heat_labels: tối đa 6 nhãn vi mô trong ngày (vd: US yields, Risk, Oil, VN liquidity,…), mỗi phần tử: label, sentiment (hot | warm | cool | ice) — để heatmap (hot=căng/nguy cơ tăng, warm=tích cực nhẹ, cool=trung tính/dị giảm, ice=trầm/xả).

- risks_to_watch: tối đa 3 mục rất ngắn; hoặc []
- web_verification: summary 1 câu (việc đã kiểm, không lặp bản chính); checks tối đa {checks_cap} mục (url, status: confirmed | partial | unavailable | mismatch, note ngắn).

KHÔNG trả về: key_points, vietnam_watch, global_watch, editor_notes, macro_global, international_markets, vietnam_implications như field riêng — chỉ macro_world và vietnam_macro.

Trả về DUY NHẤT JSON:
{{
  "title": "Macro Daily Brief",
  "executive_summary": "",
  "macro_world": "",
  "vietnam_macro": "",
  "so_what_chain": "",
  "asset_impacts": [],
  "world_to_vietnam": "",
  "actual_vs_forecast": [],
  "macro_heat_labels": [],
  "market_impact": "Mixed",
  "risks_to_watch": [],
  "web_verification": {{
    "summary": "",
    "checks": []
  }}
}}

Input JSON:
{json.dumps(payload, ensure_ascii=False)}
""".strip()


def call_openai(prompt: str, model: str, api_key: str, timeout: int = 120) -> dict[str, Any]:
    payload = {
        "model": model,
        "temperature": 0.15,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a strict JSON-only financial editor for Vietnamese macro briefs. "
                    "Do not invent facts. Use live_web_snippets and evidence to verify claims when possible."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    }

    request = Request(
        OPENAI_CHAT_COMPLETIONS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urlopen(request, timeout=timeout) as response:
        response_payload = json.loads(response.read().decode("utf-8"))

    content = response_payload["choices"][0]["message"]["content"]
    return json.loads(content)


def write_summary(path: Path, summary: dict[str, Any], meta: dict[str, Any]) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "meta": meta,
        "summary": summary,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Finalize Gemini summary with a low-cost OpenAI model.")
    parser.add_argument("--gemini-input", default=str(DEFAULT_GEMINI_FILE), help="Path to gemini_summary.json")
    parser.add_argument("--enriched-input", default=str(DEFAULT_ENRICHED_FILE), help="Path to enriched_news.json")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_FILE), help="Path to final_summary.json")
    parser.add_argument("--model", default=os.environ.get("OPENAI_FINAL_MODEL", os.environ.get("OPENAI_MODEL", "gpt-4o-mini")))
    parser.add_argument("--max-evidence-chars", type=int, default=1200, help="Max article evidence chars per source")
    parser.add_argument("--verify-urls-max", type=int, default=5, help="Max source URLs to live-fetch for verification")
    parser.add_argument("--web-verify-timeout", type=int, default=12, help="Seconds per URL live fetch")
    parser.add_argument("--web-verify-body-chars", type=int, default=2000, help="Max chars of stripped body per URL")
    parser.add_argument("--skip-web-verify", action="store_true", help="Do not fetch live pages (offline / faster)")
    parser.add_argument("--update-content", action="store_true", help="Update content.json for the website")
    parser.add_argument("--dry-run", action="store_true", help="Print prompt size only; do not call OpenAI")
    args = parser.parse_args()

    load_env_file(DEFAULT_ENV_FILE)
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not args.dry_run and not api_key:
        print("Missing OPENAI_API_KEY. Add it to .env or set environment variable.", file=sys.stderr)
        return 2

    gemini_payload = load_json(Path(args.gemini_input))
    enriched_payload = load_json(Path(args.enriched_input))
    evidence = compact_evidence(gemini_payload, enriched_payload, args.max_evidence_chars)
    verify_urls = verification_urls_fill(enriched_payload, evidence, args.verify_urls_max)

    live_snippets: list[dict[str, str]] = []
    if not args.skip_web_verify:
        for url in verify_urls:
            snippet = fetch_live_page_snippet(url, args.web_verify_timeout, args.web_verify_body_chars)
            live_snippets.append(
                {
                    "url": snippet["url"],
                    "fetch_status": snippet["fetch_status"],
                    "title_live": snippet.get("title_live", ""),
                    "excerpt": snippet.get("excerpt", ""),
                }
            )

    prompt = build_prompt(gemini_payload, enriched_payload, args.max_evidence_chars, live_snippets)

    print(f"Model: {args.model}")
    print(f"Prompt chars: {len(prompt)}")
    print(f"Evidence articles: {len(evidence)}")
    print(f"Live web checks: {len(live_snippets)} (skip={args.skip_web_verify})")

    if args.dry_run:
        return 0

    try:
        summary = call_openai(prompt, args.model, api_key)
    except (HTTPError, URLError, TimeoutError, KeyError, json.JSONDecodeError) as error:
        print(f"OpenAI API error: {error}", file=sys.stderr)
        return 1

    meta = {
        "gemini_input": str(Path(args.gemini_input).resolve()),
        "enriched_input": str(Path(args.enriched_input).resolve()),
        "model": args.model,
        "max_evidence_chars": args.max_evidence_chars,
        "verify_urls_max": args.verify_urls_max,
        "skip_web_verify": args.skip_web_verify,
        "live_fetch_urls": verify_urls,
        "live_fetch_status": [
            {"url": row["url"], "fetch_status": row["fetch_status"]} for row in live_snippets
        ],
    }
    write_summary(Path(args.output), summary, meta)

    if args.update_content:
        n = rebuild_content_json(
            Path(args.output),
            Path(args.enriched_input),
            DEFAULT_CONTENT_FILE,
            fetch_images=True,
            metadata_timeout=12,
        )
        print(f"Website content: {n} article cards -> {DEFAULT_CONTENT_FILE}")

    print(f"Done: final summary written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
