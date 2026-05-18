#!/usr/bin/env python3
"""Build config/news_sources_tiered.json from news_sources.json + curated extras."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEGACY_PATH = ROOT / "news_sources.json"
OUT_PATH = ROOT / "config" / "news_sources_tiered.json"

# Legacy feed `name` values must match news_sources.json exactly.
TIER_LEGACY_NAMES: list[tuple[str, str, list[str]]] = [
    (
        "vietnam_finance_stock_economy",
        "VIETNAM - FINANCE / STOCK / ECONOMY",
        [
            "CafeF Thi Truong Chung Khoan",
            "CafeF Tai Chinh Ngan Hang",
            "CafeF Vi Mo Dau Tu",
            "VietnamBiz Tai Chinh",
            "VietnamBiz Chung Khoan",
            "VietnamBiz Hang Hoa",
            "CafeBiz Tai Chinh Ngan Hang",
            "CafeBiz Vi Mo",
        ],
    ),
    (
        "vietnam_business_policy_macro",
        "VIETNAM - BUSINESS / POLICY / MACRO",
        [
            "CafeF Doanh Nghiep",
            "VnEconomy Cong Nghe Startup",
        ],
    ),
    (
        "vietnam_big_news_economy",
        "VIETNAM - BIG NEWS SITES / ECONOMY CATEGORY",
        [
            "VnExpress Kinh Doanh",
        ],
    ),
    (
        "vietnam_real_estate_construction",
        "VIETNAM - REAL ESTATE / CONSTRUCTION / PLANNING",
        [
            "VnExpress Bat Dong San",
            "CafeF Bat Dong San",
        ],
    ),
    (
        "international_macro_central_bank_data",
        "INTERNATIONAL - MACRO / CENTRAL BANK / DATA",
        [
            "Federal Reserve Press Releases",
            "Federal Reserve Speeches",
            "Federal Reserve Testimony",
            "ECB Press",
            "ECB Blog",
            "SEC Press Releases",
            "Bank of England News",
            "Bank of England Speeches",
            "Bank of Japan Updates",
            "Asian Development Bank News",
            "NBER New Research",
        ],
    ),
    (
        "international_markets_forex_commodity",
        "INTERNATIONAL - MARKET / FOREX / GOLD / COMMODITY",
        [
            "CNBC Markets",
            "CNBC Economy",
            "Investing.com Economy",
            "Investing.com Stock Market",
            "MarketWatch Top Stories",
            "Yahoo Finance",
        ],
    ),
    (
        "international_crypto",
        "INTERNATIONAL - CRYPTO",
        [
            "CoinDesk",
            "Cointelegraph",
            "Decrypt",
            "CryptoSlate",
        ],
    ),
    (
        "international_business_news",
        "INTERNATIONAL - BUSINESS NEWS",
        [
            "The Guardian Business",
            "The Guardian Economics",
            "The Guardian Global Development",
            "BBC Business",
            "Al Jazeera Latest",
            "SCMP Business",
            "SCMP China Economy",
            "DW Business",
            "Business Insider",
            "Forbes Business",
            "Project Syndicate",
            "The Straits Times Business",
            "The Sydney Morning Herald Business",
            "The Globe and Mail Business",
            "Times of India Business",
            "Bangkok Post Business",
            "African Business",
        ],
    ),
]

# Additional RSS feeds (verified HTTP 200) — keyed by tier id.
TIER_EXTRAS: dict[str, list[dict[str, str]]] = {
    "vietnam_finance_stock_economy": [
        {
            "name": "Vietstock RSS",
            "url": "https://vietstock.vn/rss",
            "category": "markets",
            "region": "vietnam",
        },
    ],
    "vietnam_big_news_economy": [
        {
            "name": "TuoiTre Kinh Doanh RSS",
            "url": "https://tuoitre.vn/rss/kinh-doanh.rss",
            "category": "business",
            "region": "vietnam",
        },
        {
            "name": "ThanhNien Kinh Te RSS",
            "url": "https://thanhnien.vn/rss/kinh-te.rss",
            "category": "economy",
            "region": "vietnam",
        },
        {
            "name": "DanTri Kinh Doanh RSS",
            "url": "https://dantri.com.vn/rss/kinh-doanh.rss",
            "category": "business",
            "region": "vietnam",
        },
        {
            "name": "VietnamNet Kinh Doanh RSS",
            "url": "https://vietnamnet.vn/rss/kinh-doanh.rss",
            "category": "business",
            "region": "vietnam",
        },
    ],
    "international_markets_forex_commodity": [
        {
            "name": "FXStreet RSS",
            "url": "https://www.fxstreet.com/rss",
            "category": "markets",
            "region": "global",
        },
    ],
}


def main() -> None:
    legacy = json.loads(LEGACY_PATH.read_text(encoding="utf-8"))
    by_name = {str(s["name"]): s for s in legacy.get("sources", [])}

    tiers_out: list[dict[str, object]] = []
    for tier_id, title, names in TIER_LEGACY_NAMES:
        sources: list[dict[str, str]] = []
        for nm in names:
            if nm not in by_name:
                raise KeyError(f"Legacy source missing: {nm!r}")
            row = deepcopy(by_name[nm])
            sources.append(
                {
                    "name": str(row["name"]),
                    "url": str(row["url"]),
                    "category": str(row["category"]),
                    "region": str(row["region"]),
                }
            )
        for extra in TIER_EXTRAS.get(tier_id, []):
            sources.append(dict(extra))
        tiers_out.append({"id": tier_id, "title": title, "sources": sources})

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "tiers": tiers_out}
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    n = sum(len(t["sources"]) for t in tiers_out)  # type: ignore[arg-type]
    print(f"Wrote {OUT_PATH} ({len(tiers_out)} tiers, {n} feeds)")


if __name__ == "__main__":
    main()
