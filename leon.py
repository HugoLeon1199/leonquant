#!/usr/bin/env python3
"""
Leon Web Intel — GDELT event-centric live pulse (BigQuery pushdown + Gemini summaries).

Architecture: events_partitioned (hot events) + eventmentions_partitioned (real URLs per
GlobalEventID) + gkg_partitioned (sector/entities). Python exports 10–20 event cards only.

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
from urllib.parse import urlparse

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PROJECT_DIR / "market_pulse.json"
DEFAULT_MAX_BYTES_BILLED = 500_000_000
DEFAULT_JOB_TIMEOUT_MS = 60_000
TARGET_HOT_EVENTS = 20
MAX_MENTIONS_PER_EVENT = 15
DISPLAY_SOURCES_MAX = 5
PULSE_SCHEMA_VERSION = "event-centric-v1"
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
# Sources come ONLY from eventmentions_partitioned (no sector-based URL guessing).
_GKG_SECTOR_CASE = """
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
      END
"""

GDELT_MACRO_QUERY = f"""
WITH
  FilteredEvents AS (
    SELECT
      GLOBALEVENTID,
      Actor1Name,
      AvgTone,
      NumArticles,
      SOURCEURL
    FROM `gdelt-bq.gdeltv2.events_partitioned`
    WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
      AND NumArticles >= 40
      AND (AvgTone <= -4.0 OR AvgTone >= 4.0)
      AND SOURCEURL IS NOT NULL
      AND SOURCEURL != ''
  ),
  TopEvents AS (
    SELECT GLOBALEVENTID, MAX(NumArticles) AS num_articles
    FROM FilteredEvents
    GROUP BY GLOBALEVENTID
    ORDER BY num_articles DESC
    LIMIT {TARGET_HOT_EVENTS}
  ),
  EventReps AS (
    SELECT
      f.GLOBALEVENTID,
      f.Actor1Name,
      f.AvgTone,
      f.NumArticles,
      f.SOURCEURL
    FROM FilteredEvents AS f
    INNER JOIN TopEvents AS t ON f.GLOBALEVENTID = t.GLOBALEVENTID
    QUALIFY ROW_NUMBER() OVER (
      PARTITION BY f.GLOBALEVENTID
      ORDER BY f.NumArticles DESC, f.SOURCEURL
    ) = 1
  ),
  MentionDedup AS (
    SELECT
      m.GLOBALEVENTID,
      m.MentionIdentifier,
      ANY_VALUE(m.MentionSourceName) AS MentionSourceName,
      MAX(m.MentionTimeDate) AS latest_mention
    FROM `gdelt-bq.gdeltv2.eventmentions_partitioned` AS m
    INNER JOIN TopEvents AS t ON m.GLOBALEVENTID = t.GLOBALEVENTID
    WHERE m._PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
      AND m.MentionIdentifier IS NOT NULL
      AND STARTS_WITH(m.MentionIdentifier, 'http')
    GROUP BY m.GLOBALEVENTID, m.MentionIdentifier
  ),
  MentionsRanked AS (
    SELECT
      GLOBALEVENTID,
      MentionIdentifier,
      MentionSourceName,
      ROW_NUMBER() OVER (
        PARTITION BY GLOBALEVENTID
        ORDER BY latest_mention DESC, MentionIdentifier
      ) AS mention_rank
    FROM MentionDedup
  ),
  MentionAgg AS (
    SELECT
      GLOBALEVENTID,
      ARRAY_AGG(
        STRUCT(MentionIdentifier AS url, MentionSourceName AS name)
        ORDER BY mention_rank
        LIMIT {MAX_MENTIONS_PER_EVENT}
      ) AS mention_sources
    FROM MentionsRanked
    WHERE mention_rank <= {MAX_MENTIONS_PER_EVENT}
    GROUP BY GLOBALEVENTID
  ),
  FilteredGKG AS (
    SELECT
      DocumentIdentifier,
      V2Themes,
      REGEXP_REPLACE(V2Organizations, r',?\\d+', '') AS Cong_Ty_Clean,
      {_GKG_SECTOR_CASE.strip()} AS Nhom_Nganh
    FROM `gdelt-bq.gdeltv2.gkg_partitioned`
    WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
      AND V2Organizations IS NOT NULL
  )
