#!/usr/bin/env python3
"""
Standalone quality test for third-party news APIs (NewsData, GNews, WorldNews).

Does NOT touch Tin48h, invest, LIVE, or content.json writes.
"""

from __future__ import annotations

import csv
import json
import re
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"
CONTENT_JSON = ROOT / "content.json"

QUERY = "economy OR finance OR market"
PER_API_LIMIT = 30
REQUEST_TIMEOUT = 45
USER_AGENT = "LeonQuant-API-Quality-Test/1.0 (+local eval only)"

TRUNCATION_PATTERNS = (
    re.compile(r"\[\+\d+\s*chars?\]", re.I),
    re.compile(r"\.\.\.\s*$"),
    re.compile(r"…\s*$"),
    re.compile(r"\bread more\b", re.I),
    re.compile(r"\bcontinue reading\b", re.I),
    re.compile(r"\bsubscribers only\b", re.I),
    re.compile(r"\bsign in to read\b", re.I),
    re.compile(r"\bpremium content\b", re.I),
)

PAYWALL_PATTERNS = (
    re.compile(r"\bsubscribe\b", re.I),
    re.compile(r"\bpaywall\b", re.I),
    re.compile(r"\bmembers only\b", re.I),
    re.compile(r"\bsign in to read\b", re.I),
)


def load_dotenv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        k = k.strip()
        if k:
            out[k] = v.strip().strip('"').strip("'")
    return out


def http_get_json(url: str, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any] | list[Any] | None, str]:
    """GET JSON with one retry on transient network errors."""
    last_err = ""
    for attempt in (1, 2):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": USER_AGENT, **(headers or {})},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                status = int(getattr(resp, "status", 200) or 200)
            try:
                return status, json.loads(body), body[:500]
            except json.JSONDecodeError:
                return status, None, body[:500]
        except urllib.error.HTTPError as exc:
            chunk = exc.read().decode("utf-8", errors="replace")[:500]
            return int(exc.code), None, chunk or str(exc)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_err = str(exc)
            if attempt == 1:
                time.sleep(2)
                continue
            return 0, None, last_err
    return 0, None, last_err


def parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    for fmt in (
        None,
    ):
        _ = fmt
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        pass
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(s[:19] if " " in fmt else s[:10], fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def normalize_url(url: str) -> str:
    u = (url or "").strip().lower()
    if not u:
        return ""
    u = u.split("#", 1)[0]
    u = u.rstrip("/")
    if u.startswith("http://"):
        u = "https://" + u[7:]
    return u


def load_existing_pipeline_urls() -> set[str]:
    if not CONTENT_JSON.is_file():
        return set()
    try:
        data = json.loads(CONTENT_JSON.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return set()
    urls: set[str] = set()
    for key in ("articleLinkIndex", "articles"):
        items = data.get(key)
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict):
                u = normalize_url(str(item.get("url") or ""))
                if u:
                    urls.add(u)
    return urls


def assess_content(title: str, description: str, content: str) -> dict[str, Any]:
    desc = (description or "").strip()
    body = (content or "").strip()
    combined = f"{title}\n{desc}\n{body}"
    notes: list[str] = []
    looks_truncated = False
    has_paywall_hint = False

    if not body:
        notes.append("empty_content")
    if len(body) < 120 and desc and len(desc) > len(body):
        notes.append("likely_snippet_only")
        looks_truncated = True
    if len(body) < 400 and body.endswith("..."):
        looks_truncated = True
        notes.append("ends_with_ellipsis")

    for pat in TRUNCATION_PATTERNS:
        if pat.search(combined):
            looks_truncated = True
            notes.append(f"truncation_pattern:{pat.pattern[:40]}")
            break

    for pat in PAYWALL_PATTERNS:
        if pat.search(combined):
            has_paywall_hint = True
            notes.append(f"paywall_hint:{pat.pattern[:30]}")
            break

    looks_full = bool(body) and len(body) >= 800 and not looks_truncated and not has_paywall_hint
    if body and len(body) < 200:
        notes.append("very_short_content")

    return {
        "raw_content_length": len(body or desc),
        "description_length": len(desc),
        "content_length": len(body),
        "looks_full_content": looks_full,
        "looks_truncated": looks_truncated,
        "has_paywall_hint": has_paywall_hint,
        "quality_notes": notes,
    }


def build_article(
    api: str,
    *,
    title: str = "",
    url: str = "",
    source_name: str = "",
    published_at: str = "",
    language: str = "",
    country: str = "",
    category: str = "",
    description: str = "",
    content: str = "",
    author: str = "",
    image_url: str = "",
) -> dict[str, Any]:
    pub_dt = parse_datetime(published_at)
    within_48h = False
    if pub_dt:
        within_48h = pub_dt >= datetime.now(timezone.utc) - timedelta(hours=48)
    quality = assess_content(title, description, content)
    row = {
        "api": api,
        "title": title.strip(),
        "url": url.strip(),
        "source_name": source_name.strip(),
        "published_at": published_at.strip(),
        "published_at_utc": pub_dt.isoformat() if pub_dt else "",
        "within_48h": within_48h,
        "language": language.strip(),
        "country": country.strip(),
        "category": category.strip(),
        "description": description.strip(),
        "content": content.strip(),
        "author": author.strip(),
        "image_url": image_url.strip(),
        **quality,
    }
    return row


def fetch_newsdata(api_key: str) -> dict[str, Any]:
    base_params = {
        "apikey": api_key,
        "q": QUERY,
        "language": "en",
        "size": str(min(PER_API_LIMIT, 10)),
    }
    params = {**base_params, "timeframe": "48"}
    url = "https://newsdata.io/api/1/latest?" + urllib.parse.urlencode(params)
    status, payload, raw_hint = http_get_json(url)
    if status == 422 and "timeframe" in raw_hint.lower():
        url = "https://newsdata.io/api/1/latest?" + urllib.parse.urlencode(base_params)
        status, payload, raw_hint = http_get_json(url)
        params = base_params
    meta: dict[str, Any] = {
        "api": "newsdata",
        "request_url": url.split("apikey=", 1)[0] + "apikey=***",
        "http_status": status,
        "errors": [],
        "quota_hint": {},
        "articles": [],
    }
    if status != 200 or not isinstance(payload, dict):
        meta["errors"].append(f"HTTP {status}: {raw_hint[:200]}")
        return meta
    if payload.get("status") == "error":
        meta["errors"].append(str(payload.get("message") or payload.get("results") or "API error"))
        return meta
    meta["quota_hint"] = {
        k: payload.get(k)
        for k in ("totalResults", "nextPage", "status")
        if payload.get(k) is not None
    }
    results = payload.get("results") or []
    if not isinstance(results, list):
        meta["errors"].append("Unexpected results shape")
        return meta
    for item in results[:PER_API_LIMIT]:
        if not isinstance(item, dict):
            continue
        authors = item.get("creator")
        author = ", ".join(authors) if isinstance(authors, list) else str(authors or "")
        cats = item.get("category")
        category = ", ".join(cats) if isinstance(cats, list) else str(cats or "")
        countries = item.get("country")
        country = ", ".join(countries) if isinstance(countries, list) else str(countries or "")
        meta["articles"].append(
            build_article(
                "newsdata",
                title=str(item.get("title") or ""),
                url=str(item.get("link") or item.get("source_url") or ""),
                source_name=str(item.get("source_id") or item.get("source_name") or ""),
                published_at=str(item.get("pubDate") or item.get("published_at") or ""),
                language=str(item.get("language") or "en"),
                country=country,
                category=category,
                description=str(item.get("description") or ""),
                content=str(item.get("content") or item.get("full_description") or ""),
                author=author,
                image_url=str(item.get("image_url") or ""),
            )
        )
    return meta


def fetch_gnews(api_key: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    params = {
        "q": QUERY,
        "lang": "en",
        "max": str(min(PER_API_LIMIT, 100)),
        "from": (now - timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "to": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "apikey": api_key,
    }
    url = "https://gnews.io/api/v4/search?" + urllib.parse.urlencode(params)
    status, payload, raw_hint = http_get_json(url)
    meta: dict[str, Any] = {
        "api": "gnews",
        "request_url": url.split("apikey=", 1)[0] + "apikey=***",
        "http_status": status,
        "errors": [],
        "quota_hint": {},
        "articles": [],
    }
    if status != 200 or not isinstance(payload, dict):
        meta["errors"].append(f"HTTP {status}: {raw_hint[:200]}")
        return meta
    if "errors" in payload:
        meta["errors"].append(str(payload.get("errors")))
        return meta
    meta["quota_hint"] = {"totalArticles": payload.get("totalArticles")}
    articles = payload.get("articles") or []
    if not isinstance(articles, list):
        meta["errors"].append("Unexpected articles shape")
        return meta
    for item in articles[:PER_API_LIMIT]:
        if not isinstance(item, dict):
            continue
        src = item.get("source") if isinstance(item.get("source"), dict) else {}
        meta["articles"].append(
            build_article(
                "gnews",
                title=str(item.get("title") or ""),
                url=str(item.get("url") or ""),
                source_name=str(src.get("name") or ""),
                published_at=str(item.get("publishedAt") or ""),
                language="en",
                description=str(item.get("description") or ""),
                content=str(item.get("content") or ""),
                image_url=str(item.get("image") or ""),
            )
        )
    return meta


def fetch_worldnews(api_key: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    params = {
        "api-key": api_key,
        "text": QUERY,
        "language": "en",
        "number": str(min(PER_API_LIMIT, 100)),
        "earliest-publish-date": (now - timedelta(hours=48)).strftime("%Y-%m-%d"),
        "latest-publish-date": now.strftime("%Y-%m-%d"),
        "sort": "publish-time",
        "sort-direction": "desc",
    }
    url = "https://api.worldnewsapi.com/search-news?" + urllib.parse.urlencode(params)
    status, payload, raw_hint = http_get_json(url)
    meta: dict[str, Any] = {
        "api": "worldnews",
        "request_url": url.split("api-key=", 1)[0] + "api-key=***",
        "http_status": status,
        "errors": [],
        "quota_hint": {},
        "articles": [],
    }
    if status != 200 or not isinstance(payload, dict):
        meta["errors"].append(f"HTTP {status}: {raw_hint[:200]}")
        return meta
    meta["quota_hint"] = {
        k: payload.get(k) for k in ("available", "offset", "number") if payload.get(k) is not None
    }
    news = payload.get("news") or []
    if not isinstance(news, list):
        meta["errors"].append("Unexpected news shape")
        return meta
    for item in news[:PER_API_LIMIT]:
        if not isinstance(item, dict):
            continue
        authors = item.get("authors")
        author = ", ".join(authors) if isinstance(authors, list) else str(authors or "")
        meta["articles"].append(
            build_article(
                "worldnews",
                title=str(item.get("title") or ""),
                url=str(item.get("url") or ""),
                source_name=str(item.get("source") or item.get("source_name") or ""),
                published_at=str(item.get("publish_date") or item.get("published_at") or ""),
                language=str(item.get("language") or "en"),
                country=str(item.get("source_country") or ""),
                category=str(item.get("category") or ""),
                description=str(item.get("summary") or ""),
                content=str(item.get("text") or item.get("body") or ""),
                author=author,
                image_url=str(item.get("image") or ""),
            )
        )
    return meta


def summarize_api(meta: dict[str, Any], pipeline_urls: set[str]) -> dict[str, Any]:
    articles: list[dict[str, Any]] = meta.get("articles") or []
    content_lens = [int(a.get("content_length") or 0) for a in articles if a.get("content_length")]
    with_content = sum(1 for a in articles if int(a.get("content_length") or 0) > 0)
    full = sum(1 for a in articles if a.get("looks_full_content"))
    truncated = sum(1 for a in articles if a.get("looks_truncated"))
    missing_url = sum(1 for a in articles if not a.get("url"))
    missing_pub = sum(1 for a in articles if not a.get("published_at"))
    in_48h = sum(1 for a in articles if a.get("within_48h"))
    overlap_pipeline = 0
    overlap_urls: set[str] = set()
    for a in articles:
        u = normalize_url(str(a.get("url") or ""))
        if u:
            overlap_urls.add(u)
            if u in pipeline_urls:
                overlap_pipeline += 1
    avg_len = statistics.mean(content_lens) if content_lens else 0
    med_len = statistics.median(content_lens) if content_lens else 0
    rating = "Weak"
    if meta.get("errors"):
        rating = "Weak"
    elif with_content >= 10 and full >= 5 and truncated <= with_content // 2:
        rating = "Good"
    elif with_content >= 5:
        rating = "Medium"
    return {
        "api": meta.get("api"),
        "fetched": len(articles),
        "with_content": with_content,
        "avg_content_length": round(avg_len, 1),
        "median_content_length": round(med_len, 1),
        "looks_full_content": full,
        "looks_truncated": truncated,
        "missing_url": missing_url,
        "missing_published_at": missing_pub,
        "within_48h": in_48h,
        "overlap_with_content_json": overlap_pipeline,
        "unique_urls": len(overlap_urls),
        "errors": meta.get("errors") or [],
        "quota_hint": meta.get("quota_hint") or {},
        "rating": rating,
    }


def rating_label(summary: dict[str, Any]) -> str:
    return str(summary.get("rating") or "Weak")


def sample_lines(articles: list[dict[str, Any]], n: int = 5) -> list[str]:
    lines: list[str] = []
    for a in articles[:n]:
        title = (a.get("title") or "")[:80]
        clen = a.get("content_length")
        flags = []
        if a.get("looks_full_content"):
            flags.append("full?")
        if a.get("looks_truncated"):
            flags.append("truncated")
        if a.get("within_48h"):
            flags.append("48h")
        lines.append(f"- **{title}** — content {clen} chars ({', '.join(flags) or 'n/a'})")
    return lines


def cross_api_url_overlap(all_metas: list[dict[str, Any]]) -> dict[str, int]:
    by_api: dict[str, set[str]] = {}
    for meta in all_metas:
        name = str(meta.get("api") or "")
        by_api[name] = {
            normalize_url(str(a.get("url") or ""))
            for a in (meta.get("articles") or [])
            if a.get("url")
        }
    counts: dict[str, int] = {}
    names = list(by_api.keys())
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            overlap = len(by_api[a] & by_api[b])
            counts[f"{a}_x_{b}"] = overlap
    return counts


def write_samples(meta: dict[str, Any], filename: str) -> None:
    path = OUTPUT_DIR / filename
    payload = {
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "query": QUERY,
        "limit": PER_API_LIMIT,
        "http_status": meta.get("http_status"),
        "errors": meta.get("errors"),
        "quota_hint": meta.get("quota_hint"),
        "articles": meta.get("articles"),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(all_articles: list[dict[str, Any]]) -> None:
    path = OUTPUT_DIR / "api_quality_report.csv"
    fields = [
        "api",
        "title",
        "url",
        "source_name",
        "published_at",
        "published_at_utc",
        "within_48h",
        "language",
        "country",
        "category",
        "description_length",
        "content_length",
        "looks_full_content",
        "looks_truncated",
        "has_paywall_hint",
        "quality_notes",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in all_articles:
            out = dict(row)
            out["quality_notes"] = ";".join(row.get("quality_notes") or [])
            writer.writerow(out)


def write_markdown(
    summaries: list[dict[str, Any]],
    metas: list[dict[str, Any]],
    pipeline_url_count: int,
    cross_overlap: dict[str, int],
) -> None:
    lines: list[str] = [
        "# API Quality Test Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Query: `{QUERY}` · limit {PER_API_LIMIT}/API · English · ~48h window",
        "",
        "## Summary",
        "",
        "| API | fetched | with content | avg len | median len | full? | truncated | missing URL | missing date | in 48h | overlap content.json | errors | rating |",
        "|-----|---------|--------------|---------|------------|-------|-----------|-------------|--------------|--------|----------------------|--------|--------|",
    ]
    for s in summaries:
        err = "; ".join(s.get("errors") or [])[:60] or "—"
        lines.append(
            f"| {s.get('api')} | {s.get('fetched')} | {s.get('with_content')} | "
            f"{s.get('avg_content_length')} | {s.get('median_content_length')} | "
            f"{s.get('looks_full_content')} | {s.get('looks_truncated')} | "
            f"{s.get('missing_url')} | {s.get('missing_published_at')} | "
            f"{s.get('within_48h')} | {s.get('overlap_with_content_json')} | {err} | **{s.get('rating')}** |"
        )
    lines.extend(
        [
            "",
            f"Pipeline baseline: `{pipeline_url_count}` URLs in `content.json` (read-only compare).",
            "",
            "### Cross-API URL overlap",
            "",
        ]
    )
    for key, n in cross_overlap.items():
        lines.append(f"- {key}: **{n}** shared URLs")
    if not cross_overlap:
        lines.append("- (no pairwise overlap computed)")

    sections = {
        "newsdata": "NewsData.io",
        "gnews": "GNews.io",
        "worldnews": "WorldNews API",
    }
    for meta in metas:
        api = str(meta.get("api") or "")
        title = sections.get(api, api)
        articles = meta.get("articles") or []
        s = next((x for x in summaries if x.get("api") == api), {})
        lines.extend(["", f"## {title}", ""])
        if meta.get("errors"):
            lines.append(f"- **Errors:** {'; '.join(meta.get('errors') or [])}")
        if meta.get("quota_hint"):
            lines.append(f"- **Quota/response meta:** `{json.dumps(meta.get('quota_hint'), ensure_ascii=False)}`")
        lines.append(f"- **Rating:** {rating_label(s)}")
        lines.extend(["", "### Sample articles (5)", ""])
        lines.extend(sample_lines(articles) or ["- (none)"])
        strengths: list[str] = []
        weaknesses: list[str] = []
        if s.get("with_content", 0) >= 10:
            strengths.append("Nhiều bài có trường content")
        if s.get("looks_full_content", 0) >= 5:
            strengths.append("Một số bài có vẻ full text")
        if s.get("within_48h", 0) >= 10:
            strengths.append("Đa số bài trong 48h")
        if s.get("looks_truncated", 0) > s.get("with_content", 1) // 2:
            weaknesses.append("Nhiều bài truncated/snippet")
        if s.get("missing_url"):
            weaknesses.append("Thiếu URL")
        if s.get("overlap_with_content_json", 0) > 5:
            weaknesses.append("Trùng URL pipeline hiện tại khá nhiều — giá trị gia tăng thấp")
        if meta.get("errors"):
            weaknesses.append("Lỗi quota/auth/HTTP")
        lines.extend(["", "**Điểm mạnh:**", ""])
        lines.extend([f"- {x}" for x in strengths] or ["- (chưa rõ — xem sample)"])
        lines.extend(["", "**Điểm yếu:**", ""])
        lines.extend([f"- {x}" for x in weaknesses] or ["- (chưa phát hiện rõ)"])
        integrate = "Chưa đáng — fix lỗi/quota trước."
        if s.get("rating") == "Good":
            integrate = "Có thể thử làm **input phụ** (pilot nhỏ, không thay crawl)."
        elif s.get("rating") == "Medium":
            integrate = "Thử **fallback** hoặc enrich metadata; chưa thay full crawl."
        lines.extend(["", f"**Có nên tích hợp?** {integrate}", ""])

    ranked = sorted(
        [s for s in summaries if not s.get("errors")],
        key=lambda x: (x.get("looks_full_content", 0), x.get("with_content", 0)),
        reverse=True,
    )
    lines.extend(
        [
            "",
            "## Final Recommendation",
            "",
        ]
    )
    if ranked:
        first = ranked[0].get("api")
        lines.append(f"- **Thử tích hợp trước:** `{first}` (nếu quota/terms OK).")
        if len(ranked) > 1:
            lines.append(f"- **Fallback:** `{ranked[1].get('api')}` cho headline/metadata.")
        weak = [s.get("api") for s in summaries if s.get("rating") == "Weak"]
        if weak:
            lines.append(f"- **Chưa đáng dùng / cần key trả phí:** {', '.join(str(w) for w in weak)}.")
    else:
        lines.append("- **Không API nào trả dữ liệu usable** trong lần chạy này — kiểm tra key/quota.")
    lines.extend(
        [
            "- **Gemini full-content input:** chỉ nên dùng API có `looks_full_content` cao và terms cho phép lưu/republish body.",
            "- **Bản quyền/terms:** NewsData/GNews/WorldNews thường cấp metadata hoặc excerpt; full text có thể bị giới hạn plan — đọc ToS trước khi đưa vào sản phẩm công khai.",
            "",
            "_Standalone test — chưa tích hợp LeonQuant pipeline._",
        ]
    )
    (OUTPUT_DIR / "api_quality_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    env = load_dotenv(ENV_EXAMPLE)
    env.update(load_dotenv(ENV_FILE))
    keys = {
        "newsdata": (env.get("NEWSDATA_API_KEY") or "").strip(),
        "gnews": (env.get("GNEWS_API_KEY") or "").strip(),
        "worldnews": (env.get("WORLDNEWS_API_KEY") or "").strip(),
    }
    pipeline_urls = load_existing_pipeline_urls()
    print(f"Query: {QUERY!r} · limit {PER_API_LIMIT}/API")
    print(f"Pipeline URL baseline (content.json): {len(pipeline_urls)} URLs")

    fetchers = {
        "newsdata": fetch_newsdata,
        "gnews": fetch_gnews,
        "worldnews": fetch_worldnews,
    }
    metas: list[dict[str, Any]] = []
    all_articles: list[dict[str, Any]] = []

    for name, fn in fetchers.items():
        key = keys[name]
        if not key or key.lower().startswith("your-"):
            meta = {
                "api": name,
                "http_status": 0,
                "errors": ["Missing or placeholder API key in .env"],
                "quota_hint": {},
                "articles": [],
            }
            print(f"[{name}] SKIP — no API key")
        else:
            print(f"[{name}] Fetching…")
            meta = fn(key)
            n = len(meta.get("articles") or [])
            err = meta.get("errors") or []
            print(f"[{name}] Got {n} articles" + (f" · ERR: {err[0][:80]}" if err else ""))
        metas.append(meta)
        all_articles.extend(meta.get("articles") or [])
        write_samples(meta, f"{name}_sample.json")

    summaries = [summarize_api(m, pipeline_urls) for m in metas]
    cross = cross_api_url_overlap(metas)
    write_csv(all_articles)
    write_markdown(summaries, metas, len(pipeline_urls), cross)

    print(f"\nWrote {OUTPUT_DIR / 'api_quality_report.md'}")
    print(f"Wrote {OUTPUT_DIR / 'api_quality_report.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
