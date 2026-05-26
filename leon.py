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
DEFAULT_INVEST_OUTPUT = PROJECT_DIR / "invest_pulse.json"
INVEST_SQL_PATH = PROJECT_DIR / "sql" / "gdelt_invest_pulse.sql"
DEFAULT_MAX_BYTES_BILLED = 500_000_000
DEFAULT_JOB_TIMEOUT_MS = 60_000
TOP_EVENTS_POOL = 300
INVEST_TOP_EVENTS_POOL = 500
BQ_OUTPUT_LIMIT = 50
INVEST_BQ_OUTPUT_LIMIT = 100
TARGET_HOT_EVENTS = 20
MAX_MENTIONS_PER_EVENT = 20
PULSE_SCHEMA_VERSION = "event-centric-v7"
INVEST_PULSE_SCHEMA_VERSION = "invest-event-v1"
GEMINI_MAX_URL_ATTEMPTS = 5
GEMINI_MIN_EXCERPT_CHARS = 60
# Invest: SQL = hot coverage + sector only; Gemini = accurate summary + economic curation.
INVEST_MAX_ENRICH_EVENTS = 80
INVEST_CURATION_POOL = 75
INVEST_FEED_MAX = 20  # trần cứng; không ép đủ số tin — chỉ giữ tin đủ tiêu chí kinh tế
INVEST_VALID_SECTORS = (
    "Vĩ mô - Chính sách Tiền tệ & Lãi suất",
    "Tài chính - Ngân hàng & Tín dụng",
    "Chứng khoán - Thị trường Vốn",
    "Crypto - Tiền mã hóa & Tài sản số",
    "Hàng hóa - Năng lượng & Khoáng sản",
    "Thương mại - Chuỗi cung ứng Toàn cầu",
    "Bất động sản - Hạ tầng",
    "Công nghệ - AI & Bán dẫn",
    "Doanh nghiệp - Công nghiệp & Tiêu dùng",
    "Pháp lý - Quy định & Trừng phạt",
    "Khủng hoảng - Xung đột & An ninh",
    "Chính trị - Ngoại giao",
    "Khác",
)
VALID_SECTORS = (
    "An ninh - Xung đột - Tội phạm",
    "Xã hội - Bất ổn - Biểu tình",
    "Pháp lý - Quy định - Tội phạm",
    "Chính trị - Địa chính trị",
    "Kinh tế vĩ mô",
    "Tài chính - Ngân hàng",
    "Doanh nghiệp - Công nghiệp - Tiêu dùng",
    "Công nghệ - AI - Bán dẫn",
    "Năng lượng - Khí hậu - Tài nguyên",
    "Y tế - Dược phẩm - Sức khỏe cộng đồng",
    "Khoa học - Vũ trụ - Nghiên cứu",
    "Hạ tầng - Bất động sản - Đô thị",
    "Logistics - Chuỗi cung ứng - Thương mại",
    "Xã hội - Giáo dục - Lao động - Đời sống",
    "Khác",
)
FETCH_TITLE_TIMEOUT = 5
TITLE_UNAVAILABLE = "(Title unavailable)"
HTTP_USER_AGENT = "LeonWebIntel/1.0 (+https://leonquant.com)"
# GDELT MentionURL sometimes includes HTML attrs glued to the slug (%20target=, class=, …).
_MENTION_URL_JUNK_RE = re.compile(
    r"(?:%20|\s)(?:target|class|rel|onclick|data-[a-z-]+)=",
    re.IGNORECASE,
)
SKIP_ACTOR_VALUES = frozenset({"", "NONE", "NULL", "UNKNOWN", "KHÔNG RÕ", "KHONG RO", "N/A"})
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"
GEMINI_CALL_INTERVAL_SEC = 2.0

LOG = logging.getLogger("leon.web_intel")
_title_cache: dict[str, str] = {}
_content_cache: dict[str, str | None] = {}
_gemini_configured = False

# CRITICAL: query pushdown — TopEvents first, then mentions, then GKG (sector only).
# URLs come ONLY from eventmentions_partitioned (never from sector/theme matching).
# Final Nhom_Nganh: MEGA CLASSIFIER — CAMEO EventRootCode + GKG V2Themes in one CASE.

