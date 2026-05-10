import argparse
import json
import os
import sys
from datetime import datetime, timezone
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


def build_prompt(gemini_payload: dict[str, Any], enriched_payload: dict[str, Any], max_evidence_chars: int) -> str:
    gemini_summary = gemini_payload.get("summary", {})
    evidence = compact_evidence(gemini_payload, enriched_payload, max_evidence_chars)
    payload = {
        "gemini_summary": gemini_summary,
        "evidence_articles": evidence,
    }

    return f"""
Bạn là final editor/judge cho bản tin macro của LEON Quant Labs.

Input gồm:
1. Bản tổng hợp từ Gemini.
2. Một số bài gốc đã crawl làm evidence.

Nhiệm vụ:
- Kiểm tra bản Gemini, loại bỏ hoặc làm mềm các claim không đủ evidence.
- Viết lại thành bản final tiếng Việt, rõ ràng, ngắn gọn, có giá trị đầu tư.
- Không bịa số liệu. Chỉ dùng dữ liệu có trong input.
- Nếu thiếu dữ liệu, ghi rõ "chưa đủ dữ liệu" thay vì suy diễn.
- Ưu tiên insight liên quan: vĩ mô, ngân hàng, bất động sản, vàng/hàng hóa, dòng vốn, chứng khoán, rủi ro chính sách.
- Không cần dài. Bản final dùng cho website.

Trả về DUY NHẤT JSON hợp lệ theo schema:
{{
  "title": "Macro Daily Brief",
  "executive_summary": "5-7 câu tổng quan cuối cùng",
  "market_impact": "Risk-on | Risk-off | Neutral | Mixed",
  "key_points": [
    {{
      "title": "Ý chính",
      "detail": "2-3 câu",
      "impact": "High | Medium | Low",
      "sources": ["URL"]
    }}
  ],
  "vietnam_watch": "Nhận định Việt Nam",
  "global_watch": "Nhận định quốc tế",
  "risks_to_watch": ["Rủi ro 1", "Rủi ro 2"],
  "editor_notes": "Ghi chú chất lượng dữ liệu và điểm cần kiểm chứng"
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
                "content": "You are a strict JSON-only financial editor. Do not invent facts.",
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
    cards = [
        {
            "title": summary.get("title", "Macro Daily Brief"),
            "content": (
                f"{summary.get('executive_summary', '')}\n\n"
                f"Market impact: {summary.get('market_impact', 'Mixed')}"
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
    prompt = build_prompt(gemini_payload, enriched_payload, args.max_evidence_chars)

    print(f"Model: {args.model}")
    print(f"Prompt chars: {len(prompt)}")
    print(f"Evidence articles: {len(compact_evidence(gemini_payload, enriched_payload, args.max_evidence_chars))}")

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