SELECT
  r.GLOBALEVENTID AS GlobalEventID,
  r.Actor1Name AS Doi_Tuong_Chinh,
  g.Nhom_Nganh,
  g.V2Themes,
  r.AvgTone AS Diem_Cam_Xuc,
  g.Cong_Ty_Clean AS Cac_To_Chuc_Lien_Quan,
  r.SOURCEURL AS Link_Bai_Bao,
  r.NumArticles AS So_Bao_De_Cap,
  COALESCE(m.mention_sources, ARRAY<STRUCT<url STRING, name STRING>>[]) AS Mention_Sources
FROM EventReps AS r
INNER JOIN FilteredGKG AS g ON r.SOURCEURL = g.DocumentIdentifier
LEFT JOIN MentionAgg AS m ON r.GLOBALEVENTID = m.GLOBALEVENTID
WHERE g.Nhom_Nganh != 'Khác'
ORDER BY r.NumArticles DESC
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


SECTOR_THEME_RULES: list[tuple[str, str]] = [
    (r"ECON|TRADE|FINANCE|CURRENCY|BANK", "Tài chính - Kinh tế"),
    (r"CRYPTO|BITCOIN|BLOCKCHAIN|DIGITAL_CURRENCY", "Crypto - Tài sản số"),
    (r"TECH|CYBER|ARTIFICIAL_INTELLIGENCE|INNOVATION", "Công nghệ - AI"),
    (r"LAW|LEGISLATION|JUSTICE|REGULATION|COURT|ANTITRUST", "Pháp lý - Quy định"),
    (r"SCIENCE|SPACE|RESEARCH|DISCOVERY", "Khoa học - Vũ trụ"),
    (r"ENV_|ENERGY|CLIMATE|MINERALS", "Năng lượng - Môi trường"),
    (r"INFRASTRUCTURE|CONSTRUCTION|REAL_ESTATE|TRANSPORT", "Hạ tầng - Bất động sản"),
    (r"HEALTH|MEDICAL|DISEASE|PANDEMIC", "Y tế - Sức khỏe"),
    (r"AGRICULTURE|FOOD_SECURITY|FARMING", "Nông nghiệp - Lương thực"),
    (r"MILITARY|GOV|POLITICAL|TERROR|ELECTION|CRISIS", "Chính trị - Xung đột"),
]


def _iter_raw_sequence(val: Any) -> list[Any]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return []
    if hasattr(val, "tolist") and not isinstance(val, (str, bytes)):
        return list(val.tolist())
    if isinstance(val, (list, tuple)):
        return list(val)
    s = str(val).strip()
    if not s:
        return []
    if s.startswith("["):
        try:
            parsed = json.loads(s)
            return parsed if isinstance(parsed, list) else [parsed]
        except json.JSONDecodeError:
            return [s]
    return [s]


def _source_label_from_url(url: str, mention_name: str = "") -> str:
    name = re.sub(r"\s+", " ", str(mention_name or "").strip())
    if name and name.lower() not in ("none", "null", "unknown"):
        return name[:80]
    host = urlparse(url).netloc.lower().replace("www.", "")
    if not host:
        return "Nguồn"
    base = host.split(".")[0]
    return base[:1].upper() + base[1:] if base else host


def _source_record(url: str, mention_name: str = "") -> dict[str, str]:
    u = str(url or "").strip()
    host = urlparse(u).netloc.lower().replace("www.", "")
    return {
        "url": u,
        "name": _source_label_from_url(u, mention_name),
        "domain": host,
    }