GDELT_MACRO_QUERY = f"""
WITH
  RankedTopEvents AS (
    SELECT
      GLOBALEVENTID,
      Actor1Name,
      Actor2Name,
      EventRootCode,
      EventCode,
      GoldsteinScale,
      AvgTone,
      NumArticles,
      SOURCEURL
    FROM `gdelt-bq.gdeltv2.events_partitioned`
    WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
      AND NumArticles >= 40
      AND ABS(AvgTone) >= 4
      AND SOURCEURL IS NOT NULL
      AND STARTS_WITH(SOURCEURL, 'http')
    QUALIFY ROW_NUMBER() OVER (
      PARTITION BY GLOBALEVENTID
      ORDER BY NumArticles DESC, ABS(AvgTone) DESC
    ) = 1
  ),
  TopEvents AS (
    SELECT * FROM RankedTopEvents
    ORDER BY NumArticles DESC, ABS(AvgTone) DESC
    LIMIT {TOP_EVENTS_POOL}
  ),
  FilteredMentions AS (
    SELECT
      m.GLOBALEVENTID,
      m.MentionIdentifier AS MentionURL,
      m.MentionSourceName,
      m.MentionTimeDate
    FROM `gdelt-bq.gdeltv2.eventmentions_partitioned` AS m
    INNER JOIN TopEvents AS e ON m.GLOBALEVENTID = e.GLOBALEVENTID
    WHERE m._PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
      AND m.MentionIdentifier IS NOT NULL
      AND STARTS_WITH(m.MentionIdentifier, 'http')
      AND NOT REGEXP_CONTAINS(
        LOWER(m.MentionIdentifier),
        r'(youtube\\.com|facebook\\.com|x\\.com|twitter\\.com|tiktok\\.com|instagram\\.com)'
      )
  ),
  DedupMentions AS (
    SELECT * FROM FilteredMentions
    QUALIFY ROW_NUMBER() OVER (
      PARTITION BY GLOBALEVENTID, MentionURL
      ORDER BY MentionTimeDate DESC
    ) = 1
  ),
  EventSources AS (
    SELECT
      e.GLOBALEVENTID,
      e.Actor1Name,
      e.Actor2Name,
      e.EventRootCode,
      e.EventCode,
      e.GoldsteinScale,
      e.AvgTone,
      e.NumArticles,
      e.SOURCEURL,
      ARRAY_AGG(m.MentionURL ORDER BY m.MentionTimeDate DESC LIMIT {MAX_MENTIONS_PER_EVENT}) AS SourceURLs,
      ARRAY_AGG(DISTINCT m.MentionSourceName IGNORE NULLS LIMIT 10) AS MentionSources,
      COUNT(DISTINCT m.MentionURL) AS source_count
    FROM TopEvents AS e
    LEFT JOIN DedupMentions AS m ON e.GLOBALEVENTID = m.GLOBALEVENTID
    GROUP BY
      e.GLOBALEVENTID,
      e.Actor1Name,
      e.Actor2Name,
      e.EventRootCode,
      e.EventCode,
      e.GoldsteinScale,
      e.AvgTone,
      e.NumArticles,
      e.SOURCEURL
  ),
  FilteredGKG AS (
    SELECT
      DocumentIdentifier,
      V2Themes,
      V2Organizations,
      V2Persons,
      V2Locations
    FROM `gdelt-bq.gdeltv2.gkg_partitioned`
    WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
      AND DocumentIdentifier IS NOT NULL
  )
SELECT
  e.GLOBALEVENTID AS GlobalEventID,
  e.Actor1Name AS Doi_Tuong_Chinh,
  e.Actor2Name,
  e.EventRootCode,
  e.EventCode,
  e.GoldsteinScale,
  e.AvgTone AS Diem_Cam_Xuc,
  e.NumArticles AS So_Bao_De_Cap,
  e.SOURCEURL AS Link_Bai_Bao,
  COALESCE(e.SourceURLs, ARRAY<STRING>[]) AS SourceURLs,
  COALESCE(e.MentionSources, ARRAY<STRING>[]) AS MentionSources,
  e.source_count,
  CASE
    WHEN e.EventRootCode IN ('18', '19', '20') THEN 'An ninh - Xung đột - Tội phạm'
    WHEN e.EventRootCode IN ('14') THEN 'Xã hội - Bất ổn - Biểu tình'
    WHEN e.EventRootCode IN ('09', '17') OR REGEXP_CONTAINS(g.V2Themes, r'LAW|LEGAL|LEGISLATION|REGULATION|COURT|JUSTICE|JUDGE|LAWSUIT|TRIAL|POLICE|CRIME|CRIMINAL|INVESTIGATION|ARREST|CORRUPTION|FRAUD|ANTITRUST|COMPLIANCE|PROSECUTOR|SENTENCE|PRISON|HUMAN_RIGHTS|IMMIGRATION')
      THEN 'Pháp lý - Quy định - Tội phạm'
    WHEN e.EventRootCode IN ('04', '05', '13', '15', '16') OR REGEXP_CONTAINS(g.V2Themes, r'POLITICAL|POLITICS|GOVERNMENT|PRESIDENT|PRIME_MINISTER|PARLIAMENT|ELECTION|VOTE|DIPLOMACY|FOREIGN_POLICY|GEOPOLITICS|MILITARY|WAR|CONFLICT|CRISIS|TERROR|SANCTIONS|BORDER|NATO|UNITED_NATIONS|MIDDLE_EAST|RUSSIA|UKRAINE|CHINA|ISRAEL|IRAN')
      THEN 'Chính trị - Địa chính trị'
    WHEN e.EventRootCode IN ('06', '07') OR REGEXP_CONTAINS(g.V2Themes, r'ECON|ECONOMY|GDP|GROWTH|RECESSION|INFLATION|DEFLATION|CPI|PPI|INTEREST_RATE|RATE_HIKE|RATE_CUT|CENTRAL_BANK|FED|ECB|BOJ|MONETARY_POLICY|FISCAL_POLICY|BUDGET|DEFICIT|TRADE_BALANCE|UNEMPLOYMENT')
      THEN 'Kinh tế vĩ mô'
    WHEN REGEXP_CONTAINS(g.V2Themes, r'FINANCE|FINANCIAL|BANK|BANKING|CREDIT|LOAN|BOND|TREASURY|YIELD|CURRENCY|FOREX|USD|DOLLAR|EURO|STOCK|EQUITY|MARKET|WALL_STREET|INVESTOR|FUND|ETF|INSURANCE|LIQUIDITY|DEFAULT|BANKRUPTCY|FINANCIAL_RISK|CREDIT_RISK')
      THEN 'Tài chính - Ngân hàng'
    WHEN REGEXP_CONTAINS(g.V2Themes, r'TECH|TECHNOLOGY|ARTIFICIAL_INTELLIGENCE|AI|MACHINE_LEARNING|ROBOTICS|SOFTWARE|HARDWARE|SEMICONDUCTOR|CHIP|GPU|DATA_CENTER|CLOUD|CYBER|CYBERSECURITY|HACKING|DATA_BREACH|INTERNET|DIGITAL|PLATFORM|TELECOM|5G|INNOVATION')
      THEN 'Công nghệ - AI - Bán dẫn'
    WHEN REGEXP_CONTAINS(g.V2Themes, r'ENERGY|OIL|GAS|LNG|COAL|ELECTRICITY|POWER|GRID|NUCLEAR|SOLAR|WIND|RENEWABLE|CLIMATE|ENV_|ENVIRONMENT|CARBON|EMISSION|MINING|MINERALS|GOLD|COPPER|LITHIUM|WATER|DROUGHT|FLOOD|WILDFIRE|EARTHQUAKE|DISASTER|OPEC')
      THEN 'Năng lượng - Khí hậu - Tài nguyên'
    WHEN REGEXP_CONTAINS(g.V2Themes, r'BUSINESS|COMPANY|CORPORATE|INDUSTRY|INDUSTRIAL|MANUFACTURING|FACTORY|PRODUCTION|RETAIL|CONSUMER|SALES|REVENUE|PROFIT|EARNINGS|IPO|MERGER|ACQUISITION|STARTUP|LAYOFFS|AUTO|EV|AIRLINE|TOURISM|HOTEL|RESTAURANT')
      THEN 'Doanh nghiệp - Công nghiệp - Tiêu dùng'
    WHEN REGEXP_CONTAINS(g.V2Themes, r'LOGISTICS|SUPPLY_CHAIN|SHIPPING|CONTAINER|FREIGHT|CARGO|TRANSPORTATION|CUSTOMS|DELIVERY|WAREHOUSE|MARITIME|CANAL|RED_SEA|STRAIT|ROUTE|DISTRIBUTION|INVENTORY')
      THEN 'Logistics - Chuỗi cung ứng - Thương mại'
    WHEN REGEXP_CONTAINS(g.V2Themes, r'INFRASTRUCTURE|CONSTRUCTION|REAL_ESTATE|HOUSING|PROPERTY|URBAN|CITY|TRANSPORT|ROAD|RAIL|AIRPORT|PORT|BRIDGE|METRO|SMART_CITY|PUBLIC_WORKS|WATER_SUPPLY|BUILDING|LAND|MORTGAGE')
      THEN 'Hạ tầng - Bất động sản - Đô thị'
    WHEN REGEXP_CONTAINS(g.V2Themes, r'HEALTH|MEDICAL|DISEASE|PANDEMIC|EPIDEMIC|OUTBREAK|VACCINE|PHARMA|WHO|PUBLIC_HEALTH|HEALTHCARE|EBOLA|COVID|FLU|CANCER|BIOTECH')
      THEN 'Y tế - Dược phẩm - Sức khỏe cộng đồng'
    WHEN REGEXP_CONTAINS(g.V2Themes, r'SCIENCE|RESEARCH|STUDY|DISCOVERY|SPACE|NASA|ESA|SATELLITE|ROCKET|ASTRONOMY|PHYSICS|CHEMISTRY|BIOLOGY|GENETICS|ARCHAEOLOGY|UNIVERSITY|LABORATORY|EXPERIMENT|QUANTUM|CLIMATE_SCIENCE')
      THEN 'Khoa học - Vũ trụ - Nghiên cứu'
    WHEN REGEXP_CONTAINS(g.V2Themes, r'SOCIETY|SOCIAL|EDUCATION|SCHOOL|STUDENT|LABOR|WORKER|EMPLOYMENT|STRIKE|UNION|WAGE|MIGRATION|DEMOGRAPHICS|POPULATION|CULTURE|MEDIA|ENTERTAINMENT|SPORTS|LIFESTYLE|POVERTY|INEQUALITY')
      THEN 'Xã hội - Giáo dục - Lao động - Đời sống'
    ELSE 'Khác'
  END AS Nhom_Nganh,
  REGEXP_REPLACE(COALESCE(g.V2Organizations, ''), r',?\\d+', '') AS Cac_To_Chuc_Lien_Quan,
  g.V2Themes,
  g.V2Persons,
  g.V2Locations
FROM EventSources AS e
LEFT JOIN FilteredGKG AS g ON e.SOURCEURL = g.DocumentIdentifier
ORDER BY e.NumArticles DESC, ABS(e.AvgTone) DESC, e.source_count DESC
LIMIT {BQ_OUTPUT_LIMIT}
""".strip()


