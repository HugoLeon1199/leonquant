#!/usr/bin/env python3
"""
Leon Web Intel — GDELT macro pulse (BigQuery pushdown + lightweight Python post-process).

Architecture: BigQuery filters/joins/classifies ~millions of rows; Python only scores,
clusters, and exports ~150 rows → 15–30 macro events.

Output: market_pulse.json (atomic write via .tmp + replace).
Separate from the 48h crawl + Gemini digest (content.json).
"""

from __future__ import annotations

import argparse
import html
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import google.generativeai as genai
import pandas as pd
import requests
from bs4 import BeautifulSoup
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
from google.oauth2 import service_account
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PROJECT_DIR / "market_pulse.json"
DEFAULT_MAX_BYTES_BILLED = 500_000_000
DEFAULT_JOB_TIMEOUT_MS = 60_000
TARGET_CLUSTER_MIN = 15
TARGET_CLUSTER_MAX = 35
TFIDF_MERGE_THRESHOLD = 0.55
FETCH_TITLE_TIMEOUT = 5
TITLE_UNAVAILABLE = "(Title unavailable)"
HTTP_USER_AGENT = "LeonWebIntel/1.0 (+https://leonquant.com)"
SKIP_ACTOR_VALUES = frozenset({"", "NONE", "NULL", "UNKNOWN", "KHÔNG RÕ", "KHONG RO", "N/A"})
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"
GEMINI_CALL_INTERVAL_SEC = 2.0

LOG = logging.getLogger("leon.web_intel")
_title_cache: dict[str, str] = {}
_content_cache: dict[str, str | None] = {}
_gemini_configured = False

# CRITICAL: query pushdown — do not widen SELECT or remove filters (OOM / billing risk).
GDELT_MACRO_QUERY = """
WITH
  FilteredEvents AS (
    SELECT Actor1Name, Actor2Name, EventRootCode, AvgTone, NumArticles, SOURCEURL
    FROM `gdelt-bq.gdeltv2.events_partitioned`
    WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
    AND NumArticles >= 15
    AND (AvgTone <= -3.0 OR AvgTone >= 3.0)
  ),
  FilteredGKG AS (
    SELECT DocumentIdentifier, REGEXP_REPLACE(V2Organizations, r',?\\d+', '') AS Cong_Ty_Clean,
      CASE
        WHEN REGEXP_CONTAINS(V2Themes, r'ECON|TRADE|FINANCE|CURRENCY|BANK') THEN 'Tài chính - Kinh tế'
        WHEN REGEXP_CONTAINS(V2Themes, r'CRYPTO|BITCOIN|BLOCKCHAIN|DIGITAL_CURRENCY') THEN 'Crypto - Tài sản số'
        WHEN REGEXP_CONTAINS(V2Themes, r'TECH|CYBER|ARTIFICIAL_INTELLIGENCE|INNOVATION') THEN 'Công nghệ - AI'
        WHEN REGEXP_CONTAINS(V2Themes, r'LAW|LEGISLATION|JUSTICE|REGULATION|COURT|ANTITRUST') THEN 'Pháp lý - Quy định'
        WHEN REGEXP_CONTAINS(V2Themes, r'SCIENCE|SPACE|RESEARCH|DISCOVERY') THEN 'Khoa học - Vũ trụ'
        WHEN REGEXP_CONTAINS(V2Themes, r'ENV_|ENERGY|CLIMATE|MINERALS') THEN 'Năng lượng - Môi trường'
        WHEN REGEXP_CONTAINS(V2Themes, r'INFRASTRUCTURE|CONSTRUCTION|REAL_ESTATE|TRANSPORT') THEN 'Hạ tầng - Bất động sản'
        WHEN REGEXP_CONTAINS(V2Themes, r'HEALTH|MEDICAL|DISEASE|PANDEMIC') THEN 'Y tế - Sức khỏe'
        WHEN REGEXP_CONTAINS(V2Themes, r'AGRICULTURE|FOOD_SECURITY|FARMING') THEN 'Nông nghiệp - Lương thực'
        WHEN REGEXP_CONTAINS(V2Themes, r'MILITARY|GOV|POLITICAL|TERROR|ELECTION|CRISIS') THEN 'Chính trị - Xung đột'
        ELSE 'Khác'
      END AS Nhom_Nganh
    FROM `gdelt-bq.gdeltv2.gkg_partitioned`
    WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
    AND V2Organizations IS NOT NULL
  )
SELECT e.Actor1Name AS Doi_Tuong_Chinh, g.Nhom_Nganh, e.AvgTone AS Diem_Cam_Xuc,
       g.Cong_Ty_Clean AS Cac_To_Chuc_Lien_Quan, e.SOURCEURL AS Link_Bai_Bao,
       e.NumArticles AS So_Bao_De_Cap
FROM FilteredEvents AS e
INNER JOIN FilteredGKG AS g ON e.SOURCEURL = g.DocumentIdentifier
WHERE g.Nhom_Nganh != 'Khác'
ORDER BY e.NumArticles DESC
LIMIT 150
""".strip()