def _parse_mention_sources(val: Any) -> list[dict[str, str]]:
    """Parse EventMentions ARRAY<STRUCT<url,name>> from BigQuery."""
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in _iter_raw_sequence(val):
        if isinstance(item, dict):
            url = str(item.get("url") or item.get("MentionIdentifier") or "").strip()
            name = str(item.get("name") or item.get("MentionSourceName") or "").strip()
        else:
            url = str(item).strip()
            name = ""
        if not url.startswith("http") or url in seen:
            continue
        seen.add(url)
        out.append(_source_record(url, name))
        if len(out) >= MAX_MENTIONS_PER_EVENT:
            break
    return out


def _sectors_display(primary: str, v2themes: str) -> str:
    """Primary GKG sector + optional secondary from themes (e.g. Chính trị / Năng lượng)."""
    primary = str(primary or "").strip()
    themes = str(v2themes or "")
    matched: list[str] = []
    if primary and primary != "Khác":
        matched.append(primary)
    for pattern, label in SECTOR_THEME_RULES:
        if label in matched or label == "Khác":
            continue
        if re.search(pattern, themes, flags=re.IGNORECASE):
            matched.append(label)
        if len(matched) >= 2:
            break
    if not matched:
        return primary or "Khác"
    return " / ".join(matched[:2])


def sentiment_label_vi(tone: float) -> str:
    t = float(tone)
    if t >= 4.0:
        return "Tích cực mạnh"
    if t >= 2.0:
        return "Tích cực"
    if t <= -4.0:
        return "Tiêu cực mạnh"
    if t <= -2.0:
        return "Tiêu cực"
    return "Trung tính"


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """One row per GlobalEventID; mention sources parsed from EventMentions only."""
    if df.empty:
        return df

    out = df.copy()
    out.columns = [str(c) for c in out.columns]
    out["Link_Bai_Bao"] = out["Link_Bai_Bao"].astype(str).str.strip()
    out = out[out["Link_Bai_Bao"].str.startswith("http", na=False)]

    col_mentions = "Mention_Sources" if "Mention_Sources" in out.columns else "Danh_Sach_Lien_Ket"
    out["mention_sources"] = out[col_mentions].map(_parse_mention_sources)

    id_col = "GlobalEventID" if "GlobalEventID" in out.columns else "Ma_Su_Kien"
    if id_col in out.columns:
        out = out.drop_duplicates(subset=[id_col], keep="first")

    out["Doi_Tuong_Chinh"] = out["Doi_Tuong_Chinh"].fillna("").astype(str).str.strip()
    out["Nhom_Nganh"] = out["Nhom_Nganh"].fillna("").astype(str).str.strip()
    if "V2Themes" not in out.columns:
        out["V2Themes"] = ""
    out["Diem_Cam_Xuc"] = pd.to_numeric(out["Diem_Cam_Xuc"], errors="coerce").fillna(0.0)
    out["entities_clean"] = out["Cac_To_Chuc_Lien_Quan"].map(lambda x: parse_entity_list(x, limit=6))
    out["sector_display"] = out.apply(
        lambda r: _sectors_display(str(r["Nhom_Nganh"]), str(r.get("V2Themes") or "")),
        axis=1,
    )
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
        elif upper.startswith("IMPORTANCE:"):
            result["importance_reason"] = line.split(":", 1)[1].strip()
        elif upper.startswith("ENTITIES:"):
            raw = line.split(":", 1)[1].strip()
            if raw.lower() in ("none", "không", "khong", "n/a", "-", "không có", "khong co"):
                result["entities"] = []
            else:
                result["entities"] = [e.strip() for e in raw.split(",") if e.strip()]
    return result