# ---------------------------------------------------------------------------
# BigQuery
# ---------------------------------------------------------------------------


def load_invest_query() -> str:
    if not INVEST_SQL_PATH.is_file():
        raise FileNotFoundError(f"Missing invest SQL: {INVEST_SQL_PATH}")
    return INVEST_SQL_PATH.read_text(encoding="utf-8").strip()


def build_query(*, channel: str = "world") -> str:
    """Return GDELT SQL for world LIVE or investment channel."""
    if channel == "invest":
        return load_invest_query()
    return GDELT_MACRO_QUERY


def valid_sectors_for(channel: str) -> tuple[str, ...]:
    return INVEST_VALID_SECTORS if channel == "invest" else VALID_SECTORS


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
    channel: str = "world",
    job_timeout_ms: int = DEFAULT_JOB_TIMEOUT_MS,
    maximum_bytes_billed: int = DEFAULT_MAX_BYTES_BILLED,
    dry_run: bool = False,
) -> tuple[pd.DataFrame | None, dict[str, Any]]:
    """Execute macro query; returns small dataframe (~150 rows) or None on dry-run."""
    sql = build_query(channel=channel)
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


def _parse_bq_array_field(val: Any) -> list[str]:
    out: list[str] = []
    for item in _iter_raw_sequence(val):
        text = str(item or "").strip()
        if text:
            out.append(text)
    return out


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


def _normalize_mention_url(url: str) -> str:
    """Strip GDELT junk (HTML attributes appended to article URLs)."""
    u = str(url or "").strip()
    if not u.startswith("http"):
        return u
    match = _MENTION_URL_JUNK_RE.search(u)
    if match and match.start() > 0:
        u = u[: match.start()]
    return u.rstrip(" %)")


def _mention_url_dedupe_key(url: str) -> str:
    clean = _normalize_mention_url(url)
    parsed = urlparse(clean)
    host = (parsed.netloc or "").lower().replace("www.", "")
    path = (parsed.path or "/").rstrip("/") or "/"
    return f"{host}|{path}"


def _iter_mention_url_strings(urls_val: Any) -> list[str]:
    out: list[str] = []
    for item in _iter_raw_sequence(urls_val):
        url = str(item).strip() if not isinstance(item, dict) else str(item.get("url") or "").strip()
        if url.startswith("http"):
            out.append(url)
    return out


def _dedupe_mention_urls(urls: Any, *, limit: int | None = MAX_MENTIONS_PER_EVENT) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    seq = urls if isinstance(urls, list) else _iter_mention_url_strings(urls)
    for raw in seq:
        clean = _normalize_mention_url(str(raw).strip())
        if not clean.startswith("http"):
            continue
        key = _mention_url_dedupe_key(clean)
        if key in seen:
            continue
        seen.add(key)
        out.append(clean)
        if limit is not None and len(out) >= limit:
            break
    return out


def _parse_source_urls(
    urls_val: Any,
    _names_val: Any = None,
    *,
    rep_url: str = "",
) -> list[str]:
    """SourceURLs from GDELT EventMentions; normalize junk suffixes, dedupe by path."""
    del _names_val
    out = _dedupe_mention_urls(urls_val)
    if not out:
        rep = _normalize_mention_url(str(rep_url or "").strip())
        if rep.startswith("http"):
            return [rep]
    return out


def expand_event_sources(events: list[dict[str, Any]], _cleaned: pd.DataFrame | None = None) -> list[dict[str, Any]]:
    """Passthrough — sources already from GDELT EventMentions per GlobalEventID."""
    del _cleaned
    return events


def sentiment_label_vi(tone: float) -> str:
    t = float(tone)
    if t <= -8.0:
        return "Tiêu cực mạnh"
    if t <= -4.0:
        return "Tiêu cực"
    if t < 4.0:
        return "Trung tính"
    if t < 8.0:
        return "Tích cực"
    return "Tích cực mạnh"


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """One row per GlobalEventID; sources from SourceURLs (EventMentions) only."""
    if df.empty:
        return df

    out = df.copy()
    out.columns = [str(c) for c in out.columns]
    out["Link_Bai_Bao"] = out["Link_Bai_Bao"].fillna("").astype(str).str.strip()

    if "SourceURLs" in out.columns:
        out["mention_sources"] = out.apply(
            lambda r: _parse_source_urls(
                r.get("SourceURLs"),
                r.get("MentionSources"),
                rep_url=str(r.get("Link_Bai_Bao") or ""),
            ),
            axis=1,
        )
        out["mention_source_count"] = out["SourceURLs"].apply(
            lambda v: len(_dedupe_mention_urls(v, limit=None))
        )
    else:
        out["mention_sources"] = out["Link_Bai_Bao"].map(
            lambda u: [str(u).strip()] if str(u).strip().startswith("http") else []
        )

    id_col = "GlobalEventID" if "GlobalEventID" in out.columns else "Ma_Su_Kien"
    if id_col in out.columns:
        out = out.drop_duplicates(subset=[id_col], keep="first")

    out["Doi_Tuong_Chinh"] = out["Doi_Tuong_Chinh"].fillna("").astype(str).str.strip()
    out["Actor2Name"] = out.get("Actor2Name", pd.Series([""] * len(out))).fillna("").astype(str).str.strip()
    if "primary_sector" in out.columns:
        ps = out["primary_sector"].fillna("").astype(str).str.strip()
        if "Nhom_Nganh" in out.columns:
            nh = out["Nhom_Nganh"].fillna("").astype(str).str.strip()
            out["Nhom_Nganh"] = nh.where(nh != "", ps).replace("", "Khác")
        else:
            out["Nhom_Nganh"] = ps.replace("", "Khác")
    else:
        out["Nhom_Nganh"] = out["Nhom_Nganh"].fillna("Khác").astype(str).str.strip()
    for col in ("secondary_sector", "macro_signal", "investment_relevance"):
        if col not in out.columns:
            out[col] = ""
        else:
            out[col] = out[col].fillna("").astype(str).str.strip()
    if "risk_flags" not in out.columns:
        out["risk_flags"] = [[] for _ in range(len(out))]
    else:
        out["risk_flags"] = out["risk_flags"].map(_parse_bq_array_field)
    if "affected_assets" not in out.columns:
        out["affected_assets"] = [[] for _ in range(len(out))]
    else:
        out["affected_assets"] = out["affected_assets"].map(_parse_bq_array_field)
    for col in ("V2Themes", "V2Persons", "V2Locations"):
        if col not in out.columns:
            out[col] = ""
        else:
            out[col] = out[col].fillna("").astype(str)
    out["Diem_Cam_Xuc"] = pd.to_numeric(out["Diem_Cam_Xuc"], errors="coerce").fillna(0.0)
    out["source_count"] = pd.to_numeric(out.get("source_count", 0), errors="coerce").fillna(0).astype(int)
    out["entities_clean"] = out["Cac_To_Chuc_Lien_Quan"].map(lambda x: parse_entity_list(x, limit=6))
    out["persons_clean"] = out["V2Persons"].map(lambda x: parse_entity_list(x, limit=4))
    out["locations_clean"] = out["V2Locations"].map(lambda x: parse_entity_list(x, limit=4))
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


