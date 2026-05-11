import argparse
import hashlib
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
CACHE_DIR = PROJECT_DIR / ".cache"
ARTICLE_CACHE_FILE = CACHE_DIR / "article_cache.json"
DEFAULT_GEMINI_FILE = PROJECT_DIR / "gemini_summary.json"
DEFAULT_ENRICHED_FILE = PROJECT_DIR / "enriched_news.json"
DEFAULT_OUTPUT_FILE = PROJECT_DIR / "final_summary.json"
DEFAULT_CONTENT_FILE = PROJECT_DIR / "content.json"
DEFAULT_ENV_FILE = PROJECT_DIR / ".env"
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
VERIFY_USER_AGENT = "LEONQuantLabsWebVerify/0.1 (editorial pipeline; facts check)"

MACRO_CATEGORY_KEYWORDS = (
    "economy",
    "finance",
    "macro",
    "commodities",
    "commodity",
    "banking",
    "stocks",
    "stock",
    "crypto",
    "market",
    "forex",
    "bond",
    "rate",
    "fed",
    "ecb",
    "oil",
    "gold",
    "vietnam",
    "global",
    "vi mo",
    "vi-mo",
    "tai chinh",
    "chung khoan",
    "ngan hang",
    "hang hoa",
    "forex",
    "currency",
    "vn-index",
    "commodities",
)

EXCLUDE_KEYWORDS = (
    "lifestyle",
    "giai tri",
    "sport",
    "bong da",
    "celebr",
    "lam dep",
    "thoi trang",
    "quiz",
    "horoscope",
)

DEFAULT_DISCLAIMER = (
    "Nội dung chỉ phục vụ mục đích nghiên cứu và giáo dục; không phải khuyến nghị đầu tư, "
    "không phải dịch vụ tư vấn tài chính. Thông tin có thể chưa đầy đủ hoặc đã lỗi thời."
)


def env_str(key: str, default: str) -> str:
    raw = os.environ.get(key)
    if raw is None or str(raw).strip() == "":
        return default
    return str(raw).strip()


def env_int(key: str, default: int) -> int:
    raw = os.environ.get(key)
    if raw is None or str(raw).strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def openai_model_default() -> str:
    return env_str("OPENAI_MODEL", env_str("OPENAI_FINAL_MODEL", "gpt-5.4-mini"))


OPENAI_TEMPERATURE = float(env_str("OPENAI_TEMPERATURE", "0.2") or "0.2")
OPENAI_MAX_OUTPUT_TOKENS = env_int("OPENAI_MAX_OUTPUT_TOKENS", 4500)
MAX_FINAL_ARTICLES = env_int("MAX_FINAL_ARTICLES", 18)
MAX_EVIDENCE_CHARS = env_int("MAX_EVIDENCE_CHARS", 1200)
MAX_LIVE_SNIPPETS = env_int("MAX_LIVE_SNIPPETS", 6)
MAX_REPAIR_RETRIES = env_int("MAX_REPAIR_RETRIES", 1)


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