def enrich_event_with_gemini(
    sector: str,
    primary_actor: str,
    raw_content: str | None,
    *,
    num_articles: int,
    source_count: int,
    source_names: list[str],
) -> dict[str, Any] | None:
    """Gemini: Vietnamese title/summary/importance after EventMentions sources are fixed."""
    if not raw_content or not _configure_gemini():
        return None

    model_name = os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL
    model = genai.GenerativeModel(model_name)
    outlets = ", ".join(source_names[:8]) if source_names else "N/A"
    prompt = f"""
You are an expert macro analyst — writing in professional Vietnamese.

GDELT event context (reference only; do not invent beyond excerpt):
- Sector: {sector}
- Actor tag: {primary_actor}
- GDELT coverage (NumArticles): {num_articles}
- Distinct mention sources in pipeline: {source_count}
- Sample outlets: {outlets}

Raw article excerpt (representative mention):
{raw_content}

Rules:
- Use ONLY facts in the excerpt. No fabricated numbers, countries, or tickers.
- IMPORTANCE must explain why this event ranks high in global news volume (use coverage/source hints above).

Tasks:
1. TITLE: One sharp headline in Vietnamese (max 18 words).
2. SUMMARY: 1–2 sentences — what happened, who is affected, market/geopolitical relevance.
3. IMPORTANCE: One short sentence in Vietnamese — why this is among the hottest global events now.
4. ENTITIES: Up to 5 actors/orgs/countries EXPLICIT in excerpt, comma-separated; or ENTITIES: none

Format (plain text, no markdown):
TITLE: ...
SUMMARY: ...
IMPORTANCE: ...
ENTITIES: ... OR none
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
    """Scrape top EventMention URL; Gemini fills title_vi / summary_vi / importance_reason."""
    for i, ev in enumerate(events, start=1):
        sources: list[dict[str, str]] = list(ev.get("sources") or [])
        top_url = sources[0].get("url", "") if sources else ""
        sector = str(ev.get("sector") or "")
        actor = _primary_actor_label(ev)
        existing_entities = list(ev.get("entities") or [])
        source_names = [str(s.get("name") or "") for s in sources if s.get("name")]

        if not top_url:
            ev["title_vi"] = TITLE_UNAVAILABLE
            ev["summary_vi"] = "Chưa có nguồn EventMentions để tóm tắt."
            ev["importance_reason"] = ""
            ev["title"] = ev["title_vi"]
            ev["summary"] = ev["summary_vi"]
            continue

        LOG.info("Enriching event %s/%s [%s]: %s", i, len(events), ev.get("global_event_id", ""), top_url[:80])
        raw_content = extract_web_content(top_url)
        ai_data = None
        if use_gemini:
            ai_data = enrich_event_with_gemini(
                sector,
                actor,
                raw_content,
                num_articles=int(ev.get("num_articles") or 0),
                source_count=int(ev.get("source_count") or len(sources)),
                source_names=source_names,
            )
            if i < len(events):
                time.sleep(GEMINI_CALL_INTERVAL_SEC)

        if ai_data:
            ev["title_vi"] = ai_data.get("title_vi") or TITLE_UNAVAILABLE
            ev["summary_vi"] = ai_data.get("summary_vi") or "Nhấp nguồn để xem chi tiết."
            ev["importance_reason"] = ai_data.get("importance_reason") or ""
            ev["entities"] = _merge_entity_lists(ai_data.get("entities") or [], existing_entities)
        else:
            scraped_title = TITLE_UNAVAILABLE
            if raw_content and raw_content.startswith("Title:"):
                scraped_title = raw_content.split("\n", 1)[0].replace("Title:", "").strip() or TITLE_UNAVAILABLE
            if scraped_title == TITLE_UNAVAILABLE:
                scraped_title = fetch_title(top_url)
            ev["title_vi"] = scraped_title
            ev["summary_vi"] = f"Sự kiện GDELT ({sector}). Nhấp nguồn để đọc bài gốc."
            ev["importance_reason"] = (
                f"GDELT ghi nhận ~{ev.get('num_articles', 0)} lượt đề cập "
                f"và {ev.get('source_count', 0)} nguồn mention trong 24h."
            )
            ev["entities"] = existing_entities

        ev["title"] = ev.get("title_vi") or TITLE_UNAVAILABLE
        ev["summary"] = ev.get("summary_vi") or ""

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
# Event-centric export (one card per GlobalEventID)
# ---------------------------------------------------------------------------


def build_events_from_bq(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Map BigQuery rows → event cards; sources only from EventMentions (+ rep URL fallback)."""
    if df.empty:
        return []

    events: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        sources = list(row.get("mention_sources") or [])
        rep_url = str(row.get("Link_Bai_Bao") or "").strip()
        seen_urls = {s["url"] for s in sources}
        if rep_url.startswith("http") and rep_url not in seen_urls:
            sources.insert(0, _source_record(rep_url, ""))
        if not sources and rep_url.startswith("http"):
            sources = [_source_record(rep_url, "")]

        tone = float(row.get("Diem_Cam_Xuc") or 0)
        rank = int(row.get("rank", 0))
        actor = _normalize_actor_name(row.get("Doi_Tuong_Chinh"))
        orgs = list(row.get("entities_clean") or [])
        try:
            num_articles = int(row.get("So_Bao_De_Cap") or 0)
        except (TypeError, ValueError):
            num_articles = 0

        event_id = str(row.get("GlobalEventID") or row.get("Ma_Su_Kien") or "").strip()
        sector = str(row.get("sector_display") or row.get("Nhom_Nganh") or "").strip()
        entities = _merge_entity_tags([actor] if actor else [], orgs, limit=8)

        events.append(
            {
                "global_event_id": event_id,
                "sector": sector,
                "title_vi": "",
                "summary_vi": "",
                "importance_reason": "",
                "num_articles": max(num_articles, 1),
                "source_count": len({s["url"] for s in sources}),
                "sentiment_tone": round(tone, 2),
                "sentiment_label": sentiment_label_vi(tone),
                "entities": entities,
                "sources": sources[:MAX_MENTIONS_PER_EVENT],
                "impact_score": impact_score(rank, tone, max_rank=max(TARGET_HOT_EVENTS, 1)),
                "primary_actor": actor,
                "article_mentions": max(num_articles, 1),
            }
        )

    events.sort(key=lambda e: (e.get("num_articles") or 0), reverse=True)
    LOG.info("GDELT hot events (GlobalEventID): %s", len(events))
    return events[:TARGET_HOT_EVENTS]


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def build_live_feed_items(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten EventMention sources across hot events (debug / optional feed)."""
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for ev in events:
        sector = str(ev.get("sector") or "")
        mentions = int(ev.get("num_articles") or 0)
        tone = float(ev.get("sentiment_tone") or 0)
        event_id = str(ev.get("global_event_id") or "")
        for src in ev.get("sources") or []:
            url = str(src.get("url") or "").strip()
            if not url.startswith("http") or url in seen:
                continue
            seen.add(url)
            items.append(
                {
                    "url": url,
                    "name": str(src.get("name") or ""),
                    "sector": sector,
                    "mentions": mentions,
                    "tone": round(tone, 2),
                    "global_event_id": event_id,
                }
            )
    items.sort(key=lambda x: (x.get("mentions") or 0), reverse=True)
    return items


def build_payload(
    events: list[dict[str, Any]],
    *,
    query_meta: dict[str, Any],
    live_feed_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    items = live_feed_items or []
    return {
        "schema_version": PULSE_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_events": len(events),
        "total_clusters": len(events),
        "total_feed_articles": len(items),
        "query_meta": query_meta,
        "live_feed_items": items,
        "live_feed_urls": [str(x.get("url") or "") for x in items if x.get("url")],
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
    events = build_events_from_bq(cleaned)
    if events:
        use_gemini = not args.no_gemini
        LOG.info(
            "Gemini enrichment for %s events (gemini=%s, timeout=%ss)",
            len(events),
            use_gemini,
            FETCH_TITLE_TIMEOUT,
        )
        events = enrich_events_for_web(events, use_gemini=use_gemini)
    feed_items = build_live_feed_items(events)
    payload = build_payload(events, query_meta=meta, live_feed_items=feed_items)
    LOG.info(
        "Exported %s hot events, %s EventMention URLs",
        len(events),
        len(feed_items),
    )
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