def _parse_gemini_json(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        return {}
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, flags=re.DOTALL)
    if fence:
        raw = fence.group(1).strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start >= 0 and end > start:
        raw = raw[start : end + 1]
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return _parse_gemini_enrichment_legacy(raw)


def _parse_gemini_enrichment_legacy(text: str) -> dict[str, Any]:
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
            ent_raw = line.split(":", 1)[1].strip()
            if ent_raw.lower() in ("none", "không", "khong", "n/a", "-"):
                result["entities"] = []
            else:
                result["entities"] = [e.strip() for e in ent_raw.split(",") if e.strip()]
    return result


def _excerpt_body(raw_content: str) -> str:
    text = str(raw_content or "")
    if "Content Snippet:" in text:
        return text.split("Content Snippet:", 1)[1].strip()
    return ""


def _has_usable_excerpt(raw_content: str | None) -> bool:
    """Require scraped article text — never call Gemini on GDELT metadata alone."""
    if not raw_content or not str(raw_content).strip().startswith("Title:"):
        return False
    if not _usable_title(_title_from_scrape(raw_content)):
        return False
    body = _excerpt_body(raw_content)
    if len(body) >= GEMINI_MIN_EXCERPT_CHARS:
        return True
    title = _title_from_scrape(raw_content)
    return len(title) >= 24


def enrich_event_with_gemini(
    *,
    sector: str,
    num_articles: int,
    source_count: int,
    raw_content: str,
    channel: str = "world",
) -> dict[str, Any] | None:
    """Vietnamese copy from scraped excerpt only — no GDELT metadata in the prompt."""
    if not _configure_gemini() or not _has_usable_excerpt(raw_content):
        return None

    excerpt = str(raw_content).strip()
    sectors = valid_sectors_for(channel)
    sectors_list = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(sectors) if s != "Khác")
    model_name = os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL
    model = genai.GenerativeModel(model_name)
    if channel == "invest":
        prompt = f"""
Bạn là biên tập viên chuyên mục kinh tế đầu tư vĩ mô của LeonQuant.

CHỈ dùng thông tin trong "Đoạn bài tham khảo". Không dùng kiến thức ngoài.
Tuyệt đối không nhắc: AI, GDELT, crawler, pipeline, thuật toán, hệ thống, dữ liệu hệ thống,
"theo danh mục theo dõi", "trong hệ thống", số bài trong hệ thống, hay meta về quy trình xử lý tin.
Không khuyến nghị mua/bán/múc. Không bịa ticker, giá, hoặc tác động tài sản không có trong bài.

Ngành gợi ý (chỉ đổi sector nếu đoạn bài rõ thuộc ngành khác trong danh sách): {sector}
Độ phủ báo chí (~{num_articles} bài, {source_count} nguồn) chỉ được nhắc ngắn gọn trong importance_reason
theo kiểu "được nhiều báo đưa" — không gắn với thị trường vốn hay công cụ nội bộ.

Quy tắc tóm tắt (quan trọng):
- Tóm tắt trung thực đoạn bài: sự kiện là gì, ai liên quan — không thêm chi tiết không có trong bài.
- Nếu bài nói chính sách/lãi suất/lạm phát/chứng khoán/crypto/vàng/dầu/ngân hàng thì summary phải phản ánh đúng, không lệch sang scandal chính trị.
- Nếu bài không nêu tác động kinh tế: summary trung lập, không ép về thị trường.
- Không suy diễn risk-on/risk-off hay giá/ticker nếu bài không đề cập.
- importance_reason: một câu — ý nghĩa với nhà đầu tư khi bài hỗ trợ; nếu không rõ thì nói trung lập.

Trả về JSON (không markdown):
{{
  "title_vi": "Tiêu đề tối đa 18 từ, rõ sự kiện",
  "summary_vi": "1-2 câu khách quan, bám sát đoạn bài",
  "importance_reason": "Một câu: ý nghĩa kinh tế/đầu tư (hoặc trung lập nếu bài không nói thị trường)",
  "entities": ["3-6 thực thể trong đoạn bài"],
  "sector": "một trong danh sách ngành hợp lệ"
}}

Danh sách ngành:
{sectors_list}

Đoạn bài tham khảo:
{excerpt}
""".strip()
    else:
        prompt = f"""
Bạn là biên tập viên phân tích quốc tế của LeonQuant.

CHỈ được dùng thông tin trong khối "Đoạn bài tham khảo" bên dưới.
Không dùng kiến thức ngoài, không suy diễn từ tên tổ chức/địa điểm không có trong đoạn bài.
Không nhắc AI, GDELT, crawler, pipeline.
Không khuyến nghị đầu tư. Không bịa ticker.

Ngành gợi ý (SQL, chỉ đổi sector nếu đoạn bài rõ ràng thuộc ngành khác): {sector}
Độ phủ: ~{num_articles} bài, {source_count} nguồn URL — dùng cho importance_reason, không bịa chi tiết sự kiện.

Trả về đúng một JSON object (không markdown):
{{
  "title_vi": "Tiêu đề tiếng Việt tối đa 18 từ",
  "summary_vi": "Tóm tắt 1-2 câu chỉ từ đoạn bài",
  "importance_reason": "Một câu: vì sao đáng chú ý (có thể nhắc độ phủ)",
  "entities": ["3-6 thực thể có trong đoạn bài"],
  "sector": "một trong danh sách ngành hợp lệ",
  "sector_confidence": 0
}}

Danh sách ngành hợp lệ:
{sectors_list}

Đoạn bài tham khảo:
{excerpt}
""".strip()

    try:
        response = model.generate_content(prompt)
        parsed = _parse_gemini_json(response.text or "")
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


def _usable_title(title: Any) -> bool:
    t = str(title or "").strip()
    return bool(t) and t != TITLE_UNAVAILABLE


def _title_from_scrape(raw_content: str | None) -> str:
    if raw_content and raw_content.startswith("Title:"):
        scraped = raw_content.split("\n", 1)[0].replace("Title:", "").strip()
        if scraped:
            return scraped[:300]
    return TITLE_UNAVAILABLE


def _gemini_kwargs(ev: dict[str, Any], urls: list[str], *, channel: str = "world") -> dict[str, Any]:
    return {
        "sector": str(ev.get("primary_sector") or ev.get("sector") or "Khác"),
        "num_articles": int(ev.get("num_articles") or 0),
        "source_count": int(ev.get("source_count") or len(urls)),
        "channel": channel,
    }


