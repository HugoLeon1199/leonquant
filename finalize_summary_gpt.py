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

from build_website_content import _default_strategy_snake, load_market_snapshot_json, rebuild_content_json


PROJECT_DIR = Path(__file__).resolve().parent
CACHE_DIR = PROJECT_DIR / ".cache"
ARTICLE_CACHE_FILE = CACHE_DIR / "article_cache.json"
DEFAULT_GEMINI_FILE = PROJECT_DIR / "gemini_summary.json"
DEFAULT_ENRICHED_FILE = PROJECT_DIR / "enriched_news.json"
DEFAULT_OUTPUT_FILE = PROJECT_DIR / "final_summary.json"
DEFAULT_CONTENT_FILE = PROJECT_DIR / "content.json"
DEFAULT_MARKET_SNAPSHOT_FILE = PROJECT_DIR / "market_snapshot.json"
DEFAULT_ENV_FILE = PROJECT_DIR / ".env"
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
VERIFY_USER_AGENT = "LEONQuantLabsWebVerify/0.1 (editorial reference fetch; facts check)"

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

# Schema snake_case: Global Market Strategy Brief v2 (build_website_content sẽ migrate/sanitize trước khi ra content.json).
STRATEGY_BRIEF_SUMMARY_KEYS = frozenset(
    {
        "title",
        "date",
        "generated_at",
        "publication_intro",
        "main_thesis",
        "what_changed",
        "market_regime_score",
        "global_macro_drivers",
        "intermarket_map",
        "transmission_chains",
        "quick_actions",
        "allocation_guide",
        "priority_and_avoid",
        "increase_risk_signals",
        "reduce_risk_signals",
        "intraday_playbook",
        "scenario_plan",
        "view_change_triggers",
        "final_decision",
    }
)

# Alias tương thích import cũ
MACRO_INTELLIGENCE_SUMMARY_KEYS = STRATEGY_BRIEF_SUMMARY_KEYS

