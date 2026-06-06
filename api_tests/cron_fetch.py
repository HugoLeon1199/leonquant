#!/usr/bin/env python3
"""One third-party API request per run; accumulate unique articles (30m cron)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api_tests.test_news_apis import (  # noqa: E402
    ENV_EXAMPLE,
    ENV_FILE,
    QUERY,
    fetch_gnews,
    fetch_newsdata,
    fetch_worldnews,
    load_dotenv,
)

DATA_DIR = Path(__file__).resolve().parent / "data"
ACCUMULATOR = DATA_DIR / "cron_accumulator.json"
SUMMARY_MD = DATA_DIR / "cron_summary.md"

APIS = ("worldnews", "gnews", "newsdata")
FETCHERS = {
    "worldnews": fetch_worldnews,
    "gnews": fetch_gnews,
    "newsdata": fetch_newsdata,
}
KEY_NAMES = {
    "worldnews": "WORLDNEWS_API_KEY",
    "gnews": "GNEWS_API_KEY",
    "newsdata": "NEWSDATA_API_KEY",
}


def empty_state() -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "started_at_utc": now,
        "query": QUERY,
        "rotation": list(APIS),
        "runs": [],
        "articles_by_url": {},
    }


def load_state() -> dict:
    if not ACCUMULATOR.is_file():
        return empty_state()
    return json.loads(ACCUMULATOR.read_text(encoding="utf-8"))


def choose_api(state: dict) -> str:
    runs = state.get("runs") or []
    return APIS[len(runs) % len(APIS)]


def slim_article(article: dict) -> dict:
    return {
        "api": article.get("api"),
        "title": article.get("title"),
        "content_length": article.get("content_length"),
        "looks_full_content": article.get("looks_full_content"),
        "published_at_utc": article.get("published_at_utc"),
        "within_48h": article.get("within_48h"),
    }


def compute_stats(state: dict) -> dict:
    by_url = state.get("articles_by_url") or {}
    by_api_unique: dict[str, int] = {}
    by_api_full: dict[str, int] = {}
    for rec in by_url.values():
        api = str(rec.get("api") or "unknown")
        by_api_unique[api] = by_api_unique.get(api, 0) + 1
        if rec.get("looks_full_content"):
            by_api_full[api] = by_api_full.get(api, 0) + 1

    by_api_runs: dict[str, dict[str, int]] = {}
    for run in state.get("runs") or []:
        api = str(run.get("api") or "unknown")
        slot = by_api_runs.setdefault(api, {"runs": 0, "articles_fetched": 0, "errors": 0})
        slot["runs"] += 1
        slot["articles_fetched"] += int(run.get("articles_fetched") or 0)
        if run.get("errors"):
            slot["errors"] += 1

    runs = state.get("runs") or []
    return {
        "total_runs": len(runs),
        "total_requests": len(runs),
        "unique_urls_total": len(by_url),
        "full_content_urls": sum(1 for r in by_url.values() if r.get("looks_full_content")),
        "by_api_unique": by_api_unique,
        "by_api_full_content": by_api_full,
        "by_api_runs": by_api_runs,
        "last_run_utc": runs[-1].get("run_at_utc") if runs else None,
    }


def write_summary(state: dict, stats: dict) -> None:
    lines = [
        "# API cron accumulator (30 phút / 1 request)",
        "",
        f"Started: `{state.get('started_at_utc')}`",
        f"Query: `{state.get('query')}`",
        f"Updated: `{state.get('updated_at_utc')}`",
        "",
        "## Totals",
        "",
        f"- HTTP requests: **{stats['total_runs']}**",
        f"- Unique URLs: **{stats['unique_urls_total']}**",
        f"- URLs with full-ish body: **{stats['full_content_urls']}**",
        "",
        "## By API",
        "",
        "| API | runs | fetched | unique URLs | full body |",
        "|-----|------|---------|-------------|-----------|",
    ]
    for api in APIS:
        runs = stats.get("by_api_runs", {}).get(api, {})
        lines.append(
            f"| {api} | {runs.get('runs', 0)} | {runs.get('articles_fetched', 0)} | "
            f"{stats.get('by_api_unique', {}).get(api, 0)} | "
            f"{stats.get('by_api_full_content', {}).get(api, 0)} |"
        )
    lines.extend(["", "## Recent runs (last 12)", ""])
    for run in (state.get("runs") or [])[-12:]:
        err = run["errors"][0][:70] if run.get("errors") else "OK"
        lines.append(
            f"- `{run.get('run_at_utc')}` **{run.get('api')}** → "
            f"{run.get('articles_fetched', 0)} fetched, +{run.get('new_unique_urls', 0)} new · {err}"
        )
    lines.append("")
    lines.append("_Rotate: worldnews → gnews → newsdata. Standalone — chưa vào Tin48h pipeline._")
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    env = load_dotenv(ENV_EXAMPLE)
    env.update(load_dotenv(ENV_FILE))

    state = load_state()
    api = choose_api(state)
    run_at = datetime.now(timezone.utc).isoformat()
    run_rec: dict = {
        "run_at_utc": run_at,
        "api": api,
        "http_status": 0,
        "articles_fetched": 0,
        "new_unique_urls": 0,
        "errors": [],
        "quota_hint": {},
    }

    key = (env.get(KEY_NAMES[api]) or "").strip()
    if not key or key.lower().startswith("your-"):
        run_rec["errors"].append(f"Missing API key for {api}")
    else:
        meta = FETCHERS[api](key)
        run_rec["http_status"] = int(meta.get("http_status") or 0)
        run_rec["errors"] = list(meta.get("errors") or [])
        run_rec["quota_hint"] = dict(meta.get("quota_hint") or {})
        articles = meta.get("articles") or []
        run_rec["articles_fetched"] = len(articles)

        by_url = state.setdefault("articles_by_url", {})
        new_count = 0
        for article in articles:
            url = str(article.get("url") or "").strip()
            if not url or url in by_url:
                continue
            new_count += 1
            by_url[url] = {"first_seen_utc": run_at, **slim_article(article)}
        run_rec["new_unique_urls"] = new_count

    state.setdefault("runs", []).append(run_rec)
    stats = compute_stats(state)
    state["stats"] = stats
    state["updated_at_utc"] = run_at

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ACCUMULATOR.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_summary(state, stats)

    print(
        f"[cron] {api} @ {run_at}: fetched={run_rec['articles_fetched']} "
        f"new={run_rec['new_unique_urls']} unique_total={stats['unique_urls_total']}"
    )
    if run_rec["errors"]:
        print(f"[cron] errors: {run_rec['errors']}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
