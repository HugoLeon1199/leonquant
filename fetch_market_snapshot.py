#!/usr/bin/env python3
"""Thu thập snapshot giá tài sản công khai (Yahoo Finance chart API) — không bịa số khi lỗi."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PROJECT_DIR / "market_snapshot.json"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 LEONQuantLabs/1.0"
)

# (yahoo_symbol, display_name, currency_hint)
ASSET_DEFINITIONS: list[tuple[str, str, str]] = [
    ("BZ=F", "Brent crude oil (front month)", "USD"),
    ("CL=F", "WTI crude oil (front month)", "USD"),
    ("GC=F", "Gold (COMEX)", "USD"),
    ("SI=F", "Silver (COMEX)", "USD"),
    ("BTC-USD", "Bitcoin", "USD"),
    ("ETH-USD", "Ethereum", "USD"),
    ("DX-Y.NYB", "US Dollar Index (DXY)", "USD"),
    ("^TNX", "US Treasury 10Y yield", "pct"),
    ("VND=X", "USD/VND", "VND"),
    ("VNM", "VN-Index proxy (VanEck Vietnam ETF)", "USD"),
]


def _iso_from_unix(ts: Any) -> str:
    if ts is None:
        return ""
    try:
        t = float(ts)
        return datetime.fromtimestamp(t, tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return ""


def fetch_yahoo_chart(symbol: str, timeout: int = 14) -> dict[str, Any]:
    """Một hàng `assets` item; không raise."""
    enc = quote(symbol, safe="")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{enc}?range=5d&interval=1d"
    row: dict[str, Any] = {
        "symbol": symbol,
        "name": "",
        "price": None,
        "change_pct": None,
        "currency": "",
        "timestamp": "",
        "source": "yahoo_finance_chart",
        "status": "missing",
        "note": "",
    }
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
        payload = json.loads(raw.decode("utf-8", errors="replace"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, UnicodeError, ValueError) as e:
        row["status"] = "error"
        row["note"] = str(e)
        return row

    chart = payload.get("chart") or {}
    err = chart.get("error")
    if err:
        row["status"] = "error"
        row["note"] = json.dumps(err, ensure_ascii=False)[:500]
        return row
    results = chart.get("result")
    if not results:
        row["status"] = "missing"
        row["note"] = "empty chart result"
        return row
    meta = results[0].get("meta") or {}
    price = meta.get("regularMarketPrice")
    if price is None:
        price = meta.get("previousClose") or meta.get("regularMarketPreviousClose")
    prev = meta.get("chartPreviousClose")
    if prev is None:
        prev = meta.get("previousClose")

    change_pct = None
    try:
        if price is not None and prev is not None and float(prev) != 0:
            change_pct = round((float(price) - float(prev)) / float(prev) * 100.0, 4)
    except (TypeError, ValueError):
        change_pct = None

    currency = str(meta.get("currency", "") or "")
    ts = _iso_from_unix(meta.get("regularMarketTime") or meta.get("gmtoffset"))

    row["price"] = float(price) if price is not None else None
    row["change_pct"] = change_pct
    row["currency"] = currency
    row["timestamp"] = ts
    row["status"] = "ok" if price is not None else "missing"
    if row["status"] == "missing":
        row["note"] = "no price in response"
    return row


def build_snapshot(timeout: int) -> dict[str, Any]:
    generated = datetime.now(timezone.utc).isoformat()
    assets: list[dict[str, Any]] = []
    for ysym, name, cur_hint in ASSET_DEFINITIONS:
        row = fetch_yahoo_chart(ysym, timeout=timeout)
        row["name"] = name
        if not row.get("currency"):
            row["currency"] = cur_hint
        assets.append(row)

    ok_n = sum(1 for a in assets if a.get("status") == "ok")
    note = (
        f"Public Yahoo Finance chart endpoint (~{ok_n}/{len(assets)} OK). "
        "Not guaranteed real-time; dùng chỉ để neo số liệu, không phải khuyến nghị giao dịch."
    )
    return {
        "generated_at": generated,
        "assets": assets,
        "coverage_note": note,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch best-effort market snapshot JSON.")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT))
    parser.add_argument("--timeout", type=int, default=14, help="Seconds per Yahoo request")
    args = parser.parse_args()
    out = Path(args.output)
    snap = build_snapshot(timeout=args.timeout)
    out.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out} ({len(snap['assets'])} assets)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
