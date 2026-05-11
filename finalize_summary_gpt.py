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

from build_website_content import load_market_snapshot_json, rebuild_content_json


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

# Schema công khai: Investment Strategy Brief (không disclaimer / source_quality trong summary).
STRATEGY_BRIEF_SUMMARY_KEYS = frozenset(
    {
        "title",
        "date",
        "generated_at",
        "publication_intro",
        "main_thesis",
        "global_macro_drivers",
        "vietnam_transmission",
        "quick_actions",
        "allocation_guide",
        "sector_priority",
        "increase_risk_signals",
        "reduce_risk_signals",
        "scenario_plan",
        "final_takeaway",
    }
)

# Alias tương thích import cũ
MACRO_INTELLIGENCE_SUMMARY_KEYS = STRATEGY_BRIEF_SUMMARY_KEYS

SCHEMA_JSON_EXAMPLE = """{
  "title": "LEON Quant Labs — Góc nhìn vĩ mô và chiến lược thị trường",
  "date": "YYYY-MM-DD",
  "generated_at": "ISO-8601",
  "publication_intro": { "headline": "", "description": "" },
  "main_thesis": { "regime": "", "thesis": "", "action_conclusion": "" },
  "global_macro_drivers": [
    { "title": "", "analysis": "", "vietnam_impact": "" }
  ],
  "vietnam_transmission": { "summary": "", "chains": [] },
  "quick_actions": [ { "investor_state": "", "action": "" } ],
  "allocation_guide": [ { "profile": "", "stocks": "", "cash": "", "margin": "" } ],
  "sector_priority": [ { "sector": "", "view": "", "action": "" } ],
  "increase_risk_signals": [ { "signal": "", "meaning": "" } ],
  "reduce_risk_signals": [ { "signal": "", "action": "" } ],
  "scenario_plan": {
    "base_case": { "title": "Kịch bản cơ sở", "description": "", "action": "" },
    "bull_case": { "title": "Kịch bản tích cực", "description": "", "action": "" },
    "bear_case": { "title": "Kịch bản tiêu cực", "description": "", "action": "" }
  },
  "final_takeaway": ""
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
title, date, generated_at, publication_intro, main_thesis, global_macro_drivers,
vietnam_transmission, quick_actions, allocation_guide, sector_priority,
increase_risk_signals, reduce_risk_signals, scenario_plan, final_takeaway.

Do NOT output: market_regime, daily_thesis, source_quality, disclaimer, key_points,
brief_stories, asset_impact_heatmap, vietnam_investor_lens, scenario_map,
key_variables_to_watch, top_macro_drivers, or any keys not listed above.

Shape:
{SCHEMA_JSON_EXAMPLE}

Counts:
- global_macro_drivers: 3 or 4 items.
- quick_actions: at least 6 items covering common investor situations.
- allocation_guide: 3 items (Thận trọng, Cân bằng, Chủ động).
- sector_priority: 6–8 Vietnamese sectors.
- increase_risk_signals: 5 or 6 items.
- reduce_risk_signals: 5 or 6 items.
- vietnam_transmission.chains: list of strings (causal chains).

MARKET DATA (strict):
- `market_snapshot` is the ONLY source for specific prices or percentage changes.
- If price/change missing or status not ok, describe qualitatively only. Never invent numbers.

LANGUAGE: Vietnamese only in all string fields. JSON only, no markdown, no URLs in analytical text."""

    editorial = """
You are the final editor of LEON Quant Labs, an independent Vietnamese investment research publication.

Your job is NOT to summarize news.
Your job is to turn global macro developments into a concise, actionable market strategy brief for Vietnamese investors.

PUBLIC OUTPUT RULES (the JSON will be read by investors):
- Do NOT mention artificial intelligence, automation, crawling, models, pipelines, or how content was produced.
- Do NOT include a disclaimer section or field; do NOT say "this is not financial advice."
- Write as a serious human-edited investment research desk would.
- Every section must connect to what a Vietnamese investor should watch or do.

AUDIENCE:
Vietnamese investors, traders, and analysts who need:
(1) what is moving global macro, (2) how it transmits into Vietnam, (3) what to do on allocation, sectors, and risk.

STYLE:
- Short, sharp, desk-note tone; no hype; no chatbot phrasing; no news-aggregator feel.
- Prefer causal chains over isolated headlines; actionable language over pure description.
- If evidence in inputs is weak, use cautious wording. Do not overstate certainty.

THINKING ORDER:
Global macro → transmission → Vietnam impact → investor actions → allocation → sectors →
signals to add risk → signals to cut risk → three scenarios → closing takeaway.
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
                    "You output only valid JSON for the LEON Quant Labs Investment Strategy Brief. "
                    "Never include keys outside the user schema. "
                    "Never mention AI, automation, web crawling, language models, pipelines, or internal tooling in any string "
                    "meant for readers. "
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
title, date, generated_at, publication_intro, main_thesis, global_macro_drivers,
vietnam_transmission, quick_actions, allocation_guide, sector_priority,
increase_risk_signals, reduce_risk_signals, scenario_plan, final_takeaway.

Remove legacy keys such as market_regime, daily_thesis, source_quality, disclaimer,
top_macro_drivers, asset_impact_heatmap, vietnam_investor_lens, scenario_map,
key_variables_to_watch, or any other fields not in the list above.

Schema shape:
{SCHEMA_JSON_EXAMPLE}

Do not mention AI, automation, or production tooling in strings for readers.
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
    """Validate `summary` object inside final_summary.json (Investment Strategy Brief)."""
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

    def _obj_list(
        key: str,
        min_n: int,
        fields: tuple[str, ...],
    ) -> None:
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

    _obj_list("global_macro_drivers", 3, ("title", "analysis", "vietnam_impact"))
    _obj_list("quick_actions", 4, ("investor_state", "action"))
    _obj_list("allocation_guide", 3, ("profile", "stocks", "cash", "margin"))
    _obj_list("sector_priority", 6, ("sector", "view", "action"))
    _obj_list("increase_risk_signals", 4, ("signal", "meaning"))
    _obj_list("reduce_risk_signals", 4, ("signal", "action"))

    vt = data.get("vietnam_transmission")
    if not isinstance(vt, dict):
        errors.append("vietnam_transmission:not_object")
    else:
        if not str(vt.get("summary", "")).strip():
            errors.append("vietnam_transmission.summary:empty")
        ch = vt.get("chains")
        if ch is not None and not isinstance(ch, list):
            errors.append("vietnam_transmission.chains:bad")
        elif isinstance(ch, list):
            for i, c in enumerate(ch):
                if not isinstance(c, str) or not c.strip():
                    errors.append(f"vietnam_transmission.chains[{i}]:empty")

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

    if not str(data.get("final_takeaway", "")).strip():
        errors.append("final_takeaway:empty")

    forbidden_public = (
        "source_quality",
        "disclaimer",
        "market_regime",
        "daily_thesis",
        "asset_impact_heatmap",
    )
    for fk in forbidden_public:
        if fk in data:
            errors.append(f"forbidden_public_field:{fk}")

    return (len(errors) == 0, errors)


def merge_strategy_summary_defaults(
    summary: dict[str, Any],
    *,
    generated_at_iso: str,
    brief_date: str,
) -> None:
    summary["title"] = summary.get("title") or "LEON Quant Labs — Góc nhìn vĩ mô và chiến lược thị trường"
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
    gs = gemini_payload.get("summary", {}) if isinstance(gemini_payload.get("summary"), dict) else {}
    extra_ctx = (
        str(gs.get("executive_summary", "")).strip()
        or str(gs.get("global_watch", "")).strip()
        or str(gs.get("title", "")).strip()
    )
    thesis_body = (
        "Thị trường toàn cầu chịu ảnh hưởng từ lãi suất Mỹ, đồng USD, giá dầu và dòng vốn quốc tế. "
        "Với Việt Nam, cơ hội vẫn tồn tại nhưng phụ thuộc vào thanh khoản nội địa, nhóm dẫn dắt và hoạt động của khối ngoại."
    )
    if extra_ctx:
        thesis_body = f"{thesis_body} Bối cảnh tin tức hiện có: {extra_ctx[:900]}"

    return {
        "title": "LEON Quant Labs — Góc nhìn vĩ mô và chiến lược thị trường",
        "date": brief_date,
        "generated_at": generated_at_iso,
        "publication_intro": {
            "headline": "Góc nhìn vĩ mô và chiến lược thị trường dành cho nhà đầu tư Việt Nam",
            "description": (
                "LEON Quant Labs tập trung vào việc chuyển biến động vĩ mô toàn cầu thành góc nhìn đầu tư "
                "có thể hành động tại thị trường Việt Nam."
            ),
        },
        "main_thesis": {
            "regime": "Thận trọng có chọn lọc",
            "thesis": thesis_body,
            "action_conclusion": (
                "Không cần rút lui hoàn toàn, nhưng cũng không nên mua đuổi. Ưu tiên cổ phiếu khỏe, giữ tỷ trọng vừa phải, "
                "hạn chế margin và chờ xác nhận từ dòng tiền."
            ),
        },
        "global_macro_drivers": [
            {
                "title": "Lãi suất Mỹ còn cao",
                "analysis": (
                    "Khi Fed chưa vội hạ lãi suất, lợi suất trái phiếu Mỹ dễ duy trì ở vùng tương đối cao. "
                    "Chi phí vốn toàn cầu đắt hơn và tài sản rủi ro khó mở rộng định giá mạnh nếu không có tin tích cực rõ ràng."
                ),
                "vietnam_impact": (
                    "Kênh tâm lý risk-off và dòng vốn: nhà đầu tư mới nởi thường thận trọng hơn; cổ phiếu Việt Nam cần dựa nhiều vào dòng tiền nội."
                ),
            },
            {
                "title": "Đồng USD mạnh gây áp lực tỷ giá",
                "analysis": (
                    "USD mạnh thường kéo chi phí nhập khẩu hàng hóa USD và làm thắt tài chính cho các DN có nợ ngoại tệ."
                ),
                "vietnam_impact": "Áp lực lên USD/VND và kỳ vọng chính sách; khối ngoại có thể cân nhắc tốc độ phân bổ.",
            },
            {
                "title": "Giá dầu là rủi ro lạm phát",
                "analysis": (
                    "Dầu cao không chỉ tác động nhóm năng lượng mà lan sang vận tải, sản xuất và kỳ vọng lạm phát."
                ),
                "vietnam_impact": (
                    "Biên lợi nhuận DN sử dụng năng lượng và logistics chịu áp lực; tâm lý thị trường dễ nhạy với shock giá."
                ),
            },
        ],
        "vietnam_transmission": {
            "summary": (
                "Chuỗi tác động thường gặp: lãi suất Mỹ cao → USD mạnh → áp lực USD/VND → khối ngoại thận trọng hơn "
                "→ VN-Index cần dựa nhiều hơn vào dòng tiền nội và nhóm dẫn dắt."
            ),
            "chains": [
                "Lãi suất Mỹ cao → USD mạnh → áp lực USD/VND → khối ngoại thận trọng.",
                "Giá dầu biến động → lạm phát kỳ vọng → tâm lý risk-off → định giá tài sản rủi ro thắt lại.",
            ],
        },
        "quick_actions": [
            {"investor_state": "Cầm nhiều tiền mặt", "action": "Chưa cần mua vội; ưu tiên theo dõi thanh khoản và độ rộng."},
            {"investor_state": "Đang nắm cổ phiếu tốt", "action": "Có thể tiếp tục nắm; đặt điểm cắt lỗ/hạ tỷ trọng nếu thị trường suy yếu đồng loạt."},
            {"investor_state": "Đang lãi ngắn hạn", "action": "Chốt lời một phần để bảo toàn lợi thế; tránh mua thêm đuổi đỉnh."},
            {"investor_state": "Đang dùng margin cao", "action": "Hạ đòn bẩy về mức an toàn; ưu tiên sống sót qua nhịp biến động."},
            {"investor_state": "Muốn mua mới", "action": "Chỉ tích sườn nhỏ; chọn cổ phiếu khỏe có dòng tiền xác nhận."},
            {"investor_state": "Đang kẹt cổ phiếu yếu", "action": "Không cố gồng; cơ cấu sang mã có cơ bản và thanh khoản tốt hơn."},
        ],
        "allocation_guide": [
            {"profile": "Thận trọng", "stocks": "30–40%", "cash": "60–70%", "margin": "Không dùng"},
            {"profile": "Cân bằng", "stocks": "50–60%", "cash": "40–50%", "margin": "Rất thấp, chỉ khi thị trường xác nhận"},
            {"profile": "Chủ động", "stocks": "60–70%", "cash": "30–40%", "margin": "Chỉ khi sóng và thanh khoản rõ ràng"},
        ],
        "sector_priority": [
            {"sector": "Ngân hàng", "view": "Tích cực có chọn lọc", "action": "Ưu tiên mã có CASA tốt và room tín dụng lành mạnh."},
            {"sector": "Dầu khí", "view": "Tích cực ngắn hạn có điều kiện", "action": "Theo giá dầu và tin địa chính trị; quản trị nhịp điều chỉnh."},
            {"sector": "Chứng khoán", "view": "Phụ thuộc thanh khoản", "action": "Chỉ mạnh khi dòng tiền cá nhân/ margin bền."},
            {"sector": "Khu công nghiệp", "view": "Trung tính tích cực", "action": "Chọn KCN có kế hoạch lấp đầy và khách lớn ổn định."},
            {"sector": "Xuất khẩu", "view": "Trung tính", "action": "Lưu ý USD/VND và cầu bên ngoài."},
            {"sector": "Bất động sản", "view": "Thận trọng", "action": "Chỉ xem các dự án có dòng tiền và pháp lý rõ."},
            {"sector": "Thép", "view": "Trung tính thận trọng", "action": "Bám giá nguyên liệu và biên lợi nhuận."},
            {"sector": "Bán lẻ", "view": "Chọn lọc", "action": "Ưu tiên chuỗi có same-store tốt và kiểm soát chi phí."},
        ],
        "increase_risk_signals": [
            {"signal": "VN-Index tăng cùng thanh khoản cải thiện", "meaning": "Dòng tiền xác nhận nhịp tăng có thể lan rộng hơn."},
            {"signal": "Số mã tăng lan rộng", "meaning": "Độ rộng tốt giảm rủi ro ‘chỉ số giả vờ’."},
            {"signal": "Ngân hàng giữ vai trò dẫn dắt", "meaning": "Nhóm nền tảng ổn định thường củng cố xu hướng."},
            {"signal": "Khối ngoại giảm bán hoặc mua ròng", "meaning": "Áp lực bán ETF/passive có thể hạ nhiệt."},
            {"signal": "USD/VND ổn định", "meaning": "Giảm rủi ro tâm lý tỷ giá với danh mục nội địa."},
            {"signal": "Cổ phiếu vượt nền với volume tốt", "meaning": "Xác nhận kỹ thuật có đỡ dòng tiền thật."},
        ],
        "reduce_risk_signals": [
            {"signal": "VN-Index tăng nhưng độ rộng yếu", "action": "Hạ kỳ vọng; tránh mua đuổi đỉnh hẹp."},
            {"signal": "Thanh khoản giảm trong nhịp tăng", "action": "Thận trọng; dễ đảo chiều nhanh."},
            {"signal": "Khối ngoại bán ròng mạnh", "action": "Ưu tiên giữ tiền mặt bảo vệ vốn."},
            {"signal": "USD/VND tăng nhanh", "action": "Xem xét giảm tỷ trọng nhóm nhạy FX và margin."},
            {"signal": "Ngân hàng suy yếu đồng loạt", "action": "Tín hiệu hệ thống tài chính stress; giảm rủi ro."},
            {"signal": "Cổ phiếu đầu cơ tăng nóng", "action": "Rủi ro bull trap; không chasing nhóm mỏng thanh khoản."},
        ],
        "scenario_plan": {
            "base_case": {
                "title": "Kịch bản cơ sở",
                "description": "Thị trường phân hóa; vĩ mô vẫn có điểm nghẽn nhưng chưa vỡ trận.",
                "action": "Giữ tỷ trọng vừa phải; ưu tiên cổ phiếu chất lượng và quản trị margin.",
            },
            "bull_case": {
                "title": "Kịch bản tích cực",
                "description": "USD hạ nhiệt, thanh khoản cải thiện, rủi ro hệ thống không leo thang.",
                "action": "Tăng tỷ trọng từng phần theo nhịp xác nhận; giữ cash để còn quyền chủ động.",
            },
            "bear_case": {
                "title": "Kịch bản tiêu cực",
                "description": "USD mạnh, khối ngoại bán ròng, VN-Index mất các ngưỡng hỗ trợ quan trọng.",
                "action": "Giảm cổ phiếu, hạ margin; ưu tiên an toàn vốn và thanh khoản cá nhân.",
            },
        },
        "final_takeaway": (
            "Bối cảnh hiện tại không ủng hộ chiến lược all-in, nhưng cũng chưa yêu cầu phải rút lui hoàn toàn. "
            "Vĩ mô thế giới vẫn còn áp lực từ lãi suất Mỹ, đồng USD và giá dầu. Thị trường Việt Nam vẫn có cơ hội nếu dòng tiền nội "
            "duy trì và nhóm ngân hàng giữ vai trò dẫn dắt. Chiến lược hợp lý là giữ danh mục gọn, nắm cổ phiếu khỏe, tránh mua đuổi, "
            "hạn chế margin và giữ tiền mặt để có quyền chủ động."
        ),
    }


def strip_summary_to_macro_schema(summary: dict[str, Any]) -> None:
    """Giữ đúng schema Investment Strategy Brief; xoá mọi key không thuộc public summary."""
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
        description="Finalize editorial pass — Investment Strategy Brief JSON (OpenAI).",
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
                meta["pipeline_note"] = "Fallback: final editorial output failed validation."
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
        meta["pipeline_note"] = "Fallback: OpenAI request failed."

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