SCHEMA_JSON_EXAMPLE = """{
  "title": "LEON Quant Labs — Global Market Strategy Brief",
  "date": "YYYY-MM-DD",
  "generated_at": "ISO-8601",
  "publication_intro": { "headline": "", "description": "" },
  "main_thesis": { "regime": "", "thesis": "", "action_conclusion": "" },
  "what_changed": [ { "variable": "", "change": "", "meaning": "" } ],
  "market_regime_score": {
    "total_score": 0,
    "regime": "",
    "items": [ { "axis": "", "signal": "", "score": 0 } ],
    "interpretation": ""
  },
  "global_macro_drivers": [
    { "title": "", "analysis": "", "market_impact": "" }
  ],
  "intermarket_map": [ { "asset": "", "state": "", "action": "" } ],
  "transmission_chains": [ "…" ],
  "quick_actions": [ { "investor_state": "", "action": "" } ],
  "allocation_guide": [
    {
      "profile": "",
      "stocks": "",
      "cash": "",
      "gold_defense": "",
      "crypto_high_risk": "",
      "leverage": ""
    }
  ],
  "priority_and_avoid": {
    "prioritize": [ { "asset": "", "reason": "" } ],
    "avoid_or_be_careful": [ { "asset": "", "reason": "" } ]
  },
  "increase_risk_signals": [ { "signal": "", "meaning": "" } ],
  "reduce_risk_signals": [ { "signal": "", "action": "" } ],
  "intraday_playbook": [ { "market_condition": "", "action": "" } ],
  "scenario_plan": {
    "base_case": { "title": "Kịch bản cơ sở", "description": "", "action": "" },
    "bull_case": { "title": "Kịch bản tích cực", "description": "", "action": "" },
    "bear_case": { "title": "Kịch bản tiêu cực", "description": "", "action": "" }
  },
  "view_change_triggers": {
    "more_positive_if": [ "" ],
    "more_negative_if": [ "" ]
  },
  "final_decision": ""
}"""


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
    market_snapshot: dict[str, Any],
    *,
    brief_date: str,
) -> str:
    gemini_summary = gemini_payload.get("summary", {})
    payload_for_model = {
        "market_snapshot": market_snapshot,
        "editorial_inputs": {
            "themes_and_notes": gemini_summary,
            "reference_articles": evidence,
            "reference_page_excerpts": live_page_snippets,
        },
    }

    schema_hint = f"""Return ONE JSON object. Keys MUST be EXACTLY this set and no others:
title, date, generated_at, publication_intro, main_thesis, what_changed, market_regime_score,
global_macro_drivers, intermarket_map, transmission_chains, quick_actions, allocation_guide,
priority_and_avoid, increase_risk_signals, reduce_risk_signals, intraday_playbook,
scenario_plan, view_change_triggers, final_decision.

Do NOT output: vietnam_transmission, sector_priority, final_takeaway, source_quality, disclaimer,
market_regime, daily_thesis, asset_impact_heatmap, vietnam_investor_lens, scenario_map,
top_macro_drivers, or any keys not listed above.

Shape:
{SCHEMA_JSON_EXAMPLE}

Counts / rules:
- Thinking chain: Market → Regime → Transmission → Allocation → Action → Trigger. Content changes daily from inputs; do not quote fixed regimes or numbers without market_snapshot support.
- what_changed: 4 to 6 items (variable / change / meaning). Use qualitative wording if precise deltas are missing.
- market_regime_score: 5–6 axes; each item score must be -1, 0, or +1. total_score must be consistent with regime label per rubric (>=3 risk-on; 1–2 selective positive; 0 neutral; -1 to -2 cautious selective; <=-3 defensive).
- global_macro_drivers: 3 or 4 items — GLOBAL only (Fed/US rates/yields, USD/DXY/FX, oil/inflation, China/trade/demand, geopolitics as it affects oil/USD/inflation/risk appetite). Use market_impact (cross-market transmission, not purely domestic Vietnam headlines). No Vietnam-only infra, single domestic bank story, or local project as a “global” driver.
- intermarket_map: cover US equities, Vietnam equities, EM, gold, oil, bonds/yields, crypto, cash — each row asset/state/action.
- transmission_chains: 3–5 causal strings (not disconnected headlines).
- quick_actions: exactly 6 items; investor_state MUST be exactly (verbatim):
  "Cầm nhiều tiền mặt", "Đang nắm tài sản khỏe", "Đang lãi ngắn hạn", "Đang dùng margin / đòn bẩy",
  "Muốn mua mới", "Đang kẹt tài sản yếu".
  Actions must be specific and not copy-pasted across rows.
- allocation_guide: exactly 4 profiles "Thận trọng", "Cân bằng", "Chủ động", "Rủi ro cao" with stocks, cash, gold_defense, crypto_high_risk, leverage.
  Thận trọng: thấp cổ phiếu, cao tiền mặt, vàng phòng thủ vừa phải, crypto tối thiểu, KHÔNG đòn bẩy cao.
  Never assign aggressive leverage to Thận trọng / Cân bằng.
- priority_and_avoid: 5–6 prioritize rows and 5–6 avoid_or_be_careful rows (asset + reason), adapted to evidence.
- increase_risk_signals: 5 or 6 items — ONLY positive confirmation (rates cooling, USD softer, stable oil, better breadth/liquidity, leaders holding, lighter foreign selling). NO risk-off shocks here.
- reduce_risk_signals: 5 or 6 items — ONLY warnings (USD spike, yields jumping, oil shock, narrow breadth rally, liquidity deterioration, leaders rolling over, speculative blow-off, heavy foreign selling).
- intraday_playbook: 5–7 rows tied to price action (liquidity, breadth), not headline emotion.
- view_change_triggers: lists of strings (>=4 each) for what would make the stance more positive vs more negative.
- final_decision: one concise closing stance (portfolio language; no direct "buy gold/oil/crypto").

MARKET DATA (strict):
- `market_snapshot` is the ONLY source for specific prices or percentage changes.
- If price/change missing or status not ok, describe qualitatively only. Never invent numbers.

LANGUAGE: Vietnamese only in all string fields. JSON only, no markdown, no URLs in analytical text."""

    editorial = """
You are the final editor of LEON Quant Labs, a serious Vietnamese investment research publication.

Your job is NOT to summarize news.
Your job is to turn daily global macro and market information into a concise, actionable Global Market Strategy Brief.

The structure is fixed, but the content must change every day based strictly on the evidence provided (market_snapshot, enriched articles, editorial notes, live excerpts when present).

Core chain you must reflect in writing:
Market → Regime → Transmission → Allocation → Action → Trigger.

The brief must help readers:
- understand the market regime
- identify what changed today
- understand global macro drivers
- connect global macro to assets
- decide portfolio stance
- know what to prioritize or avoid
- know when to increase risk
- know when to reduce risk
- know the base / bull / bear scenarios

PUBLIC OUTPUT RULES (JSON strings are shown to readers):
- Do NOT mention artificial intelligence, automation, web crawling, “GPT”, “Gemini”, internal tooling, training data,
  “models”, “pipelines”, “source quality”, “verified links”, “disclaimer”, or “đây không phải khuyến nghị đầu tư”.
- Write as a human investment research desk would: calm, precise, professional Vietnamese.

Writing rules:
- Short but meaningful. No hype. No chatbot tone. No generic news digest.
- Every section must connect to investor action.
- Prefer causal chains over isolated headlines; prefer portfolio stance over direct buy/sell calls.
- Do not say “mua vàng”, “mua dầu”, “mua crypto”, or imperative commodity trades.
- Prefer: ưu tiên, theo dõi, giữ tỷ trọng, tăng từng phần, giảm rủi ro, hạn chế đòn bẩy.

Risk lists:
- increase_risk_signals: confirmations only; never place negative macro shocks here.
- reduce_risk_signals: warnings only; never place “USD yếu / lợi suất hạ nhiệt / mua ròng” style positives here.

Scenarios (scenario_plan.*.action): portfolio stance language — equity weight, cash buffer, leverage discipline, concentration — never direct commodity instructions.

If evidence is weak or uneven, state it cautiously. Do not fabricate yesterday’s exact levels.
""".strip()

    return f"""{editorial}

{schema_hint}

Input JSON (for you only; do not repeat tool or production jargon in output strings):
{json.dumps(payload_for_model, ensure_ascii=False)}
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
                    "You output only valid JSON for the LEON Quant Labs Global Market Strategy Brief (v2). "
                    "Never include keys outside the user schema. "
                    "Never mention AI, automation, web crawling, GPT, Gemini, models, pipelines, or internal tooling in any "
                    "reader-facing string. "
                    "Use market_snapshot from the user message as the ONLY source for specific price figures or percentages. "
                    "Obey the user schema exactly."
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

Return ONLY valid JSON. The root object MUST contain EXACTLY these keys and no others:
title, date, generated_at, publication_intro, main_thesis, what_changed, market_regime_score,
global_macro_drivers, intermarket_map, transmission_chains, quick_actions, allocation_guide,
priority_and_avoid, increase_risk_signals, reduce_risk_signals, intraday_playbook,
scenario_plan, view_change_triggers, final_decision.

Remove legacy keys such as vietnam_transmission, sector_priority, final_takeaway, market_regime, daily_thesis,
source_quality, disclaimer, top_macro_drivers, asset_impact_heatmap, vietnam_investor_lens, scenario_map,
key_variables_to_watch, or any other fields not in the list above.

Schema shape:
{SCHEMA_JSON_EXAMPLE}

Do not mention AI, automation, GPT, Gemini, crawling, models, pipelines, or internal tooling in strings for readers.
Use market_snapshot rules from the original prompt: never invent prices.

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
    """Validate `summary` object inside final_summary.json (Global Market Strategy Brief v2)."""
    errors: list[str] = []

    if not isinstance(data, dict):
        return False, ["summary must be an object"]

    for key in STRATEGY_BRIEF_SUMMARY_KEYS:
        if key not in data:
            errors.append(f"missing:{key}")

    pub = data.get("publication_intro")
    if not isinstance(pub, dict):
        errors.append("publication_intro:not_object")
    else:
        for f in ("headline", "description"):
            if not str(pub.get(f, "")).strip():
                errors.append(f"publication_intro.{f}:empty")

    mt = data.get("main_thesis")
    if not isinstance(mt, dict):
        errors.append("main_thesis:not_object")
    else:
        for f in ("regime", "thesis", "action_conclusion"):
            if not str(mt.get(f, "")).strip():
                errors.append(f"main_thesis.{f}:empty")

    def _obj_list(key: str, min_n: int, fields: tuple[str, ...]) -> None:
        items = data.get(key)
        if not isinstance(items, list):
            errors.append(f"{key}:not_list")
            return
        if len(items) < min_n:
            errors.append(f"{key}:need_at_least_{min_n}")
        for i, row in enumerate(items):
            if not isinstance(row, dict):
                errors.append(f"{key}[{i}]:not_object")
                continue
            for f in fields:
                if not str(row.get(f, "")).strip():
                    errors.append(f"{key}[{i}].{f}:empty")

    _obj_list("what_changed", 4, ("variable", "change", "meaning"))

    mrs = data.get("market_regime_score")
    if not isinstance(mrs, dict):
        errors.append("market_regime_score:not_object")
    else:
        items = mrs.get("items")
        if not isinstance(items, list) or len(items) < 4:
            errors.append("market_regime_score.items:need_at_least_4")
        else:
            for i, it in enumerate(items):
                if not isinstance(it, dict):
                    errors.append(f"market_regime_score.items[{i}]:not_object")
                    continue
                for f in ("axis", "signal"):
                    if not str(it.get(f, "")).strip():
                        errors.append(f"market_regime_score.items[{i}].{f}:empty")
                sc = it.get("score", 0)
                try:
                    si = int(sc)
                except (TypeError, ValueError):
                    errors.append(f"market_regime_score.items[{i}].score:bad")
                    continue
                if si not in (-1, 0, 1):
                    errors.append(f"market_regime_score.items[{i}].score:not_in_-1_0_1")
        if not str(mrs.get("regime", "")).strip():
            errors.append("market_regime_score.regime:empty")
        if not str(mrs.get("interpretation", "")).strip():
            errors.append("market_regime_score.interpretation:empty")

    gmd = data.get("global_macro_drivers")
    if not isinstance(gmd, list):
        errors.append("global_macro_drivers:not_list")
    elif len(gmd) < 3:
        errors.append("global_macro_drivers:need_at_least_3")
    else:
        for i, row in enumerate(gmd):
            if not isinstance(row, dict):
                errors.append(f"global_macro_drivers[{i}]:not_object")
                continue
            for f in ("title", "analysis"):
                if not str(row.get(f, "")).strip():
                    errors.append(f"global_macro_drivers[{i}].{f}:empty")
            impact = str(row.get("market_impact", "") or row.get("vietnam_impact", "") or "").strip()
            if not impact:
                errors.append(f"global_macro_drivers[{i}].market_impact:empty")

    im = data.get("intermarket_map")
    if not isinstance(im, list):
        errors.append("intermarket_map:not_list")
    elif len(im) < 6:
        errors.append("intermarket_map:need_at_least_6")
    else:
        for i, row in enumerate(im):
            if not isinstance(row, dict):
                errors.append(f"intermarket_map[{i}]:not_object")
                continue
            for f in ("asset", "state", "action"):
                if not str(row.get(f, "")).strip():
                    errors.append(f"intermarket_map[{i}].{f}:empty")

    tc = data.get("transmission_chains")
    if not isinstance(tc, list):
        errors.append("transmission_chains:not_list")
    elif len([x for x in tc if isinstance(x, str) and x.strip()]) < 3:
        errors.append("transmission_chains:need_at_least_3_strings")
    else:
        for i, c in enumerate(tc):
            if not isinstance(c, str) or not c.strip():
                errors.append(f"transmission_chains[{i}]:empty")

    canonical_states = (
        "Cầm nhiều tiền mặt",
        "Đang nắm tài sản khỏe",
        "Đang lãi ngắn hạn",
        "Đang dùng margin / đòn bẩy",
        "Muốn mua mới",
        "Đang kẹt tài sản yếu",
    )
    qa = data.get("quick_actions")
    if not isinstance(qa, list):
        errors.append("quick_actions:not_list")
    elif len(qa) != 6:
        errors.append(f"quick_actions:must_be_exactly_6_items_got_{len(qa)}")
    else:
        seen_states: set[str] = set()
        for i, row in enumerate(qa):
            if not isinstance(row, dict):
                errors.append(f"quick_actions[{i}]:not_object")
                continue
            st = str(row.get("investor_state", "") or "").strip()
            act = str(row.get("action", "") or "").strip()
            if not act:
                errors.append(f"quick_actions[{i}].action:empty")
            if st not in canonical_states:
                errors.append(f"quick_actions[{i}].investor_state:not_canonical:{st!r}")
            elif st.lower() in seen_states:
                errors.append(f"quick_actions:duplicate_state:{st!r}")
            else:
                seen_states.add(st.lower())
        if len(seen_states) != 6:
            errors.append("quick_actions:need_exactly_6_distinct_canonical_states")

    ag = data.get("allocation_guide")
    if not isinstance(ag, list):
        errors.append("allocation_guide:not_list")
    elif len(ag) < 4:
        errors.append("allocation_guide:need_at_least_4")
    else:
        for i, row in enumerate(ag):
            if not isinstance(row, dict):
                errors.append(f"allocation_guide[{i}]:not_object")
                continue
            for f in ("profile", "stocks", "cash"):
                if not str(row.get(f, "") or "").strip():
                    errors.append(f"allocation_guide[{i}].{f}:empty")
            lev = str(row.get("leverage", "") or row.get("margin", "") or "").strip()
            if not lev:
                errors.append(f"allocation_guide[{i}].leverage:empty")
            if not str(row.get("gold_defense", "") or "").strip():
                errors.append(f"allocation_guide[{i}].gold_defense:empty")
            if not str(row.get("crypto_high_risk", "") or "").strip():
                errors.append(f"allocation_guide[{i}].crypto_high_risk:empty")

    pa = data.get("priority_and_avoid")
    if not isinstance(pa, dict):
        errors.append("priority_and_avoid:not_object")
    else:
        pr = pa.get("prioritize")
        av = pa.get("avoid_or_be_careful")
        if not isinstance(pr, list) or len(pr) < 5:
            errors.append("priority_and_avoid.prioritize:need_at_least_5")
        if not isinstance(av, list) or len(av) < 5:
            errors.append("priority_and_avoid.avoid_or_be_careful:need_at_least_5")
        if isinstance(pr, list):
            for i, row in enumerate(pr):
                if not isinstance(row, dict):
                    errors.append(f"priority_and_avoid.prioritize[{i}]:not_object")
                    continue
                if not str(row.get("asset", "") or "").strip() or not str(row.get("reason", "") or "").strip():
                    errors.append(f"priority_and_avoid.prioritize[{i}]:incomplete")
        if isinstance(av, list):
            for i, row in enumerate(av):
                if not isinstance(row, dict):
                    errors.append(f"priority_and_avoid.avoid_or_be_careful[{i}]:not_object")
                    continue
                if not str(row.get("asset", "") or "").strip() or not str(row.get("reason", "") or "").strip():
                    errors.append(f"priority_and_avoid.avoid_or_be_careful[{i}]:incomplete")

    _obj_list("increase_risk_signals", 4, ("signal", "meaning"))
    _obj_list("reduce_risk_signals", 4, ("signal", "action"))

    _obj_list("intraday_playbook", 4, ("market_condition", "action"))

    vct = data.get("view_change_triggers")
    if not isinstance(vct, dict):
        errors.append("view_change_triggers:not_object")
    else:
        mp = vct.get("more_positive_if")
        mn = vct.get("more_negative_if")
        if not isinstance(mp, list) or len([x for x in mp if isinstance(x, str) and x.strip()]) < 4:
            errors.append("view_change_triggers.more_positive_if:need_at_least_4")
        if not isinstance(mn, list) or len([x for x in mn if isinstance(x, str) and x.strip()]) < 4:
            errors.append("view_change_triggers.more_negative_if:need_at_least_4")

    sp = data.get("scenario_plan")
    if not isinstance(sp, dict):
        errors.append("scenario_plan:not_object")
    else:
        for case in ("base_case", "bull_case", "bear_case"):
            sc = sp.get(case)
            if not isinstance(sc, dict):
                errors.append(f"scenario_plan.{case}:not_object")
            else:
                for f in ("title", "description", "action"):
                    if not str(sc.get(f, "")).strip():
                        errors.append(f"scenario_plan.{case}.{f}:empty")

    if not str(data.get("final_decision", "")).strip():
        errors.append("final_decision:empty")

    forbidden_public = (
        "source_quality",
        "disclaimer",
        "vietnam_transmission",
        "sector_priority",
        "final_takeaway",
        "market_regime",
        "daily_thesis",
        "asset_impact_heatmap",
    )
    for fk in forbidden_public:
        if fk in data:
            errors.append(f"forbidden_public_field:{fk}")

    qa2 = data.get("quick_actions")
    if isinstance(qa2, list) and len(qa2) >= 4:
        act_texts = [
            str(r.get("action", "") or "").strip()
            for r in qa2
            if isinstance(r, dict) and str(r.get("action", "") or "").strip()
        ]
        if len(set(act_texts)) <= 2 and len(act_texts) >= 4:
            errors.append("quick_actions:actions_too_repetitive")

    return (len(errors) == 0, errors)


def merge_strategy_summary_defaults(
    summary: dict[str, Any],
    *,
    generated_at_iso: str,
    brief_date: str,
) -> None:
    summary["title"] = summary.get("title") or "LEON Quant Labs — Global Market Strategy Brief"
    summary["date"] = summary.get("date") or brief_date
    summary["generated_at"] = summary.get("generated_at") or generated_at_iso
    for leak in ("source_quality", "disclaimer", "web_verification", "market_regime"):
        summary.pop(leak, None)


def build_fallback_summary(
    gemini_payload: dict[str, Any],
    *,
    enriched_count: int,
    evidence_count: int,
    verified_links: int,
    generated_at_iso: str,
    brief_date: str,
) -> dict[str, Any]:
    del enriched_count, evidence_count, verified_links
    base = _default_strategy_snake(brief_date=brief_date, generated_at=generated_at_iso)
    gs = gemini_payload.get("summary", {}) if isinstance(gemini_payload.get("summary"), dict) else {}
    extra_ctx = (
        str(gs.get("executive_summary", "")).strip()
        or str(gs.get("global_watch", "")).strip()
        or str(gs.get("title", "")).strip()
    )
    if extra_ctx:
        mt = base["main_thesis"]
        mt["thesis"] = (str(mt.get("thesis", "") or "").strip() + " Bối cảnh tin tức hiện có: " + extra_ctx[:900]).strip()
    return base


def strip_summary_to_macro_schema(summary: dict[str, Any]) -> None:
    """Giữ đúng schema Global Market Strategy Brief v2; xoá mọi key không thuộc summary."""
    for k in list(summary.keys()):
        if k not in MACRO_INTELLIGENCE_SUMMARY_KEYS:
            summary.pop(k, None)


def write_summary(path: Path, summary: dict[str, Any], meta: dict[str, Any]) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "meta": meta,
        "summary": summary,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Finalize editorial pass — Global Market Strategy Brief v2 JSON (OpenAI).",
    )
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
    parser.add_argument(
        "--market-snapshot-input",
        default=str(DEFAULT_MARKET_SNAPSHOT_FILE),
        help="Path to market_snapshot.json (from fetch_market_snapshot.py)",
    )
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
    market_snap = load_market_snapshot_json(Path(args.market_snapshot_input))
    prompt = build_prompt(
        gemini_payload,
        evidence,
        live_snippets,
        market_snap,
        brief_date=brief_date,
    )

    print(f"Model: {model}")
    print(f"Prompt chars: {len(prompt)}")
    print(f"Evidence articles (after filter): {len(evidence)}")
    print(f"Live web checks: {len(live_snippets)} (skip={args.skip_web_verify})")

    if args.dry_run:
        return 0

    meta = {
        "gemini_input": str(Path(args.gemini_input).resolve()),
        "enriched_input": str(Path(args.enriched_input).resolve()),
        "market_snapshot_input": str(Path(args.market_snapshot_input).resolve()),
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
        merge_strategy_summary_defaults(
            summary,
            generated_at_iso=gen_at.isoformat(),
            brief_date=brief_date,
        )
        strip_summary_to_macro_schema(summary)
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
                    merge_strategy_summary_defaults(
                        summary,
                        generated_at_iso=gen_at.isoformat(),
                        brief_date=brief_date,
                    )
                    strip_summary_to_macro_schema(summary)
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
                merge_strategy_summary_defaults(
                    summary,
                    generated_at_iso=gen_at.isoformat(),
                    brief_date=brief_date,
                )
                strip_summary_to_macro_schema(summary)
                used_fallback = True
                meta["fallback_reason"] = "Fallback: final editorial output failed validation."
    else:
        summary = build_fallback_summary(
            gemini_payload,
            enriched_count=ev_stats["sources_scanned"],
            evidence_count=len(evidence),
            verified_links=verified_ok,
            generated_at_iso=gen_at.isoformat(),
            brief_date=brief_date,
        )
        merge_strategy_summary_defaults(
            summary,
            generated_at_iso=gen_at.isoformat(),
            brief_date=brief_date,
        )
        strip_summary_to_macro_schema(summary)
        used_fallback = True
        meta["fallback_reason"] = "Fallback: OpenAI request failed."

    meta["sources_scanned"] = ev_stats["sources_scanned"]
    meta["articles_selected"] = ev_stats["articles_selected"]
    meta["verified_links"] = verified_ok
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
