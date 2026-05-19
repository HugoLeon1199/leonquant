"""Markdown summaries for profiling runs."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from storage.db import WebIntelDB


def build_profile_markdown(db: WebIntelDB) -> str:
    rows = db.fetch_all_profiles()
    total = len(rows)
    strat_counts = Counter(r.get("best_strategy") or "" for r in rows)
    status_counts = Counter(r.get("status") or "" for r in rows)

    active = sum(1 for r in rows if r.get("status") == "active")
    active_cand = sum(1 for r in rows if r.get("status") == "active_candidate")
    review = sum(1 for r in rows if r.get("status") == "review")
    errors = sum(1 for r in rows if r.get("error_message"))

    ready = sorted(
        rows,
        key=lambda r: (
            0 if r.get("best_strategy") == "api_first" else 1,
            r.get("source_id") or "",
        ),
    )[:20]

    review_rows = [
        r
        for r in rows
        if r.get("best_strategy") in ("manual_review", "metadata_only")
        or r.get("html_status_code", 0) >= 400
        or r.get("error_message")
    ]

    lines: list[str] = []
    lines.append("# Profile Summary")
    lines.append("")
    lines.append(f"- total_sources: {total}")
    lines.append(f"- active_sources: {active}")
    lines.append(f"- active_candidate_sources: {active_cand}")
    lines.append(f"- review_sources: {review}")
    lines.append(f"- error_sources: {errors}")
    lines.append("")
    lines.append("## Strategy Breakdown")
    lines.append("")
    for k in [
        "api_first",
        "rss_then_article_extract",
        "sitemap_then_article_extract",
        "html_then_trafilatura",
        "playwright_fallback",
        "metadata_only",
        "manual_review",
    ]:
        lines.append(f"- {k}: {strat_counts.get(k, 0)}")
    lines.append("")
    lines.append("## Readiness")
    lines.append("")
    lines.append("Top 20 ready sources:")
    lines.append("")
    lines.append("source_id | domain | best_strategy | rss | sitemap | html_ok")
    lines.append("--- | --- | --- | --- | --- | ---")
    for r in ready:
        rss = bool(json.loads(r.get("rss_urls") or "[]"))
        sm = bool(json.loads(r.get("sitemap_urls") or "[]"))
        html_ok = bool(r.get("html_extract_ok"))
        lines.append(
            f"{r.get('source_id')} | {r.get('domain')} | {r.get('best_strategy')} | {rss} | {sm} | {html_ok}"
        )
    lines.append("")
    lines.append("## Sources Needing Review")
    lines.append("")
    lines.append("source_id | domain | reason | error_message")
    lines.append("--- | --- | --- | ---")
    for r in review_rows[:50]:
        reason_parts = []
        if r.get("best_strategy"):
            reason_parts.append(str(r.get("best_strategy")))
        if r.get("paywall_detected"):
            reason_parts.append("paywall_signal")
        if r.get("login_detected"):
            reason_parts.append("login_signal")
        if r.get("captcha_detected"):
            reason_parts.append("captcha_signal")
        reason = ", ".join(reason_parts) or "unspecified"
        err_raw = r.get("error_message")
        err = str(err_raw if err_raw is not None and str(err_raw) != "nan" else "").replace("\n", " ")[:200]
        lines.append(f"{r.get('source_id')} | {r.get('domain')} | {reason} | {err}")
    lines.append("")
    lines.append("## Next Steps")
    lines.append("")
    lines.append("- crawl sample active sources")
    lines.append("- review metadata_only")
    lines.append("- add API adapters for top official sources")
    lines.append("- expand sources after v1 stable")
    lines.append("")
    return "\n".join(lines)


def write_profile_summary(db: WebIntelDB, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_profile_markdown(db), encoding="utf-8")


def console_strategy_counts(db: WebIntelDB) -> dict[str, int]:
    rows = db.fetch_all_profiles()
    return Counter(r.get("best_strategy") or "" for r in rows)