def enrich_events_for_web(
    events: list[dict[str, Any]], *, use_gemini: bool = True, channel: str = "world"
) -> list[dict[str, Any]]:
    """Try up to GEMINI_MAX_URL_ATTEMPTS URLs; Gemini only when scrape returns article excerpt."""
    for i, ev in enumerate(events, start=1):
        urls = [str(u).strip() for u in (ev.get("sources") or []) if str(u).strip().startswith("http")]
        sector = str(ev.get("primary_sector") or ev.get("sector") or "Khác")
        existing_entities = list(ev.get("entities") or [])
        attempt_urls = urls[:GEMINI_MAX_URL_ATTEMPTS]
        gemini_args = _gemini_kwargs(ev, urls, channel=channel)

        if not attempt_urls:
            ev["title_vi"] = TITLE_UNAVAILABLE
            ev["summary_vi"] = "Chưa có nguồn tin để tóm tắt."
            ev["importance_reason"] = ""
            ev["title"] = ev["title_vi"]
            ev["summary"] = ev["summary_vi"]
            continue

        ai_data: dict[str, Any] | None = None
        if use_gemini:
            for j, url in enumerate(attempt_urls):
                LOG.info(
                    "Enriching event %s/%s [%s] url %s/%s: %s",
                    i,
                    len(events),
                    ev.get("global_event_id", ""),
                    j + 1,
                    len(attempt_urls),
                    url[:80],
                )
                raw_content = extract_web_content(url)
                if raw_content and _has_usable_excerpt(raw_content):
                    ai_data = enrich_event_with_gemini(**gemini_args, raw_content=raw_content)
                    if _usable_title((ai_data or {}).get("title_vi")):
                        ev["enrichment_url"] = url
                        break
                    ai_data = None
                if j < len(attempt_urls) - 1:
                    time.sleep(GEMINI_CALL_INTERVAL_SEC)
            if i < len(events) and ai_data:
                time.sleep(GEMINI_CALL_INTERVAL_SEC)
        else:
            scraped_title = TITLE_UNAVAILABLE
            for url in attempt_urls:
                raw_content = extract_web_content(url)
                scraped_title = _title_from_scrape(raw_content)
                if not _usable_title(scraped_title):
                    scraped_title = fetch_title(url)
                if _usable_title(scraped_title):
                    break

        if ai_data and _usable_title(ai_data.get("title_vi")):
            ev["title_vi"] = ai_data.get("title_vi") or TITLE_UNAVAILABLE
            ev["summary_vi"] = ai_data.get("summary_vi") or "Nhấp nguồn để xem chi tiết."
            ev["importance_reason"] = ai_data.get("importance_reason") or ""
            gem_sector = str(ai_data.get("sector") or "").strip()
            allowed = valid_sectors_for(channel)
            if gem_sector in allowed:
                ev["sector"] = gem_sector
                if channel == "invest":
                    ev["primary_sector"] = gem_sector
            ev["entities"] = _merge_entity_lists(ai_data.get("entities") or [], limit=6)
        elif not use_gemini:
            ev["title_vi"] = scraped_title
            ev["summary_vi"] = f"Sự kiện thuộc nhóm {sector}. Nhấp nguồn để đọc bài gốc."
            ev["importance_reason"] = (
                f"Độ phủ khoảng {ev.get('num_articles', 0)} bài báo "
                f"và {ev.get('source_count', 0)} nguồn tin trong 24 giờ qua."
            )
            ev["entities"] = existing_entities
        else:
            scraped_title = TITLE_UNAVAILABLE
            for url in attempt_urls:
                raw_content = extract_web_content(url)
                scraped_title = _title_from_scrape(raw_content)
                if not _usable_title(scraped_title):
                    scraped_title = fetch_title(url)
                if _usable_title(scraped_title):
                    break
            ev["title_vi"] = scraped_title
            ev["summary_vi"] = f"Sự kiện thuộc nhóm {sector}. Nhấp nguồn để đọc bài gốc."
            ev["importance_reason"] = (
                f"Độ phủ khoảng {ev.get('num_articles', 0)} bài báo "
                f"và {ev.get('source_count', 0)} nguồn tin trong 24 giờ qua."
            )
            ev["entities"] = existing_entities

        ev["title"] = ev.get("title_vi") or TITLE_UNAVAILABLE
        ev["summary"] = ev.get("summary_vi") or ""

    return events


# ---------------------------------------------------------------------------
# Gemini source alignment (GDELT sometimes attaches unrelated MentionURLs)
# ---------------------------------------------------------------------------


def _event_source_filter_block(ev: dict[str, Any]) -> str:
    eid = str(ev.get("global_event_id") or "")
    title = str(ev.get("title_vi") or ev.get("title") or "").strip()
    summary = str(ev.get("summary_vi") or ev.get("summary") or "").strip()[:200]
    urls = _dedupe_mention_urls(ev.get("sources") or [], limit=MAX_MENTIONS_PER_EVENT)
    url_lines = "\n".join(f"    {i + 1}. {u[:140]}" for i, u in enumerate(urls))
    anchor = str(ev.get("enrichment_url") or urls[0] if urls else "")
    return f"EventID={eid}\nTitle: {title}\nSummary: {summary}\nAnchor URL (title source): {anchor[:140]}\nCandidate URLs:\n{url_lines}"