# ---------------------------------------------------------------------------
# BigQuery
# ---------------------------------------------------------------------------


def build_query() -> str:
    """Return the optimized GDELT macro SQL (pushdown only — do not alter filters)."""
    return GDELT_MACRO_QUERY


def get_bigquery_client() -> bigquery.Client:
    """Authenticate via GOOGLE_APPLICATION_CREDENTIALS or local credentials.json (dev)."""
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")

    if creds_path and Path(creds_path).is_file():
        credentials = service_account.Credentials.from_service_account_file(creds_path)
        return bigquery.Client(project=project or credentials.project_id, credentials=credentials)

    local = PROJECT_DIR / "credentials.json"
    if local.is_file():
        LOG.warning("Using credentials.json in repo root (dev only).")
        credentials = service_account.Credentials.from_service_account_file(str(local))
        return bigquery.Client(project=project or credentials.project_id, credentials=credentials)

    return bigquery.Client(project=project)


def run_bigquery(
    client: bigquery.Client,
    *,
    job_timeout_ms: int = DEFAULT_JOB_TIMEOUT_MS,
    maximum_bytes_billed: int = DEFAULT_MAX_BYTES_BILLED,
    dry_run: bool = False,
) -> tuple[pd.DataFrame | None, dict[str, Any]]:
    """Execute macro query; returns small dataframe (~150 rows) or None on dry-run."""
    sql = build_query()
    job_config = bigquery.QueryJobConfig(
        job_timeout_ms=job_timeout_ms,
        maximum_bytes_billed=maximum_bytes_billed,
        dry_run=dry_run,
        use_query_cache=not dry_run,
    )
    meta: dict[str, Any] = {"dry_run": dry_run, "job_timeout_ms": job_timeout_ms}

    try:
        job = client.query(sql, job_config=job_config)
        if dry_run:
            meta["total_bytes_processed"] = job.total_bytes_processed
            meta["total_gb"] = round((job.total_bytes_processed or 0) / 1e9, 4)
            LOG.info("Dry-run estimate: ~%s GB", meta["total_gb"])
            return None, meta

        df = job.result(timeout=job_timeout_ms / 1000).to_dataframe()
        meta["bytes_processed"] = job.total_bytes_processed
        meta["row_count"] = len(df)
        bp = meta.get("bytes_processed") or 0
        LOG.info("BigQuery returned %s rows (~%.3f GB processed)", len(df), bp / 1e9)
        return df, meta
    except GoogleCloudError as exc:
        LOG.error("BigQuery job failed: %s", exc)
        raise
    except Exception as exc:
        LOG.error("BigQuery request error (timeout/network): %s", exc)
        raise


# ---------------------------------------------------------------------------
# Cleaning (small dataframe only)
# ---------------------------------------------------------------------------