def article_lookup_from_enriched(enriched_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for article in enriched_payload.get("articles", []):
        url = str(article.get("url", ""))
        if url:
            lookup[url] = article
    return lookup


def article_cache_key(url: str, published_at: str, title: str) -> str:
    base = f"{url}|{published_at}|{title}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def load_article_cache() -> dict[str, Any]:
    if not ARTICLE_CACHE_FILE.exists():
        return {}
    try:
        return json.loads(ARTICLE_CACHE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_article_cache(data: dict[str, Any]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    ARTICLE_CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def is_excluded_article(article: dict[str, Any]) -> bool:
    blob = f"{article.get('title', '')} {article.get('category', '')} {article.get('summary', '')}".lower()
    return any(k in blob for k in EXCLUDE_KEYWORDS)


def passes_macro_filter(article: dict[str, Any], *, from_important: bool) -> bool:
    if from_important:
        return True
    cat = str(article.get("category", "")).lower()
    reg = str(article.get("region", "")).lower()
    blob = f"{cat} {reg}"
    return any(k in blob for k in MACRO_CATEGORY_KEYWORDS)


def collect_ordered_urls(gemini_summary: dict[str, Any]) -> tuple[list[str], set[str]]:
    important_urls: list[str] = []
    for item in gemini_summary.get("important_articles", []):
        if isinstance(item, dict) and item.get("url"):
            important_urls.append(str(item["url"]))
    important_set = set(important_urls)
    theme_urls: list[str] = []
    for theme in gemini_summary.get("key_themes", []):
        if isinstance(theme, dict):
            for url in theme.get("source_urls", []):
                theme_urls.append(str(url))
    seen: set[str] = set()
    ordered: list[str] = []
    for url in important_urls + theme_urls:
        if url and url not in seen:
            seen.add(url)
            ordered.append(url)
    return ordered, important_set


def build_compacted_evidence(
    gemini_payload: dict[str, Any],
    enriched_payload: dict[str, Any],
    *,
    max_final_articles: int,
    max_evidence_chars: int,
) -> tuple[list[dict[str, str]], dict[str, int]]:
    gemini_summary = gemini_payload.get("summary", {})
    lookup = article_lookup_from_enriched(enriched_payload)
    ordered, important_set = collect_ordered_urls(gemini_summary)
    cache = load_article_cache()
    cache_dirty = False
    rows: list[dict[str, str]] = []

    for url in ordered:
        article = lookup.get(url)
        if not article:
            continue
        if is_excluded_article(article):
            continue
        from_imp = url in important_set
        if not passes_macro_filter(article, from_important=from_imp):
            continue

        title = str(article.get("title", ""))
        published_at = str(article.get("published_at", ""))
        key = article_cache_key(url, published_at, title)
        raw_text = str(article.get("content_for_ai") or article.get("summary") or "")

        cached = cache.get(key)
        if isinstance(cached, dict) and cached.get("evidence_text"):
            evidence_text = str(cached["evidence_text"])
        else:
            evidence_text = raw_text[:max_evidence_chars]
            cache[key] = {
                "evidence_text": evidence_text,
                "title": title,
                "url": url,
                "published_at": published_at,
            }
            cache_dirty = True

        rows.append(
            {
                "title": title,
                "source": str(article.get("source", "")),
                "region": str(article.get("region", "")),
                "category": str(article.get("category", "")),
                "published_at": published_at,
                "url": url,
                "evidence_text": evidence_text,
            }
        )
        if len(rows) >= max_final_articles:
            break

    if cache_dirty:
        save_article_cache(cache)

    stats = {
        "sources_scanned": len(enriched_payload.get("articles", [])),
        "articles_selected": len(rows),
    }
    return rows, stats


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
    evidence: list[dict[str, str]],
    live_page_snippets: list[dict[str, str]],
    *,
    brief_date: str,
) -> str:
    gemini_summary = gemini_payload.get("summary", {})
    payload = {
        "brief_date_hint": brief_date,
        "gemini_summary": gemini_summary,
        "evidence_articles": evidence,
        "live_web_snippets": live_page_snippets,
    }

    schema_hint = """Return a single JSON object with these keys exactly:
title, date, generated_at, market_regime, daily_thesis, thirty_second_summary, what_changed,
top_macro_drivers, asset_impact_heatmap, vietnam_investor_lens, scenario_map,
key_variables_to_watch, source_quality, final_takeaway, disclaimer.

market_regime: regime, primary_driver, secondary_driver, risk_tone, confidence, invalidation (all strings).

top_macro_drivers: 3 to 5 items; each has headline, fact, why_it_matters, transmission_chain (array of short strings),
assets_affected (array of strings), time_horizon (string), confidence {fact, impact each High|Medium|Low},
what_could_prove_this_wrong (string).

asset_impact_heatmap: at least 6 rows; each has asset, direction Bullish|Bearish|Neutral|Mixed,
strength High|Medium|Low, horizon Intraday|1-5 days|1-2 weeks|1-3 months, main_reason, watch_risk.

vietnam_investor_lens: summary, channels array of {channel, analysis}.

scenario_map: base_case, bull_case, bear_case each probability (integer 0-100), description, signals_to_watch (array).
Probabilities must sum to 100.

key_variables_to_watch: array of {variable, why_it_matters}.

source_quality: sources_scanned, articles_selected, verified_links (integers), coverage_note (string).

Use Vietnamese prose in string fields. JSON only, no markdown, no URLs inside analytical text."""

    editorial = """
You are the final editor of LEON Quant Labs, an AI-powered macro research desk for Vietnamese investors.

Your job is NOT to summarize random news.
Your job is to produce one coherent daily macro intelligence note.

Core principle:
Every daily brief must identify ONE dominant daily macro thesis.
All selected stories must support, challenge, or qualify that thesis.
Do not produce a list of unrelated news.

Audience:
Serious Vietnamese investors, traders, analysts, and experienced market readers.
They do not want generic news.
They want market regime, causality, transmission channels, Vietnam relevance, scenarios, confidence, invalidation, and what to watch next.

Writing style:
- Vietnamese.
- Concise but analytical.
- Professional desk-note style.
- No hype.
- No financial advice.
- Separate facts from inference.
- Never invent numbers.
- Never invent sources.
- If evidence is weak, say confidence is Medium or Low.
- Always explain “So What”.
- Always include “What could prove this wrong”.
- Prefer 3 to 5 macro drivers only.
- Avoid unrelated local news unless it affects Vietnam macro, VN-Index, banking, FX, foreign flows, inflation, policy, liquidity, or major sectors.

Required thinking:
1. Identify the dominant macro thesis first.
2. Identify current market regime.
3. Explain what changed versus market expectations.
4. Select only the most important macro drivers.
5. For each driver, explain: Fact; Why it matters; Transmission chain; Assets affected; Time horizon; Confidence; What could prove this wrong.
6. Translate global macro into Vietnam investor lens (USD/VND, foreign flows, rates, VN-Index, sectors, breadth, liquidity).
7. Create base/bull/bear scenarios. Probabilities must sum to 100.
8. Create key variables to watch.
9. Return JSON only. No markdown. No commentary outside JSON.

Important anti-hallucination rules:
- Use only evidence from input JSON and live snippets.
- If a number is not in evidence, do not create it.
- If two sources conflict, say “dữ liệu chưa đồng nhất” and lower confidence.
- Do not include raw URLs inside the article text.
- Source quality must honestly describe coverage limitations.
""".strip()

    return f"""{editorial}

{schema_hint}

Use honest integers in source_quality when possible; pipeline will overwrite sources_scanned, articles_selected, verified_links with measured counts. Still provide a truthful coverage_note.

Input JSON:
{json.dumps(payload, ensure_ascii=False)}
""".strip()


def call_openai(
    prompt: str,
    *,
    model: str,
    api_key: str,
    temperature: float,
    max_output_tokens: int,
    timeout: int = 120,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_output_tokens,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a strict JSON-only macro research editor for Vietnamese investors. "
                    "Do not invent facts or numbers. Obey the user's schema exactly."
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


def repair_json_with_gpt(
    bad_json_text: str,
    errors: list[str],
    *,
    model: str,
    api_key: str,
    temperature: float,
    max_output_tokens: int,
) -> dict[str, Any]:
    err_blob = "; ".join(errors)
    prompt = f"""The following JSON failed validation.
Errors: {err_blob}

Fix the JSON to satisfy the LEON Quant Daily Macro Intelligence schema (all required keys, 3-5 drivers, heatmap >=6 rows, scenario probabilities sum 100, non-empty strings where required). Return ONLY fixed JSON, no markdown.

Broken JSON:
{bad_json_text[:100_000]}
""".strip()
    return call_openai(
        prompt,
        model=model,
        api_key=api_key,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        timeout=90,
    )


def validate_final_summary(data: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []

    def need_str(key: str, path: str) -> None:
        v = data.get(key)
        if not isinstance(v, str) or not str(v).strip():
            errors.append(f"missing_or_empty:{path}")

    need_str("daily_thesis", "daily_thesis")
    need_str("thirty_second_summary", "thirty_second_summary")
    need_str("what_changed", "what_changed")
    need_str("final_takeaway", "final_takeaway")
    need_str("disclaimer", "disclaimer")

    mr = data.get("market_regime")
    if not isinstance(mr, dict):
        errors.append("market_regime:not_object")
    else:
        for k in ("regime", "primary_driver", "risk_tone", "confidence", "invalidation"):
            if not str(mr.get(k, "")).strip():
                errors.append(f"market_regime.{k}:empty")

    drivers = data.get("top_macro_drivers")
    if not isinstance(drivers, list) or not (3 <= len(drivers) <= 5):
        errors.append("top_macro_drivers:need_3_to_5")
    else:
        for i, d in enumerate(drivers):
            if not isinstance(d, dict):
                errors.append(f"top_macro_drivers[{i}]:not_object")
                continue
            for k in ("headline", "fact", "why_it_matters", "what_could_prove_this_wrong"):
                if not str(d.get(k, "")).strip():
                    errors.append(f"driver[{i}].{k}:empty")
            tc = d.get("transmission_chain")
            if not isinstance(tc, list) or len(tc) < 1:
                errors.append(f"driver[{i}].transmission_chain:need_list")
            conf = d.get("confidence")
            if not isinstance(conf, dict):
                errors.append(f"driver[{i}].confidence:not_object")
            else:
                for ck in ("fact", "impact"):
                    val = str(conf.get(ck, "")).strip()
                    if val not in ("High", "Medium", "Low"):
                        errors.append(f"driver[{i}].confidence.{ck}:invalid")

    heat = data.get("asset_impact_heatmap")
    if not isinstance(heat, list) or len(heat) < 6:
        errors.append("asset_impact_heatmap:need_at_least_6")
    else:
        allowed_dir = {"Bullish", "Bearish", "Neutral", "Mixed"}
        allowed_strength = {"High", "Medium", "Low"}
        allowed_horizon = {"Intraday", "1-5 days", "1-2 weeks", "1-3 months"}
        for i, row in enumerate(heat):
            if not isinstance(row, dict):
                errors.append(f"heatmap[{i}]:not_object")
                continue
            if str(row.get("direction", "")).strip() not in allowed_dir:
                errors.append(f"heatmap[{i}].direction:invalid")
            if str(row.get("strength", "")).strip() not in allowed_strength:
                errors.append(f"heatmap[{i}].strength:invalid")
            if str(row.get("horizon", "")).strip() not in allowed_horizon:
                errors.append(f"heatmap[{i}].horizon:invalid")

    vil = data.get("vietnam_investor_lens")
    if not isinstance(vil, dict):
        errors.append("vietnam_investor_lens:not_object")
    else:
        if not str(vil.get("summary", "")).strip():
            errors.append("vietnam_investor_lens.summary:empty")
        ch = vil.get("channels")
        if not isinstance(ch, list) or len(ch) < 1:
            errors.append("vietnam_investor_lens.channels:need_list")
        else:
            for i, c in enumerate(ch):
                if not isinstance(c, dict) or not str(c.get("channel", "")).strip():
                    errors.append(f"vil.channels[{i}]:bad")
                if not str(c.get("analysis", "")).strip():
                    errors.append(f"vil.channels[{i}].analysis:empty")

    sm = data.get("scenario_map")
    if not isinstance(sm, dict):
        errors.append("scenario_map:not_object")
    else:
        for case in ("base_case", "bull_case", "bear_case"):
            if case not in sm or not isinstance(sm[case], dict):
                errors.append(f"scenario_map.{case}:missing")
        if isinstance(sm, dict) and all(k in sm for k in ("base_case", "bull_case", "bear_case")):
            try:
                pb = float(sm["base_case"].get("probability", -1))
                pu = float(sm["bull_case"].get("probability", -1))
                pe = float(sm["bear_case"].get("probability", -1))
                if abs((pb + pu + pe) - 100.0) > 0.51:
                    errors.append("scenario_map.probabilities:not_100")
            except (TypeError, KeyError):
                errors.append("scenario_map.probabilities:invalid")

    kvw = data.get("key_variables_to_watch")
    if not isinstance(kvw, list) or len(kvw) < 1:
        errors.append("key_variables_to_watch:need_list")

    sq = data.get("source_quality")
    if not isinstance(sq, dict):
        errors.append("source_quality:not_object")

    return (len(errors) == 0, errors)


def merge_pipeline_metadata(
    summary: dict[str, Any],
    *,
    generated_at_iso: str,
    brief_date: str,
    sources_scanned: int,
    articles_selected: int,
    verified_links: int,
    coverage_note_extra: str = "",
) -> None:
    summary["title"] = summary.get("title") or "LEON Quant Labs — Daily Macro Intelligence"
    summary["date"] = summary.get("date") or brief_date
    summary["generated_at"] = summary.get("generated_at") or generated_at_iso
    sq = summary.get("source_quality")
    if not isinstance(sq, dict):
        sq = {}
    sq["sources_scanned"] = sources_scanned
    sq["articles_selected"] = articles_selected
    sq["verified_links"] = verified_links
    note = str(sq.get("coverage_note", "") or "").strip()
    if coverage_note_extra:
        note = f"{note} {coverage_note_extra}".strip() if note else coverage_note_extra
    sq["coverage_note"] = note
    summary["source_quality"] = sq
    if not str(summary.get("disclaimer", "")).strip():
        summary["disclaimer"] = DEFAULT_DISCLAIMER


def build_fallback_summary(
    gemini_payload: dict[str, Any],
    *,
    enriched_count: int,
    evidence_count: int,
    verified_links: int,
    generated_at_iso: str,
    brief_date: str,
) -> dict[str, Any]:
    gs = gemini_payload.get("summary", {})
    thesis = (
        str(gs.get("executive_summary", "")).strip()
        or str(gs.get("title", "")).strip()
        or "Tóm tắt tạm từ bước Gemini; cần chạy lại bước GPT khi API khả dụng."
    )
    themes = [t for t in gs.get("key_themes", []) if isinstance(t, dict)][:5]
    drivers: list[dict[str, Any]] = []
    for t in themes:
        if len(drivers) >= 5:
            break
        th = str(t.get("theme", "Chủ đề vĩ mô")).strip()
        fact = str(t.get("summary", "")).strip() or "Không có tóm tắt chi tiết trong đầu vào."
        drivers.append(
            {
                "headline": th,
                "fact": fact[:1200],
                "why_it_matters": "Luồng này được Gemini đánh dấu quan trọng; cần đối chiếu thêm nguồn gốc trước khi giao dịch.",
                "transmission_chain": ["Tin → Kỳ vọng → Giá tài sản → Kênh truyền vào VN"],
                "assets_affected": ["Đa dạng theo chủ đề"],
                "time_horizon": "1-5 days",
                "confidence": {"fact": "Medium", "impact": "Medium"},
                "what_could_prove_this_wrong": "Số liệu mới hoặc tuyên bố chính sách khác với kịch bản hiện tại.",
            }
        )
    while len(drivers) < 3:
        drivers.append(
            {
                "headline": "Thông tin bổ sung từ pipeline",
                "fact": "Pipeline không đủ mục sau lọc nguồn; đây là dòng dự phòng.",
                "why_it_matters": "Giữ khung đọc nhất quán trong ngày.",
                "transmission_chain": ["Thiếu dữ liệu → Độ tin cậy thấp hơn → Thận trọng vị thế"],
                "assets_affected": ["Thận trọng chung"],
                "time_horizon": "1-5 days",
                "confidence": {"fact": "Low", "impact": "Low"},
                "what_could_prove_this_wrong": "Khi có thêm bài macro đã lọc.",
            }
        )

    heat_assets = [
        ("USD / DXY", "Mixed", "Medium", "1-5 days"),
        ("Vàng", "Mixed", "Medium", "1-5 days"),
        ("Dầu / năng lượng", "Mixed", "Medium", "1-5 days"),
        ("Lợi suất thực", "Bearish", "Medium", "1-2 weeks"),
        ("VN-Index", "Mixed", "Medium", "1-5 days"),
        ("USD/VND", "Mixed", "Medium", "1-5 days"),
        ("Trái phiếu Hoa Kỳ", "Mixed", "Low", "1-2 weeks"),
        ("TTCK mới nổi", "Mixed", "Medium", "1-2 weeks"),
    ]
    heat = [
        {
            "asset": a,
            "direction": d,
            "strength": s,
            "horizon": h,
            "main_reason": "Ước lượng từ tóm tắt Gemini — không phải khuyến nghị.",
            "watch_risk": "Xác minh lại bằng nguồn Tier-1 khi có thể.",
        }
        for a, d, s, h in heat_assets[:8]
    ]

    gwatch = str(gs.get("global_watch", "") or "").strip()
    vwatch = str(gs.get("vietnam_watch", "") or "").strip()

    return {
        "title": "LEON Quant Labs — Daily Macro Intelligence",
        "date": brief_date,
        "generated_at": generated_at_iso,
        "market_regime": {
            "regime": "Mixed / cần xác nhận lại",
            "primary_driver": "Dữ liệu từ Gemini (fallback)",
            "secondary_driver": "",
            "risk_tone": "Thận trọng",
            "confidence": "Low",
            "invalidation": "Khi bước GPT khôi phục và schema hợp lệ.",
        },
        "daily_thesis": thesis[:2000],
        "thirty_second_summary": thesis[:1200],
        "what_changed": "Không tạo được bản GPT hợp lệ; diễn biến được rút từ lớp Gemini và nguồn đã lọc.",
        "top_macro_drivers": drivers[:5],
        "asset_impact_heatmap": heat,
        "vietnam_investor_lens": {
            "summary": vwatch or "Xem kênh chi tiết bên dưới — dữ liệu fallback.",
            "channels": [
                {"channel": "VN-Index", "analysis": vwatch or "Theo dõi dòng tiền nội bộ."},
                {"channel": "USD/VND", "analysis": "Biến động USD toàn cầu có thể tác động qua kỳ vọng tỷ giá."},
                {"channel": "Khối ngoại", "analysis": "Theo dõi khớp lệnh và room ngoại khi thị trường biến động."},
                {"channel": "Lãi suất", "analysis": "Spread chính sách có thể ảnh hưởng chi phí vốn."},
                {"channel": "Độ rộng thị trường", "analysis": "Ưu tiên tin có đề cập thanh khoản/phân hóa nếu có."},
                {"channel": "Thanh khoản", "analysis": "Quan sát phiên khi tin lớn từ thế giới."},
            ],
        },
        "scenario_map": {
            "base_case": {
                "probability": 55,
                "description": "Thị trường giữ trạng thái mixed; ưu tiên quản trị rủi ro.",
                "signals_to_watch": ["Tin Fed", "Dầu", "USD/VND"],
            },
            "bull_case": {
                "probability": 25,
                "description": "Rủi ro địa chính trị hạ nhiệt, lạm phát nguội — risk-on trở lại.",
                "signals_to_watch": ["Đàm phán", "PMI"],
            },
            "bear_case": {
                "probability": 20,
                "description": "Dầu và lãi suất đồng thời tạo shock — risk-off sâu hơn.",
                "signals_to_watch": ["PPI/CPI", "Biên Hormuz"],
            },
        },
        "key_variables_to_watch": [
            {"variable": "Giá dầu", "why_it_matters": "Kênh lạm phát và tâm lý risk-off."},
            {"variable": "Phát ngôn Fed", "why_it_matters": "Định hình kỳ vọng lãi suất thực."},
            {"variable": "USD/VND", "why_it_matters": "Kênh trực tiếp cho nhà đầu tư Việt Nam."},
        ],
        "source_quality": {
            "sources_scanned": enriched_count,
            "articles_selected": evidence_count,
            "verified_links": verified_links,
            "coverage_note": "Fallback mode: final GPT output failed validation.",
        },
        "final_takeaway": gwatch[:800] or "Ưu tiên xác minh dữ liệu; đây là bản fallback từ Gemini.",
        "disclaimer": DEFAULT_DISCLAIMER,
        "macro_world": str(gs.get("macro_world", "") or gwatch),
        "vietnam_macro": str(gs.get("vietnam_macro", "") or vwatch),
        "world_to_vietnam": str(gs.get("world_to_vietnam", "") or ""),
        "market_impact": str(gs.get("market_impact", "Mixed") or "Mixed"),
    }


def write_summary(path: Path, summary: dict[str, Any], meta: dict[str, Any]) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "meta": meta,
        "summary": summary,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Finalize Gemini summary — Macro Intelligence JSON (OpenAI).")
    parser.add_argument("--gemini-input", default=str(DEFAULT_GEMINI_FILE))
    parser.add_argument("--enriched-input", default=str(DEFAULT_ENRICHED_FILE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_FILE))
    parser.add_argument("--model", default="")
    parser.add_argument("--max-evidence-chars", type=int, default=0, help="0 = use MAX_EVIDENCE_CHARS env/default")
    parser.add_argument("--max-final-articles", type=int, default=0, help="0 = use MAX_FINAL_ARTICLES env/default")
    parser.add_argument("--web-verify-timeout", type=int, default=12)
    parser.add_argument("--web-verify-body-chars", type=int, default=2000)
    parser.add_argument("--skip-web-verify", action="store_true")
    parser.add_argument("--update-content", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_env_file(DEFAULT_ENV_FILE)
    api_key = os.environ.get("OPENAI_API_KEY", "")
    model = args.model.strip() or openai_model_default()
    max_evidence = args.max_evidence_chars or MAX_EVIDENCE_CHARS
    max_final = args.max_final_articles or MAX_FINAL_ARTICLES

    if not args.dry_run and not api_key:
        print("Missing OPENAI_API_KEY. Add it to .env or set environment variable.", file=sys.stderr)
        return 2

    gemini_payload = load_json(Path(args.gemini_input))
    enriched_payload = load_json(Path(args.enriched_input))
    evidence, ev_stats = build_compacted_evidence(
        gemini_payload,
        enriched_payload,
        max_final_articles=max_final,
        max_evidence_chars=max_evidence,
    )
    verify_urls = verification_urls_from_evidence(evidence, MAX_LIVE_SNIPPETS)

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

    gen_at = datetime.now(timezone.utc)
    brief_date = gen_at.strftime("%Y-%m-%d")
    gs_time = gemini_payload.get("generated_at")
    if isinstance(gs_time, str) and len(gs_time) >= 10:
        brief_date = gs_time[:10]

    verified_ok = sum(1 for s in live_snippets if str(s.get("fetch_status", "")).startswith("ok"))
    prompt = build_prompt(gemini_payload, evidence, live_snippets, brief_date=brief_date)

    print(f"Model: {model}")
    print(f"Prompt chars: {len(prompt)}")
    print(f"Evidence articles (after filter): {len(evidence)}")
    print(f"Live web checks: {len(live_snippets)} (skip={args.skip_web_verify})")

    if args.dry_run:
        return 0

    meta = {
        "gemini_input": str(Path(args.gemini_input).resolve()),
        "enriched_input": str(Path(args.enriched_input).resolve()),
        "model": model,
        "max_evidence_chars": max_evidence,
        "max_final_articles": max_final,
        "max_live_snippets": MAX_LIVE_SNIPPETS,
        "skip_web_verify": args.skip_web_verify,
        "live_fetch_urls": verify_urls,
        "live_fetch_status": [{"url": row["url"], "fetch_status": row["fetch_status"]} for row in live_snippets],
        "openai_temperature": OPENAI_TEMPERATURE,
        "openai_max_output_tokens": OPENAI_MAX_OUTPUT_TOKENS,
    }

    summary: dict[str, Any] | None = None
    used_fallback = False

    try:
        summary = call_openai(
            prompt,
            model=model,
            api_key=api_key,
            temperature=OPENAI_TEMPERATURE,
            max_output_tokens=OPENAI_MAX_OUTPUT_TOKENS,
        )
        if not isinstance(summary, dict):
            summary = None
    except (HTTPError, URLError, TimeoutError, KeyError, json.JSONDecodeError) as error:
        print(f"OpenAI API error: {error}", file=sys.stderr)
        summary = None

    if summary is not None:
        merge_pipeline_metadata(
            summary,
            generated_at_iso=gen_at.isoformat(),
            brief_date=brief_date,
            sources_scanned=ev_stats["sources_scanned"],
            articles_selected=ev_stats["articles_selected"],
            verified_links=verified_ok,
        )
        ok, errs = validate_final_summary(summary)
        if not ok:
            print("Validation failed:", errs, file=sys.stderr)
            bad_text = json.dumps(summary, ensure_ascii=False)
            for attempt in range(MAX_REPAIR_RETRIES + 1):
                if attempt >= MAX_REPAIR_RETRIES:
                    break
                try:
                    summary = repair_json_with_gpt(
                        bad_text,
                        errs,
                        model=model,
                        api_key=api_key,
                        temperature=OPENAI_TEMPERATURE,
                        max_output_tokens=min(OPENAI_MAX_OUTPUT_TOKENS, 8192),
                    )
                    if not isinstance(summary, dict):
                        bad_text = "{}"
                        continue
                    merge_pipeline_metadata(
                        summary,
                        generated_at_iso=gen_at.isoformat(),
                        brief_date=brief_date,
                        sources_scanned=ev_stats["sources_scanned"],
                        articles_selected=ev_stats["articles_selected"],
                        verified_links=verified_ok,
                    )
                    ok, errs = validate_final_summary(summary)
                    if ok:
                        print("Repaired JSON passed validation.")
                        break
                    bad_text = json.dumps(summary, ensure_ascii=False)
                except (HTTPError, URLError, TimeoutError, KeyError, json.JSONDecodeError) as re:
                    print(f"Repair attempt failed: {re}", file=sys.stderr)
            if not ok:
                summary = build_fallback_summary(
                    gemini_payload,
                    enriched_count=ev_stats["sources_scanned"],
                    evidence_count=len(evidence),
                    verified_links=verified_ok,
                    generated_at_iso=gen_at.isoformat(),
                    brief_date=brief_date,
                )
                merge_pipeline_metadata(
                    summary,
                    generated_at_iso=gen_at.isoformat(),
                    brief_date=brief_date,
                    sources_scanned=ev_stats["sources_scanned"],
                    articles_selected=ev_stats["articles_selected"],
                    verified_links=verified_ok,
                    coverage_note_extra="Fallback mode: final GPT output failed validation.",
                )
                used_fallback = True
    else:
        summary = build_fallback_summary(
            gemini_payload,
            enriched_count=ev_stats["sources_scanned"],
            evidence_count=len(evidence),
            verified_links=verified_ok,
            generated_at_iso=gen_at.isoformat(),
            brief_date=brief_date,
        )
        merge_pipeline_metadata(
            summary,
            generated_at_iso=gen_at.isoformat(),
            brief_date=brief_date,
            sources_scanned=ev_stats["sources_scanned"],
            articles_selected=ev_stats["articles_selected"],
            verified_links=verified_ok,
            coverage_note_extra="Fallback mode: OpenAI request failed.",
        )
        used_fallback = True

    meta["used_fallback"] = used_fallback
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

    print(f"Done: final summary written to {args.output} (fallback={used_fallback})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
