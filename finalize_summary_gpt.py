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

    return f"""
Bạn là biên tập viên cuối cùng cho LEON Quant Labs. Giọng văn cao cấp, súc tích,
theo phong cách ghi chép trong nhóm đầu tư chuyên sâu: ưu tiên luận điểm có thể
hành động, không khẩu hiệu, không mục lục, không đọc như bài PR.

Input gồm:
1. Bản tổng hợp từ Gemini (có thể có lệch so với nguồn).
2. Các đoạn bài gốc đã crawl (evidence_articles) — trích dẫn nội dung đã lưu tại thời điểm crawl.
3. live_web_snippets: đoạn trích TỪ WEB VỪA FETCH LẠI (tiêu đề trang + og:description hoặc đoạn text rút gọn).
   Dùng mục này để KIỂM CHỨNG nhanh: nếu snippet không chứa số liệu/claim mà Gemini đưa ra, hãy làm mềm hoặc bỏ claim,
   ghi trong web_verification. Không cần kiểm từng URL; chỉ cần đủ để xác nhật hoặc phát hiện lệch rõ rệt.

Nhiệm vụ:
- Tổng hợp từ Gemini + evidence; sau đó đối chiếu với live_web_snippets (khi có).
- Không bịa số liệu. Số liệu chỉ giữ nếu xuất hiện trong evidence_articles hoặc được live_web_snippets hỗ trợ;
  nếu không chắc, nói "chưa đủ dữ liệu xác nhận" thay vì suy diễn.
- Cấu trúc nội dung theo dòng suy luận đầu tư (trình bày liền mạch trên web, không cần heading mục lục máy móc):
  + macro_global: tin vĩ mô / sự kiện toàn cầu nổi bật HÔM NAY là gì (2–4 câu, cụ thể).
  + international_markets: truyền qua các thị trường quốc tế thế nào (lãi suất, USD, risk-on/off,
    chỉ số lớn, hàng hóa năng lượng/kim loại nếu liên quan) — 3–6 câu.
  + vietnam_implications: hàm ý cho Việt Nam — TTCK, hệ thống tài chính–ngân hàng,
    tỷ giá–vĩ mô, hàng hóa/dầu ảnh hưởng tới VN, dòng vốn — 4–7 câu, có thể gắn kênh truyền rõ ràng.
- executive_summary: 1–2 câu "one-liner" tổng kết cho người bận.
- key_points: 3–6 ý, mỗi ý 2–3 câu, luôn có sources là URL từ evidence (trùng với bài đã dùng).
- web_verification: tóm tắt 1–3 câu về việc kiểm chứng; checks liệt kê tối đa {len(live_page_snippets)} dòng
  (url, status: confirmed | partial | unavailable | mismatch, note ngắn).

Trả về DUY NHẤT JSON hợp lệ theo schema:
{{
  "title": "Macro Daily Brief",
  "macro_global": "2-4 câu",
  "international_markets": "3-6 câu",
  "vietnam_implications": "4-7 câu",
  "executive_summary": "1-2 câu one-liner",
  "market_impact": "Risk-on | Risk-off | Neutral | Mixed",
  "key_points": [
    {{
      "title": "Ý chính",
      "detail": "2-3 câu",
      "impact": "High | Medium | Low",
      "sources": ["URL"]
    }}
  ],
  "vietnam_watch": "Bản rút gọn 1 đoạn đồng bộ với vietnam_implications (1-3 câu) hoặc để trống nếu trùng hoàn toàn",
  "global_watch": "Bản rút gọn 1 đoạn đồng bộ với international_markets (1-3 câu) hoặc để trống",
  "risks_to_watch": ["Rủi ro 1", "Rủi ro 2"],
  "editor_notes": "Ghi chú chất lượng dữ liệu, giới hạn mô hình",
  "web_verification": {{
    "summary": "1-3 câu",
    "checks": [
      {{"url": "https://...", "status": "confirmed", "note": "ngắn"}}
    ]
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


def write_content_json(path: Path, summary: dict[str, Any]) -> None:
    lead = summary.get("executive_summary", "").strip()
    macro = summary.get("macro_global", "").strip()
    intl = summary.get("international_markets", "").strip()
    vn = summary.get("vietnam_implications", "").strip()
    narrative = "\n\n".join(
        part
        for part in (
            lead,
            f"Vĩ mô toàn cầu:\n{macro}" if macro else "",
            f"Kênh quốc tế:\n{intl}" if intl else "",
            f"Hàm ý Việt Nam:\n{vn}" if vn else "",
        )
        if part
    )

    cards = [
        {
            "title": summary.get("title", "Macro Daily Brief"),
            "content": (
                f"{narrative}\n\nMarket impact: {summary.get('market_impact', 'Mixed')}"
            ).strip(),
        }
    ]

    key_points = summary.get("key_points", [])
    if key_points:
        cards.append(
            {
                "title": "Điểm chính",
                "content": "\n\n".join(
                    f"- {item.get('title', 'Ý chính')}: {item.get('detail', '')} "
                    f"(Impact: {item.get('impact', 'N/A')})"
                    for item in key_points
                    if isinstance(item, dict)
                ),
            }
        )

    wv = summary.get("web_verification") if isinstance(summary.get("web_verification"), dict) else {}
    if wv.get("summary"):
        checks = wv.get("checks") or []
        check_lines = ""
        if isinstance(checks, list) and checks:
            lines = []
            for c in checks:
                if not isinstance(c, dict):
                    continue
                lines.append(f"  · {c.get('url', '')} [{c.get('status', '')}] {c.get('note', '')}")
            check_lines = "\n".join(lines)
        cards.append(
            {
                "title": "Kiểm chứng nhanh từ web",
                "content": "\n".join(p for p in (wv.get("summary", ""), check_lines) if p),
            }
        )

    if summary.get("vietnam_watch"):
        cards.append({"title": "Việt Nam watch", "content": summary["vietnam_watch"]})

    if summary.get("global_watch"):
        cards.append({"title": "Global watch", "content": summary["global_watch"]})

    risks = summary.get("risks_to_watch", [])
    if risks:
        cards.append({"title": "Rủi ro cần theo dõi", "content": "\n".join(f"- {risk}" for risk in risks)})

    if summary.get("editor_notes"):
        cards.append({"title": "Ghi chú dữ liệu", "content": summary["editor_notes"]})

    payload = {
        "chatSectionTitle": "Macro Daily Brief",
        "chatItems": cards,
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
    verify_urls = verification_urls_from_evidence(evidence, args.verify_urls_max)

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
        write_content_json(DEFAULT_CONTENT_FILE, summary)

    print(f"Done: final summary written to {args.output}")
    if args.update_content:
        print(f"Website content updated: {DEFAULT_CONTENT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