def parse_entity_list(raw: Any, *, limit: int = 3) -> list[str]:
    """Split semicolon-separated org string; return top N unique entities."""
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return []
    text = str(raw).strip()
    if not text:
        return []
    parts = [re.sub(r"\s+", " ", p.strip()) for p in text.split(";") if p.strip()]
    out: list[str] = []
    for p in parts:
        key = p.upper()
        if key not in {x.upper() for x in out}:
            out.append(p[:120])
        if len(out) >= limit:
            break
    return out


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Dedupe URLs, normalize actors, parse entity lists — no heavy regex on raw GDELT."""
    if df.empty:
        return df

    out = df.copy()
    out.columns = [str(c) for c in out.columns]
    out["Link_Bai_Bao"] = out["Link_Bai_Bao"].astype(str).str.strip()
    out = out[out["Link_Bai_Bao"].str.startswith("http", na=False)]
    out = out.drop_duplicates(subset=["Link_Bai_Bao"], keep="first")

    out["Doi_Tuong_Chinh"] = out["Doi_Tuong_Chinh"].fillna("").astype(str).str.strip()
    out["Nhom_Nganh"] = out["Nhom_Nganh"].fillna("").astype(str).str.strip()
    out["Diem_Cam_Xuc"] = pd.to_numeric(out["Diem_Cam_Xuc"], errors="coerce").fillna(0.0)
    out["entities_clean"] = out["Cac_To_Chuc_Lien_Quan"].map(lambda x: parse_entity_list(x, limit=3))
    out["rank"] = range(len(out))
    return out.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Scrape + Gemini (Vietnamese headlines — top URL per cluster)
# ---------------------------------------------------------------------------


def _configure_gemini() -> bool:
    global _gemini_configured
    if _gemini_configured:
        return True
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        LOG.warning("GEMINI_API_KEY missing — skipping Vietnamese AI enrichment")
        return False
    genai.configure(api_key=api_key)
    _gemini_configured = True
    return True


def extract_web_content(url: str, *, timeout: int = FETCH_TITLE_TIMEOUT) -> str | None:
    """Scrape title + opening paragraphs for Gemini context."""
    url = str(url or "").strip()
    if not url.startswith("http"):
        return None
    if url in _content_cache:
        return _content_cache[url]

    snippet: str | None = None
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": HTTP_USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
            allow_redirects=True,
        )
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            title = soup.title.get_text(strip=True) if soup.title else ""
            paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")[:3]]
            content_text = " ".join(paragraphs)
            snippet = f"Title: {title}\nContent Snippet: {content_text[:1000]}"
    except Exception as exc:
        LOG.debug("extract_web_content failed %s: %s", url[:96], exc)

    _content_cache[url] = snippet
    return snippet


def fetch_title(url: str, *, timeout: int = FETCH_TITLE_TIMEOUT) -> str:
    """Fetch HTML <title> for a source URL; cached per run."""
    url = str(url or "").strip()
    if not url.startswith("http"):
        return TITLE_UNAVAILABLE
    if url in _title_cache:
        return _title_cache[url]

    title = TITLE_UNAVAILABLE
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": HTTP_USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
            allow_redirects=True,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "html.parser")
        tag = soup.find("title")
        raw = tag.get_text(strip=True) if tag else ""
        cleaned = html.unescape(re.sub(r"\s+", " ", raw)).strip()
        if cleaned:
            title = cleaned[:300]
    except Exception as exc:
        LOG.debug("fetch_title failed %s: %s", url[:96], exc)

    _title_cache[url] = title
    return title


def _normalize_actor_name(raw: Any) -> str:
    name = re.sub(r"\s+", " ", str(raw or "").strip())
    if not name or name.upper() in SKIP_ACTOR_VALUES:
        return ""
    return name[:120]


def _merge_entity_tags(actors: list[str], organizations: list[str], *, limit: int = 8) -> list[str]:
    """Actors (GDELT) + orgs (GKG) as display tags — not used as headline."""
    out: list[str] = []
    seen: set[str] = set()
    for item in [*actors, *organizations]:
        text = re.sub(r"\s+", " ", str(item or "").strip())
        if not text:
            continue
        key = text.upper()
        if key in seen:
            continue
        seen.add(key)
        out.append(text[:120])
        if len(out) >= limit:
            break
    return out


def _primary_actor_label(event: dict[str, Any]) -> str:
    for item in event.get("entities") or []:
        text = str(item or "").strip()
        if text and text.upper() not in SKIP_ACTOR_VALUES:
            return text
    return str(event.get("sector") or "Sự kiện")


def _parse_gemini_enrichment(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        upper = line.upper()
        if upper.startswith("TITLE:"):
            result["title_vi"] = line.split(":", 1)[1].strip()
        elif upper.startswith("SUMMARY:"):
            result["summary_vi"] = line.split(":", 1)[1].strip()
        elif upper.startswith("ENTITIES:"):
            raw = line.split(":", 1)[1].strip()
            if raw.lower() in ("none", "không", "khong", "n/a", "-", "không có", "khong co"):
                result["entities"] = []
            else:
                result["entities"] = [e.strip() for e in raw.split(",") if e.strip()]
    return result


def enrich_event_with_gemini(sector: str, primary_actor: str, raw_content: str | None) -> dict[str, Any] | None:
    """Gemini: Vietnamese headline + multi-sector summary + entities (only if cited)."""
    if not raw_content or not _configure_gemini():
        return None

    model_name = os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL
    model = genai.GenerativeModel(model_name)
    prompt = f"""
