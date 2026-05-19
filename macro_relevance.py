"""Heuristic macro relevance score for news articles (used by export_intel_to_news_output)."""

from __future__ import annotations

from typing import Any

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