def _parse_gemini_source_filters(text: str) -> dict[str, list[str]]:
    raw = (text or "").strip()
    if not raw:
        return {}
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, flags=re.DOTALL)
    if fence:
        raw = fence.group(1).strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start >= 0 and end > start:
        raw = raw[start : end + 1]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    rows = data.get("events") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return {}
    out: dict[str, list[str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        eid = str(row.get("global_event_id") or "").strip()
        keep = row.get("keep_urls") or row.get("keep") or []
        if not eid or not isinstance(keep, list):
            continue
        urls = [str(u).strip() for u in keep if str(u).strip().startswith("http")]
        if urls:
            out[eid] = urls
    return out


def _apply_filtered_sources(ev: dict[str, Any], keep_urls: list[str]) -> None:
    current = _dedupe_mention_urls(ev.get("sources") or [], limit=None)
    if not current:
        return
    keep_keys = {_mention_url_dedupe_key(u) for u in keep_urls if str(u).startswith("http")}
    filtered = [u for u in current if _mention_url_dedupe_key(u) in keep_keys]
    if not filtered:
        filtered = _dedupe_mention_urls(keep_urls, limit=MAX_MENTIONS_PER_EVENT)
    if not filtered:
        anchor = str(ev.get("enrichment_url") or "").strip()
        if anchor.startswith("http"):
            filtered = [_normalize_mention_url(anchor)]
        else:
            filtered = current[:1]
    ev["sources"] = filtered[:MAX_MENTIONS_PER_EVENT]
    ev["source_count"] = max(len(_dedupe_mention_urls(filtered, limit=None)), 1)


def gemini_filter_misaligned_sources(events: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Return {global_event_id: keep_urls} for events with multiple candidate sources."""
    eligible = [
        ev
        for ev in events
        if len(_dedupe_mention_urls(ev.get("sources") or [], limit=None)) > 1
        and _usable_title(ev.get("title_vi") or ev.get("title"))
    ]
    if not eligible or not _configure_gemini():
        return {}

    blocks = "\n\n".join(_event_source_filter_block(ev) for ev in eligible)
    model_name = os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL
    model = genai.GenerativeModel(model_name)
    prompt = f"""
Bạn là biên tập fact-check. GDELT đôi khi gắn nhầm MentionURL không cùng câu chuyện vào một GlobalEventID.

Với từng event: giữ lại URL thật sự cùng câu chuyện với Title/Summary tiếng Việt (và Anchor URL nếu có).
- Loại URL syndication lẫn từ event khác (vd. Sudbury food bank dính vào Navarra; Yahoo AI stocks dính vào Navarra).
- Giữ syndication hợp lệ nếu cùng một vụ (vd. nhiều báo đưa tin Nhà Trắng).
- keep_urls phải là chuỗi URL copy y nguyên từ danh sách Candidate URLs.
- Mỗi event giữ ít nhất 1 URL.

Trả về JSON (không markdown):
{{
  "events": [
    {{
      "global_event_id": "...",
      "keep_urls": ["https://..."],
      "reason": "một câu tiếng Việt"
    }}
  ]
}}

Events:
{blocks}
""".strip()

    try:
        response = model.generate_content(prompt)
        return _parse_gemini_source_filters(response.text or "")
    except Exception as exc:
        LOG.warning("Gemini source filter failed: %s", exc)
        return {}


def filter_event_sources_with_gemini(events: list[dict[str, Any]], *, use_gemini: bool = True) -> list[dict[str, Any]]:
    if not use_gemini or len(events) < 1:
        return events

    filters = gemini_filter_misaligned_sources(events)
    if filters:
        time.sleep(GEMINI_CALL_INTERVAL_SEC)
    if not filters:
        return events

    by_id = {str(ev.get("global_event_id") or ""): ev for ev in events if ev.get("global_event_id")}
    for eid, keep_urls in filters.items():
        ev = by_id.get(eid)
        if not ev:
            continue
        before = len(_dedupe_mention_urls(ev.get("sources") or [], limit=None))
        _apply_filtered_sources(ev, keep_urls)
        after = len(_dedupe_mention_urls(ev.get("sources") or [], limit=None))
        if after < before:
            LOG.info("Source filter %s: %s -> %s URLs", eid, before, after)

    for ev in events:
        ev.pop("enrichment_url", None)
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


def _invest_curation_brief(ev: dict[str, Any]) -> str:
    eid = str(ev.get("global_event_id") or "")
    sector = str(ev.get("primary_sector") or ev.get("sector") or "")
    num = int(ev.get("num_articles") or 0)
    title = str(ev.get("title_vi") or ev.get("title") or "").strip()[:140]
    summary = str(ev.get("summary_vi") or ev.get("summary") or "").strip()[:180]
    assets = ",".join(list(ev.get("affected_assets") or [])[:6])
    return f"id={eid} | {num} bài | {sector} | assets={assets} | {title} | {summary}"


def _parse_gemini_curation_ids(text: str) -> list[str]:
    raw = (text or "").strip()
    if not raw:
        return []
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, flags=re.DOTALL)
    if fence:
        raw = fence.group(1).strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start >= 0 and end > start:
        raw = raw[start : end + 1]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    ids = data.get("selected_ids") if isinstance(data, dict) else None
    if not isinstance(ids, list):
        return []
    return [str(x).strip() for x in ids if str(x).strip()]


def _gemini_curate_invest_ids(
    pool: list[dict[str, Any]],
    *,
    max_events: int = INVEST_FEED_MAX,
) -> list[str]:
    """Ask Gemini which GlobalEventIDs belong on the invest feed (quality over count)."""
    candidates = [
        ev for ev in pool if _usable_title(ev.get("title_vi") or ev.get("title"))
    ]
    if not candidates or not _configure_gemini():
        return []

    sectors_list = "\n".join(f"- {s}" for s in INVEST_VALID_SECTORS if s != "Khác")
    lines = "\n".join(f"{i + 1}. {_invest_curation_brief(ev)}" for i, ev in enumerate(candidates))
    model_name = os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL
    model = genai.GenerativeModel(model_name)
    prompt = f"""
Bạn là biên tập chuyên mục kinh tế đầu tư vĩ mô của LeonQuant.

Bối cảnh: danh sách dưới đây là tin ĐANG NÓNG (nhiều báo nhắc trong 24h). SQL/GKG chỉ gán ngành gợi ý.
Title và summary đã được biên tập từ bài gốc — hãy đọc nội dung đó, không đoán từ độ nóng.

Nhiệm vụ: chọn TẤT CẢ và CHỈ những GlobalEventID thật sự đủ tiêu chí đưa lên chuyên mục.
Không cần đủ số lượng cố định — có thể 3 tin, có thể 12; trung thực quan trọng hơn đủ 20.
Nếu quá nhiều tin đạt chuẩn, giữ tối đa {max_events} tin có tác động kinh tế/đầu tư rõ nhất.

GIỮ tin nếu ít nhất một điều đúng:
(a) Có tác động kinh tế/đầu tư/thị trường rõ (vĩ mô, chính sách, lãi suất, lạm phát, ngân hàng, CK, crypto,
    vàng/dầu/khí, thuế, thương mại, chuỗi cung ứng, doanh nghiệp lớn, bán dẫn/AI có góc đầu tư), HOẶC
(b) Mô tả đúng bối cảnh/tình hình kinh tế vĩ mô (kể cả khi bài phân tích, không chỉ tin tức sốc).

BỎ tin chỉ là: scandal cá nhân, tội phạm địa phương, lễ tang, giải trí, shooting/vụ án
không liên quan thị trường — dù đang viral.

Ưu tiên đa dạng chủ đề kinh tế khi có ứng viên; không chọn toàn chính trị chỉ vì nhiều bài.

Không nhắc AI, GDELT, crawler, pipeline, hệ thống.

Trả về JSON (không markdown):
{{
  "selected_ids": ["GlobalEventID", ...],
  "notes": "một câu tiếng Việt về tiêu chí"
}}

Danh sách ngành hợp lệ:
{sectors_list}

Ứng viên:
{lines}
""".strip()

    try:
        response = model.generate_content(prompt)
        return _parse_gemini_curation_ids(response.text or "")
    except Exception as exc:
        LOG.warning("Gemini invest curation failed: %s", exc)
        return []


def gemini_curate_invest_feed(
    events: list[dict[str, Any]], *, use_gemini: bool = True, max_events: int = INVEST_FEED_MAX
) -> list[dict[str, Any]]:
    """Gemini keeps only economically relevant stories; count may be below max_events."""
    if not events:
        return []

    ranked = sorted(events, key=lambda e: (int(e.get("num_articles") or 0),), reverse=True)
    if not use_gemini or not _configure_gemini():
        return ranked[:max_events]

    pool = ranked[:INVEST_CURATION_POOL]
    by_id = {str(e.get("global_event_id") or ""): e for e in pool if e.get("global_event_id")}
    if not by_id:
        return ranked[:max_events]

    selected_ids = _gemini_curate_invest_ids(pool, max_events=max_events)

    picked: list[dict[str, Any]] = []
    seen: set[str] = set()
    for eid in selected_ids:
        if eid in by_id and eid not in seen:
            picked.append(by_id[eid])
            seen.add(eid)
        if len(picked) >= max_events:
            break

    LOG.info("Gemini invest curation: kept %s / %s hot candidates (max %s)", len(picked), len(pool), max_events)
    return picked


def build_events_from_bq(df: pd.DataFrame, *, channel: str = "world") -> list[dict[str, Any]]:
    """One card per GlobalEventID; sources from SourceURLs (EventMentions) only."""
    if df.empty:
        return []

    events: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        sources = list(row.get("mention_sources") or [])
        tone = float(row.get("Diem_Cam_Xuc") or 0)
        rank = int(row.get("rank", 0))
        actor = _normalize_actor_name(row.get("Doi_Tuong_Chinh"))
        actor2 = _normalize_actor_name(row.get("Actor2Name"))
        orgs = list(row.get("entities_clean") or [])
        persons = list(row.get("persons_clean") or [])
        locations = list(row.get("locations_clean") or [])
        try:
            num_articles = int(row.get("So_Bao_De_Cap") or 0)
        except (TypeError, ValueError):
            num_articles = 0
        try:
            bq_source_count = int(row.get("source_count") or 0)
        except (TypeError, ValueError):
            bq_source_count = 0
        try:
            norm_source_count = int(row.get("mention_source_count") or 0)
        except (TypeError, ValueError):
            norm_source_count = 0

        event_id = str(row.get("GlobalEventID") or "").strip()
        sector = str(row.get("Nhom_Nganh") or "Khác").strip()
        entities = _merge_entity_lists(
            [actor, actor2] if actor2 else ([actor] if actor else []),
            orgs,
            persons,
            locations,
            limit=6,
        )
        source_count = norm_source_count if norm_source_count > 0 else (
            bq_source_count if bq_source_count > 0 else max(len(sources), 1)
        )

        card: dict[str, Any] = {
            "global_event_id": event_id,
            "sector": sector,
            "primary_sector": str(row.get("primary_sector") or sector).strip() or sector,
            "title": "",
            "summary": "",
            "title_vi": "",
            "summary_vi": "",
            "importance_reason": "",
            "num_articles": max(num_articles, 1),
            "source_count": source_count,
            "sentiment_tone": round(tone, 2),
            "sentiment_label": sentiment_label_vi(tone),
            "entities": entities,
            "sources": sources[:MAX_MENTIONS_PER_EVENT],
            "impact_score": impact_score(
                rank,
                tone,
                max_rank=max(
                    INVEST_BQ_OUTPUT_LIMIT if channel == "invest" else BQ_OUTPUT_LIMIT,
                    1,
                ),
            ),
            "primary_actor": actor,
            "secondary_actor": actor2,
            "article_mentions": max(num_articles, 1),
            "gkg_organizations": str(row.get("Cac_To_Chuc_Lien_Quan") or ""),
            "gkg_persons": str(row.get("V2Persons") or ""),
            "gkg_locations": str(row.get("V2Locations") or ""),
        }
        if channel == "invest":
            sec = str(row.get("secondary_sector") or "").strip()
            card["secondary_sector"] = sec if sec else None
            card["macro_signal"] = str(row.get("macro_signal") or "neutral").strip() or "neutral"
            card["risk_flags"] = list(row.get("risk_flags") or [])
            card["affected_assets"] = list(row.get("affected_assets") or [])
            card["investment_relevance"] = str(row.get("investment_relevance") or "").strip() or "medium"
        events.append(card)

    if channel == "invest":
        events.sort(key=lambda e: (int(e.get("num_articles") or 0),), reverse=True)
        events = events[:INVEST_MAX_ENRICH_EVENTS]
    else:
        events.sort(key=lambda e: (e.get("num_articles") or 0), reverse=True)
    LOG.info("GDELT hot events (GlobalEventID): %s", len(events))
    return expand_event_sources(events, df)


# ---------------------------------------------------------------------------
# Gemini story dedupe (same real-world incident, multiple GlobalEventIDs)
# ---------------------------------------------------------------------------


def _event_dedupe_brief(ev: dict[str, Any]) -> str:
    eid = str(ev.get("global_event_id") or "")
    sector = str(ev.get("sector") or "")
    title = str(ev.get("title_vi") or ev.get("title") or "").strip()[:120]
    summary = str(ev.get("summary_vi") or ev.get("summary") or "").strip()[:160]
    num = int(ev.get("num_articles") or 0)
    return f"id={eid} | {num} bài | {sector} | {title} | {summary}"


def _parse_gemini_clusters(text: str) -> list[dict[str, Any]]:
    raw = (text or "").strip()
    if not raw:
        return []
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, flags=re.DOTALL)
    if fence:
        raw = fence.group(1).strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start >= 0 and end > start:
        raw = raw[start : end + 1]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    clusters = data.get("clusters") if isinstance(data, dict) else None
    return clusters if isinstance(clusters, list) else []


def gemini_cluster_duplicate_events(events: list[dict[str, Any]]) -> list[list[str]]:
    """Return clusters of global_event_id strings that describe the same news story."""
    if not _configure_gemini() or len(events) < 2:
        return [[str(e.get("global_event_id") or "")] for e in events]

    by_id = {str(e.get("global_event_id") or ""): e for e in events if e.get("global_event_id")}
    lines = "\n".join(f"{i + 1}. {_event_dedupe_brief(ev)}" for i, ev in enumerate(events))
    model_name = os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL
    model = genai.GenerativeModel(model_name)
    prompt = f"""
Bạn là biên tập bản tin quốc tế. Dưới đây là các sự kiện từ GDELT (mỗi dòng một GlobalEventID).

Nhiệm vụ: gom các dòng mô tả CÙNG MỘT vụ việc/câu chuyện tin thực tế trong 24h qua.
- Gom khi cùng sự kiện (vd. nhiều mã GDELT cho vụ nổ súng Nhà Trắng, Sudbury Credit Union food bank).
- KHÔNG gom chỉ vì cùng sector, cùng quốc gia, hoặc cùng nhân vật nhưng khác vụ.
- Mỗi id chỉ thuộc đúng một cluster.

Trả về JSON (không markdown):
{{
  "clusters": [
    {{
      "keep_id": "GlobalEventID đại diện (ưu tiên sự kiện có nhiều bài hơn trong cluster)",
      "member_ids": ["id1", "id2"],
      "reason": "một câu tiếng Việt"
    }}
  ]
}}

Danh sách sự kiện:
{lines}
""".strip()

    try:
        response = model.generate_content(prompt)
        clusters_raw = _parse_gemini_clusters(response.text or "")
    except Exception as exc:
        LOG.warning("Gemini dedupe failed: %s", exc)
        return [[eid] for eid in by_id]

    assigned: set[str] = set()
    out: list[list[str]] = []
    for cluster in clusters_raw:
        if not isinstance(cluster, dict):
            continue
        members = [str(x).strip() for x in (cluster.get("member_ids") or []) if str(x).strip()]
        keep_id = str(cluster.get("keep_id") or "").strip()
        if keep_id and keep_id not in members:
            members.insert(0, keep_id)
        members = [m for m in members if m in by_id and m not in assigned]
        if not members:
            continue
        if keep_id in by_id and keep_id in members:
            members = [keep_id] + [m for m in members if m != keep_id]
        assigned.update(members)
        out.append(members)

    for eid in by_id:
        if eid not in assigned:
            out.append([eid])
    return out


def _merge_url_list(*lists: list[str], limit: int = MAX_MENTIONS_PER_EVENT) -> list[str]:
    return _dedupe_mention_urls(
        [url for lst in lists for url in (lst or [])],
        limit=limit,
    )


def _pick_representative_event(
    members: list[dict[str, Any]], *, channel: str = "world"
) -> dict[str, Any]:
    def score(ev: dict[str, Any]) -> tuple[int, int, int]:
        title_ok = 1 if _usable_title(ev.get("title_vi") or ev.get("title")) else 0
        return (int(ev.get("num_articles") or 0), int(ev.get("source_count") or 0), title_ok)

    return max(members, key=score)


def merge_event_cluster(
    members: list[dict[str, Any]], *, channel: str = "world"
) -> dict[str, Any]:
    """Mechanical merge after Gemini groups same-story GlobalEventIDs."""
    if not members:
        return {}
    if len(members) == 1:
        return dict(members[0])

    rep = _pick_representative_event(members, channel=channel)
    merged = dict(rep)
    merged_ids = [str(m.get("global_event_id") or "") for m in members if m.get("global_event_id")]
    merged["global_event_id"] = str(rep.get("global_event_id") or "")
    merged["merged_event_ids"] = merged_ids
    merged["num_articles"] = max(int(m.get("num_articles") or 0) for m in members)
    merged["article_mentions"] = merged["num_articles"]
    merged["sources"] = _merge_url_list(*[list(m.get("sources") or []) for m in members])
    merged["source_count"] = max(int(m.get("source_count") or 0) for m in members)
    merged["entities"] = _merge_entity_lists(*[list(m.get("entities") or []) for m in members], limit=8)
    tones = [float(m.get("sentiment_tone") or 0) for m in members]
    merged["sentiment_tone"] = round(rep.get("sentiment_tone") or (sum(tones) / len(tones)), 2)
    merged["sentiment_label"] = sentiment_label_vi(float(merged["sentiment_tone"]))
    merged["impact_score"] = max(int(m.get("impact_score") or 0) for m in members)
    return merged


def dedupe_events_with_gemini(
    events: list[dict[str, Any]], *, use_gemini: bool = True, channel: str = "world"
) -> list[dict[str, Any]]:
    """Collapse duplicate GDELT stories via one Gemini clustering pass."""
    if len(events) < 2 or not use_gemini:
        return events

    LOG.info("Gemini dedupe clustering for %s events", len(events))
    by_id = {str(e.get("global_event_id") or ""): e for e in events if e.get("global_event_id")}
    clusters = gemini_cluster_duplicate_events(events)
    time.sleep(GEMINI_CALL_INTERVAL_SEC)

    merged: list[dict[str, Any]] = []
    for member_ids in clusters:
        group = [by_id[i] for i in member_ids if i in by_id]
        if not group:
            continue
        if len(group) > 1:
            LOG.info(
                "Dedupe merge %s events -> keep %s (%s)",
                len(group),
                _pick_representative_event(group, channel=channel).get("global_event_id"),
                member_ids,
            )
        card = merge_event_cluster(group, channel=channel)
        if card:
            merged.append(card)

    merged.sort(key=lambda e: (int(e.get("num_articles") or 0),), reverse=True)
    LOG.info("After Gemini dedupe: %s events (from %s)", len(merged), len(events))
    if channel == "invest":
        merged = gemini_curate_invest_feed(merged, use_gemini=use_gemini)
    elif channel == "world":
        merged = merged[:TARGET_HOT_EVENTS]
    return merged


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def _sources_for_export(raw: Any) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in raw or []:
        if isinstance(item, dict):
            url = _normalize_mention_url(str(item.get("url") or "").strip())
            if not url.startswith("http"):
                continue
            key = _mention_url_dedupe_key(url)
            if key in seen:
                continue
            seen.add(key)
            out.append(
                {
                    "url": url,
                    "name": str(item.get("name") or "").strip() or _source_label_from_url(url),
                }
            )
            continue
        url = _normalize_mention_url(str(item or "").strip())
        if not url.startswith("http"):
            continue
        key = _mention_url_dedupe_key(url)
        if key in seen:
            continue
        seen.add(key)
        out.append({"url": url, "name": _source_label_from_url(url)})
    return out


def _public_event(ev: dict[str, Any], *, channel: str = "world") -> dict[str, Any]:
    """Slim card for web export (no GDELT debug fields or duplicate feed arrays)."""
    base = {
        "global_event_id": str(ev.get("global_event_id") or ""),
        "sector": str(ev.get("primary_sector") or ev.get("sector") or "Khác"),
        "title": str(ev.get("title_vi") or ev.get("title") or "").strip(),
        "summary": str(ev.get("summary_vi") or ev.get("summary") or "").strip(),
        "importance_reason": str(ev.get("importance_reason") or "").strip(),
        "num_articles": int(ev.get("num_articles") or 0),
        "source_count": int(ev.get("source_count") or 0),
        "sentiment_tone": ev.get("sentiment_tone"),
        "sentiment_label": str(ev.get("sentiment_label") or ""),
        "entities": list(ev.get("entities") or []),
        "sources": _sources_for_export(ev.get("sources") or []),
    }
    if channel != "invest":
        base["sources"] = [s["url"] for s in base["sources"]]
        return base
    base.update(
        {
            "primary_sector": str(ev.get("primary_sector") or ev.get("sector") or "Khác"),
            "secondary_sector": str(ev.get("secondary_sector") or "").strip() or None,
            "macro_signal": str(ev.get("macro_signal") or "neutral"),
            "risk_flags": list(ev.get("risk_flags") or []),
            "affected_assets": list(ev.get("affected_assets") or []),
            "investment_relevance": str(ev.get("investment_relevance") or ""),
        }
    )
    return base


def build_payload(events: list[dict[str, Any]], *, channel: str = "world") -> dict[str, Any]:
    public = [_public_event(ev, channel=channel) for ev in events]
    schema = INVEST_PULSE_SCHEMA_VERSION if channel == "invest" else PULSE_SCHEMA_VERSION
    return {
        "schema_version": schema,
        "channel": channel,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_events": len(public),
        "events": public,
    }


def atomic_export_json(payload: dict[str, Any], output_path: Path) -> Path:
    """Write .tmp.json then os.replace — safe for concurrent web reads."""
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_suffix(".tmp.json")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(output_path)
    LOG.info("Wrote %s (%s events)", output_path, payload.get("total_events", 0))
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
        "--channel",
        choices=("world", "invest"),
        default=os.environ.get("LEON_PULSE_CHANNEL", "world"),
        help="world = LIVE đa lĩnh vực; invest = chuyên mục kinh tế đầu tư",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON path (default: market_pulse.json or invest_pulse.json)",
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

    channel = str(args.channel or "world").strip().lower()
    if channel not in ("world", "invest"):
        channel = "world"
    default_out = DEFAULT_INVEST_OUTPUT if channel == "invest" else DEFAULT_OUTPUT
    env_out = os.environ.get(
        "LEON_INVEST_PULSE_OUTPUT" if channel == "invest" else "LEON_PULSE_OUTPUT", ""
    ).strip()
    output: Path = args.output or Path(env_out or default_out)
    LOG.info("Leon Web Intel [%s] → %s (dry_run=%s)", channel, output, args.dry_run)

    try:
        client = get_bigquery_client()
    except Exception as exc:
        LOG.error("BigQuery client setup failed: %s", exc)
        return 1

    try:
        df, meta = run_bigquery(
            client,
            channel=channel,
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
    events = build_events_from_bq(cleaned, channel=channel)
    LOG.info("Events after EventMentions-only sources: %s", len(events))
    if events:
        use_gemini = not args.no_gemini
        LOG.info(
            "Gemini enrichment for %s events (gemini=%s, timeout=%ss)",
            len(events),
            use_gemini,
            FETCH_TITLE_TIMEOUT,
        )
        events = enrich_events_for_web(events, use_gemini=use_gemini, channel=channel)
        events = filter_event_sources_with_gemini(events, use_gemini=use_gemini)
        events = dedupe_events_with_gemini(events, use_gemini=use_gemini, channel=channel)
    else:
        events = events[:TARGET_HOT_EVENTS]
    payload = build_payload(events, channel=channel)
    url_count = sum(len(ev.get("sources") or []) for ev in payload.get("events") or [])
    LOG.info("Exported %s hot events, %s source URLs", len(events), url_count)
    try:
        atomic_export_json(payload, output)
        # Mirror for GitHub Pages static path
        web_name = "invest_pulse.json" if channel == "invest" else "market_pulse.json"
        web_mirror = PROJECT_DIR / "web" / web_name
        if output.resolve() != web_mirror.resolve():
            atomic_export_json(payload, web_mirror)
        if channel == "invest" and output.resolve() != (PROJECT_DIR / "invest_pulse.json").resolve():
            atomic_export_json(payload, PROJECT_DIR / "invest_pulse.json")
    except OSError as exc:
        LOG.error("Export failed: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
