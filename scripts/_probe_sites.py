#!/usr/bin/env python3
"""Quick HTTP probe: status, title snippet, paywall keywords for sample domains."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "leon_web_intel" / "src"))
from settings import load_crawl_rules  # noqa: E402
from profiler.paywall_detector import detect_paywall_signals  # noqa: E402

rules = load_crawl_rules(ROOT / "leon_web_intel" / "config" / "crawl_rules.yaml")
UA = rules.user_agent

SAMPLES = [
    ("SKIP-blocked", "https://dantri.com.vn/kinh-doanh.htm"),
    ("SKIP-blocked", "https://cafebiz.vn"),
    ("SKIP-blocked", "https://tuoitre.vn/kinh-doanh.htm"),
    ("SKIP-reuters", "https://www.reuters.com/markets/"),
    ("OK-NotToday", "https://cafef.vn"),
    ("OK-hasDB", "https://vneconomy.vn"),
    ("OK-hasDB", "https://plo.vn"),
    ("SKIP-profile", "https://www.hnx.vn"),
    ("UNCLEAR", "https://vnexpress.net/kinh-doanh"),
]

lines: list[str] = []
client = httpx.Client(
    follow_redirects=True,
    timeout=25.0,
    headers={"User-Agent": UA},
)

for label, url in SAMPLES:
    lines.append(f"\n[{label}] {url}")
    try:
        r = client.get(url)
        html = r.text[:80000]
        title_m = re.search(r"<title[^>]*>([^<]{1,200})", html, re.I)
        title = (title_m.group(1).strip() if title_m else "")[:100]
        sig = detect_paywall_signals(html, rules)
        lines.append(f"  HTTP {r.status_code} | len={len(r.text)} | title={title!r}")
        lines.append(
            f"  signals: paywall={sig.paywall_detected} login={sig.login_detected} captcha={sig.captcha_detected}"
        )
        has_article_like = bool(re.search(r"<article|class=[\"'][^\"']*(?:article|post-item|story)", html[:50000], re.I))
        lines.append(f"  co HTML bai (heuristic): {has_article_like}")
    except Exception as exc:
        lines.append(f"  LOI: {exc}")

client.close()
out = ROOT / "scripts" / "_probe_results.txt"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(out.read_text(encoding="utf-8"))