You are an expert macro analyst covering finance, geopolitics, technology, health, energy, law, and conflict — writing in professional Vietnamese.

GDELT context (for reference only; do not invent facts beyond the article):
- Sector tag from data pipeline: {sector}
- Primary actor tag: {primary_actor}

Raw article excerpt:
{raw_content}

Rules:
- Use ONLY facts present in the excerpt. Do not fabricate numbers, countries, or tickers.
- Do NOT invent stock tickers or company names unless they appear in the excerpt.
- Multi-sector lens: explain why this matters across regions/industries when relevant.

Your tasks:
1. TITLE: One sharp professional headline in Vietnamese (max 18 words).
2. SUMMARY: 1–2 sentences in Vietnamese covering:
   - What happened
   - Who is affected (countries, institutions, markets)
   - Why it is notable now
   - Which sector/industry it relates to (may echo or refine: {sector})
   - If the excerpt hints at market or asset impact (stocks, oil, FX, crypto, bonds), mention lightly in one short clause; otherwise omit.
3. ENTITIES: Up to 3 organizations, institutions, or tickers EXPLICITLY mentioned in the excerpt. If none, write: ENTITIES: none

Respond STRICTLY in this format (plain text, no markdown):
TITLE: [Vietnamese headline]
SUMMARY: [1-2 Vietnamese sentences]
ENTITIES: [Name1, Name2, Name3] OR none
""".strip()

    try:
        response = model.generate_content(prompt)
        parsed = _parse_gemini_enrichment(response.text or "")
        return parsed if parsed.get("title_vi") else None
    except Exception as exc:
        LOG.warning("Gemini enrichment failed: %s", exc)
        return None


def _merge_entity_lists(*lists: list[str], limit: int = 8) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for lst in lists:
        for item in lst or []:
            text = re.sub(r"\s+", " ", str(item or "").strip())
            if not text:
                continue
            key = text.upper()
            if key in seen:
                continue
            seen.add(key)
            out.append(text[:120])
            if len(out) >= limit:
                return out
    return out


def enrich_events_for_web(events: list[dict[str, Any]], *, use_gemini: bool = True) -> list[dict[str, Any]]:
    """Scrape source URL; optionally Gemini Vietnamese title/summary."""
    for i, ev in enumerate(events, start=1):
        sources = ev.get("sources") or []
        top_url = sources[0] if sources else ""
        sector = str(ev.get("sector") or "")
        actor = _primary_actor_label(ev)
        existing_entities = list(ev.get("entities") or [])

        if not top_url:
            ev["title"] = TITLE_UNAVAILABLE
            ev["summary"] = "Chưa có nguồn tin để tóm tắt."
            continue

        LOG.info("Enriching event %s/%s: %s", i, len(events), top_url[:80])
        raw_content = extract_web_content(top_url)
        ai_data = None
        if use_gemini:
            ai_data = enrich_event_with_gemini(sector, actor, raw_content)
            if i < len(events):
                time.sleep(GEMINI_CALL_INTERVAL_SEC)

        if ai_data:
            ev["title"] = ai_data.get("title_vi") or TITLE_UNAVAILABLE
            ev["summary"] = ai_data.get("summary_vi") or "Nhấp nguồn để xem chi tiết."
            ev["entities"] = _merge_entity_lists(
                ai_data.get("entities") or [],
                existing_entities,
            )
        else:
            scraped_title = TITLE_UNAVAILABLE
            if raw_content and raw_content.startswith("Title:"):
                scraped_title = raw_content.split("\n", 1)[0].replace("Title:", "").strip() or TITLE_UNAVAILABLE
            if scraped_title == TITLE_UNAVAILABLE:
                scraped_title = fetch_title(top_url)
            ev["title"] = scraped_title
            ev["summary"] = (
                f"Tin nóng nhóm {sector}: {actor}. "
                "Nhấp link nguồn để đọc bài gốc."
            )
            ev["entities"] = existing_entities

    return events


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def impact_score(rank: int, tone: float, *, max_rank: int = 150) -> int:
    """0–100: higher BQ rank (lower index) + more extreme sentiment."""
    rank_part = ((max_rank - min(rank, max_rank - 1)) / max_rank) * 50.0
    tone_part = (min(abs(float(tone)), 25.0) / 25.0) * 50.0
    return int(round(min(100.0, max(0.0, rank_part + tone_part))))


# ---------------------------------------------------------------------------
# Clustering (lightweight — ~150 rows max)
# ---------------------------------------------------------------------------


@dataclass
class MacroCluster:
    sector: str
    primary_actor: str
    rows: list[dict[str, Any]] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    actors: list[str] = field(default_factory=list)
    related_entities: list[str] = field(default_factory=list)
    tones: list[float] = field(default_factory=list)
    ranks: list[int] = field(default_factory=list)
    article_mentions: list[int] = field(default_factory=list)

    def cluster_text(self) -> str:
        ents = " ".join(self.related_entities)
        actors = " ".join(self.actors)
        return f"{actors} {self.sector} {ents}".strip()

    def to_event(self) -> dict[str, Any]:
        tone_avg = sum(self.tones) / len(self.tones) if self.tones else 0.0
        best_rank = min(self.ranks) if self.ranks else 149
        score = impact_score(best_rank, tone_avg)
        entity_tags = _merge_entity_tags(self.actors, self.related_entities)
        # GDELT NumArticles = global media volume for that event row (not our scrape count).
        if self.article_mentions:
            coverage = max(self.article_mentions)
        else:
            coverage = max(len(self.sources), 1)
        if tone_avg >= 2.0:
            sentiment_label = "Tích cực"
        elif tone_avg <= -2.0:
            sentiment_label = "Tiêu cực"
        else:
            sentiment_label = "Trung tính"
        return {
            "title": "",
            "summary": "",
            "sector": self.sector,
            "impact_score": score,
            "sentiment_tone": round(tone_avg, 2),
            "sentiment_label": sentiment_label,
            "article_mentions": int(coverage),
            "entities": entity_tags,
            "sources": self.sources[:10],
        }


def _actor_sector_key(actor: str, sector: str) -> tuple[str, str]:
    return (actor.strip().upper() or "UNKNOWN", sector.strip())


def _merge_cluster_dicts(a: MacroCluster, b: MacroCluster) -> MacroCluster:
    for row in b.rows:
        a.rows.append(row)
    for url in b.sources:
        if url not in a.sources:
            a.sources.append(url)
    for ent in b.related_entities:
        if ent.upper() not in {x.upper() for x in a.related_entities}:
            a.related_entities.append(ent)
    a.related_entities = a.related_entities[:3]
    for actor in b.actors:
        if actor.upper() not in {x.upper() for x in a.actors}:
            a.actors.append(actor)
    a.tones.extend(b.tones)
    a.ranks.extend(b.ranks)
    a.article_mentions.extend(b.article_mentions)
    return a


def _merge_by_tfidf(clusters: list[MacroCluster], threshold: float = TFIDF_MERGE_THRESHOLD) -> list[MacroCluster]:
    """Merge similar clusters until count <= TARGET_CLUSTER_MAX."""
    if len(clusters) <= TARGET_CLUSTER_MAX:
        return clusters

    texts = [c.cluster_text() or c.sector for c in clusters]
    vec = TfidfVectorizer(min_df=1, ngram_range=(1, 2))
    matrix = vec.fit_transform(texts)
    sim = cosine_similarity(matrix)

    merged = True
    while merged and len(clusters) > TARGET_CLUSTER_MAX:
        merged = False
        best_i, best_j, best_sim = -1, -1, threshold
        n = len(clusters)
        for i in range(n):
            for j in range(i + 1, n):
                if sim[i, j] > best_sim:
                    best_sim = sim[i, j]
                    best_i, best_j = i, j
        if best_i >= 0:
            clusters[best_i] = _merge_cluster_dicts(clusters[best_i], clusters[best_j])
            del clusters[best_j]
            merged = True
            texts = [c.cluster_text() or c.sector for c in clusters]
            matrix = vec.fit_transform(texts)
            sim = cosine_similarity(matrix)
    return clusters


def cluster_events(df: pd.DataFrame) -> list[dict[str, Any]]:
    """
    Group ~150 articles into 15–30 macro events.
    Primary key: Doi_Tuong_Chinh + Nhom_Nganh; optional TF-IDF merge if too many groups.
    """
    if df.empty:
        return []

    buckets: dict[tuple[str, str], MacroCluster] = {}
    for _, row in df.iterrows():
        actor = _normalize_actor_name(row["Doi_Tuong_Chinh"]) or "UNKNOWN"
        sector = str(row["Nhom_Nganh"]).strip()
        key = _actor_sector_key(actor, sector)
        url = str(row["Link_Bai_Bao"]).strip()
        ents = list(row.get("entities_clean") or [])
        tone = float(row["Diem_Cam_Xuc"])
        rank = int(row.get("rank", 0))
        actor_display = _normalize_actor_name(row["Doi_Tuong_Chinh"])

        if key not in buckets:
            buckets[key] = MacroCluster(sector=sector, primary_actor=actor_display or actor)
        cl = buckets[key]
        cl.rows.append(row.to_dict())
        if url and url not in cl.sources:
            cl.sources.append(url)
        if actor_display and actor_display.upper() not in {x.upper() for x in cl.actors}:
            cl.actors.append(actor_display)
        for e in ents:
            if e.upper() not in {x.upper() for x in cl.related_entities}:
                cl.related_entities.append(e)
        cl.related_entities = cl.related_entities[:3]
        cl.tones.append(tone)
        cl.ranks.append(rank)
        try:
            mentions = int(row.get("So_Bao_De_Cap") or 0)
        except (TypeError, ValueError):
            mentions = 0
        if mentions > 0:
            cl.article_mentions.append(mentions)

    clusters = list(buckets.values())
    LOG.info("Actor+sector buckets: %s", len(clusters))

    if len(clusters) > TARGET_CLUSTER_MAX:
        clusters = _merge_by_tfidf(clusters)
        LOG.info("After TF-IDF merge: %s clusters", len(clusters))

    events = [c.to_event() for c in clusters]
    events.sort(key=lambda e: e["impact_score"], reverse=True)

    if len(events) > TARGET_CLUSTER_MAX:
        events = events[:TARGET_CLUSTER_MAX]
    return events


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def build_feed_urls(cleaned: pd.DataFrame, events: list[dict[str, Any]]) -> list[str]:
    """All source URLs from this pipeline run (BQ rows + clustered sources)."""
    seen: set[str] = set()
    out: list[str] = []
    if not cleaned.empty and "Link_Bai_Bao" in cleaned.columns:
        for raw in cleaned["Link_Bai_Bao"]:
            url = str(raw or "").strip()
            if url.startswith("http") and url not in seen:
                seen.add(url)
                out.append(url)
    for ev in events:
        for url in ev.get("sources") or []:
            u = str(url or "").strip()
            if u.startswith("http") and u not in seen:
                seen.add(u)
                out.append(u)
    return out


def build_payload(
    events: list[dict[str, Any]],
    *,
    query_meta: dict[str, Any],
    live_feed_urls: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_clusters": len(events),
        "query_meta": query_meta,
        "live_feed_urls": live_feed_urls or [],
        "events": events,
    }


def atomic_export_json(payload: dict[str, Any], output_path: Path) -> Path:
    """Write .tmp.json then os.replace — safe for concurrent web reads."""
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_suffix(".tmp.json")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(output_path)
    LOG.info("Wrote %s (%s clusters)", output_path, payload.get("total_clusters", 0))
    return output_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def load_dotenv() -> None:
    """Load PROJECT_DIR/.env into os.environ (only unset keys)."""
    env_path = PROJECT_DIR / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val
    creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if creds and not Path(creds).is_absolute():
        resolved = (PROJECT_DIR / creds).resolve()
        if resolved.is_file():
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(resolved)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Leon Web Intel — GDELT macro pulse (BigQuery pushdown)")
    p.add_argument(
        "--output",
        type=Path,
        default=Path(os.environ.get("LEON_PULSE_OUTPUT", DEFAULT_OUTPUT)),
        help="Output JSON path (default: market_pulse.json)",
    )
    p.add_argument("--dry-run", action="store_true", help="Estimate bytes billed only")
    p.add_argument("--job-timeout-ms", type=int, default=DEFAULT_JOB_TIMEOUT_MS)
    p.add_argument("--max-bytes-billed", type=int, default=DEFAULT_MAX_BYTES_BILLED)
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument(
        "--no-gemini",
        action="store_true",
        help="Skip Gemini; use scraped HTML title only",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    output: Path = args.output
    LOG.info("Leon Web Intel → %s (dry_run=%s)", output, args.dry_run)

    try:
        client = get_bigquery_client()
    except Exception as exc:
        LOG.error("BigQuery client setup failed: %s", exc)
        return 1

    try:
        df, meta = run_bigquery(
            client,
            job_timeout_ms=args.job_timeout_ms,
            maximum_bytes_billed=args.max_bytes_billed,
            dry_run=args.dry_run,
        )
    except (GoogleCloudError, Exception):
        LOG.error("Keeping existing %s if present", output)
        return 1

    if args.dry_run:
        return 0

    if df is None or df.empty:
        LOG.warning("No rows returned; not overwriting %s", output)
        return 0

    cleaned = clean_dataframe(df)
    events = cluster_events(cleaned)
    if events:
        use_gemini = not args.no_gemini
        LOG.info(
            "Web enrichment for %s events (gemini=%s, timeout=%ss)",
            len(events),
            use_gemini,
            FETCH_TITLE_TIMEOUT,
        )
        events = enrich_events_for_web(events, use_gemini=use_gemini)
    feed_urls = build_feed_urls(cleaned, events)
    payload = build_payload(events, query_meta=meta, live_feed_urls=feed_urls)
    try:
        atomic_export_json(payload, output)
        # Mirror for GitHub Pages static path
        web_mirror = PROJECT_DIR / "web" / "market_pulse.json"
        if output.resolve() != web_mirror.resolve():
            atomic_export_json(payload, web_mirror)
    except OSError as exc:
        LOG.error("Export failed: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
