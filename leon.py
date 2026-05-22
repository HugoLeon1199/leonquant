#!/usr/bin/env python3
"""
Leon World Pulse — GDELT BigQuery radar (multi-domain).

Separate from the 48h crawl + Gemini digest (content.json).
Exports: web/news_data.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse
from urllib.request import urlopen

import pandas as pd
import yaml
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
from google.oauth2 import service_account

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = PROJECT_DIR / "config" / "gdelt_pipeline.yaml"

LOG = logging.getLogger("leon.gdelt")

DOC_API_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"
DOC_MODE_QUERIES: dict[str, str] = {
    "all": (
        "(economy OR finance OR politics OR government OR election OR war OR conflict "
        "OR technology OR artificial intelligence OR health OR climate OR crypto OR bitcoin)"
    ),
    "finance": "(economy OR markets OR stocks OR inflation OR central bank OR trade OR banking)",
    "politics": "(politics OR government OR election OR diplomacy OR parliament OR president)",
    "conflict": "(war OR military OR armed conflict OR terrorism OR missile OR ceasefire)",
    "tech": "(technology OR artificial intelligence OR cyber OR semiconductor OR software)",
    "science": "(science OR research OR space OR NASA OR physics OR biology)",
    "health": "(health OR pandemic OR vaccine OR hospital OR disease OR medical)",
    "climate": "(climate OR environment OR carbon OR emissions OR flood OR wildfire)",
    "crypto": "(crypto OR bitcoin OR blockchain OR ethereum OR digital assets)",
}

DOMAIN_LABELS = {
    "finance": "Kinh tế & Tài chính",
    "politics": "Thời sự & Chính trị",
    "conflict": "Xung đột & An ninh",
    "tech": "Công nghệ & AI",
    "science": "Khoa học",
    "health": "Y tế",
    "climate": "Khí hậu & Môi trường",
    "crypto": "Tiền số",
    "all": "Toàn cầu",
}


def load_config(path: Path | None = None) -> dict[str, Any]:
    cfg_path = path or Path(os.environ.get("GDELT_CONFIG_PATH", DEFAULT_CONFIG_PATH))
    if not cfg_path.is_file():
        raise FileNotFoundError(f"Config not found: {cfg_path}")
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    cfg["_config_path"] = str(cfg_path)
    cfg["output_path"] = os.environ.get("GDELT_OUTPUT_PATH", cfg.get("output_path", "web/news_data.json"))
    if os.environ.get("GDELT_MAX_BYTES_BILLED"):
        cfg["maximum_bytes_billed"] = int(os.environ["GDELT_MAX_BYTES_BILLED"])
    return cfg


def get_bigquery_client(cfg: dict[str, Any]) -> bigquery.Client:
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT") or cfg.get("project_id")

    if creds_path and Path(creds_path).is_file():
        credentials = service_account.Credentials.from_service_account_file(creds_path)
        return bigquery.Client(project=project or credentials.project_id, credentials=credentials)

    local = PROJECT_DIR / "credentials.json"
    if local.is_file():
        LOG.warning("Using local credentials.json (dev only). Prefer GOOGLE_APPLICATION_CREDENTIALS.")
        credentials = service_account.Credentials.from_service_account_file(str(local))
        return bigquery.Client(project=project or credentials.project_id, credentials=credentials)

    return bigquery.Client(project=project)


def _mode_cfg(cfg: dict[str, Any], mode: str) -> dict[str, Any]:
    modes = cfg.get("modes") or {}
    if mode not in modes:
        raise ValueError(f"Unknown mode '{mode}'. Choose from: {', '.join(sorted(modes))}")
    return modes[mode]


def build_query(
    cfg: dict[str, Any],
    *,
    mode: str,
    lookback_hours: int,
    limit: int,
) -> tuple[str, list[bigquery.ScalarQueryParameter | bigquery.QueryParameter]]:
    m = _mode_cfg(cfg, mode)
    theme_regex = str(m.get("theme_regex") or ".*")
    prefixes = m.get("event_root_prefixes") or []
    prefix_conditions = " OR ".join(
        f"CAST(e.EventRootCode AS STRING) LIKE '{p}%'" for p in prefixes[:25]
    ) or "TRUE"
    theme_clause = (
        f"(g.V2Themes IS NOT NULL AND REGEXP_CONTAINS(g.V2Themes, @theme_regex)) "
        f"OR ({prefix_conditions})"
    )

    sql = f"""
SELECT
  e.SQLDATE,
  e.SQLTIME,
  e.Actor1Name,
  e.Actor2Name,
  e.EventRootCode,
  e.EventCode,
  e.GoldsteinScale,
  e.AvgTone,
  e.NumArticles,
  e.NumMentions,
  e.SOURCEURL,
  g.V2Themes,
  g.V2Organizations,
  g.V2Persons,
  g.V2Locations,
  g.V2Tone
FROM `gdelt-bq.gdeltv2.events_partitioned` AS e
LEFT JOIN `gdelt-bq.gdeltv2.gkg_partitioned` AS g
  ON e.SOURCEURL = g.DocumentIdentifier
 AND g._PARTITIONTIME >= @since_ts
WHERE e._PARTITIONTIME >= @since_ts
  AND e.SOURCEURL IS NOT NULL
  AND LENGTH(e.SOURCEURL) > 10
  AND e.NumMentions >= 1
  AND ({theme_clause})
ORDER BY e.NumMentions DESC, e.NumArticles DESC
LIMIT @row_limit
"""
    params: list[bigquery.ScalarQueryParameter] = [
        bigquery.ScalarQueryParameter("theme_regex", "STRING", theme_regex),
        bigquery.ScalarQueryParameter("row_limit", "INT64", int(limit)),
    ]
    return sql.strip(), params


def run_query(
    client: bigquery.Client,
    sql: str,
    params: list[bigquery.QueryParameter],
    *,
    cfg: dict[str, Any],
    lookback_hours: int,
    dry_run: bool = False,
) -> tuple[pd.DataFrame | None, dict[str, Any]]:
    since = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    resolved: list[bigquery.ScalarQueryParameter] = [
        bigquery.ScalarQueryParameter("since_ts", "TIMESTAMP", since),
        *params,
    ]

    job_config = bigquery.QueryJobConfig(
        query_parameters=resolved,
        maximum_bytes_billed=int(cfg.get("maximum_bytes_billed", 500_000_000)),
        job_timeout_ms=int(cfg.get("job_timeout_ms", 120_000)),
        dry_run=dry_run,
        use_query_cache=not dry_run,
    )

    meta: dict[str, Any] = {"lookback_hours": lookback_hours, "since_utc": since.isoformat(), "dry_run": dry_run}
    try:
        job = client.query(sql, job_config=job_config)
        if dry_run:
            meta["total_bytes_processed"] = job.total_bytes_processed
            meta["total_gb"] = round((job.total_bytes_processed or 0) / 1e9, 4)
            LOG.info("Dry-run: ~%s GB (%s bytes)", meta["total_gb"], meta["total_bytes_processed"])
            return None, meta
        df = job.result(timeout=job_config.job_timeout_ms / 1000).to_dataframe()
        meta["bytes_processed"] = job.total_bytes_processed
        meta["row_count"] = len(df)
        return df, meta
    except GoogleCloudError as exc:
        LOG.error("BigQuery failed: %s", exc)
        raise


def _parse_semicolon_field(raw: Any, limit: int = 12) -> list[str]:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return []
    text = str(raw).strip()
    if not text:
        return []
    parts = [p.split(",")[0].strip() for p in text.split(";") if p.strip()]
    out: list[str] = []
    for p in parts:
        if p and p not in out:
            out.append(p)
        if len(out) >= limit:
            break
    return out


def _sql_datetime(row: pd.Series) -> datetime | None:
    try:
        d = int(row.get("SQLDATE") or 0)
        t = int(row.get("SQLTIME") or 0)
        if d < 19700101:
            return None
        ds = str(d)
        ts = str(t).zfill(6)
        return datetime(
            int(ds[0:4]),
            int(ds[4:6]),
            int(ds[6:8]),
            int(ts[0:2]),
            int(ts[2:4]),
            int(ts[4:6]),
            tzinfo=timezone.utc,
        )
    except (TypeError, ValueError):
        return None


def _infer_domain(themes: list[str], mode: str) -> str:
    blob = " ".join(themes).upper()
    rules = [
        ("crypto", ("CRYPTO", "BITCOIN", "BLOCKCHAIN", "ETHEREUM")),
        ("conflict", ("WAR_", "MILITARY", "ARMEDCONFLICT", "TERROR", "MISSILE")),
        ("finance", ("ECON_", "FIN_", "TAX_", "STOCK", "MARKET", "TRADE", "BANK")),
        ("tech", ("TECH_", "ARTIFICIALINTELLIGENCE", "CYBER", "SEMICONDUCTOR")),
        ("health", ("HEALTH", "MED_", "PANDEMIC", "VACCINE", "DISEASE")),
        ("climate", ("ENV_", "CLIMATE", "CARBON", "EMISSION", "FLOOD")),
        ("science", ("SCI_", "RESEARCH", "SPACE", "NASA")),
        ("politics", ("POLITIC", "GOV_", "ELECTION", "DEMOCRACY", "DIPLOMACY")),
    ]
    for code, keys in rules:
        if any(k in blob for k in keys):
            return code
    return mode if mode != "all" else "politics"


def _infer_region(locations: list[str], actors: list[str]) -> str:
    blob = " ".join(locations + actors).upper()
    if any(x in blob for x in ("VIETNAM", "VN", "HANOI", "HO CHI MINH")):
        return "vietnam"
    if any(x in blob for x in ("UNITED STATES", "US", "WASHINGTON", "NEW YORK")):
        return "us"
    if any(x in blob for x in ("CHINA", "BEIJING", "SHANGHAI")):
        return "china"
    if any(x in blob for x in ("EUROPE", "EU", "BRUSSELS", "GERMANY", "FRANCE", "UK")):
        return "europe"
    if any(x in blob for x in ("MIDDLE EAST", "IRAN", "ISRAEL", "GAZA", "SAUDI")):
        return "middle_east"
    return "global"


def _title_from_row(row: pd.Series, themes: list[str], actors: list[str]) -> str:
    a1 = str(row.get("Actor1Name") or "").strip()
    a2 = str(row.get("Actor2Name") or "").strip()
    if a1 and a2:
        return f"{a1} — {a2}"
    if a1:
        return a1
    if themes:
        return themes[0].replace("_", " ").title()[:120]
    url = str(row.get("SOURCEURL") or "")
    if url:
        try:
            return urlparse(url).netloc.replace("www.", "")
        except Exception:
            pass
    return "Sự kiện GDELT"


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["SOURCEURL"] = out["SOURCEURL"].astype(str).str.strip()
    out = out[out["SOURCEURL"].str.startswith("http", na=False)]
    out = out.drop_duplicates(subset=["SOURCEURL"], keep="first")
    for col in ("NumArticles", "NumMentions", "GoldsteinScale", "AvgTone"):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    return out.reset_index(drop=True)


def score_events(
    df: pd.DataFrame,
    *,
    cfg: dict[str, Any],
    mode: str,
    lookback_hours: int,
) -> pd.DataFrame:
    if df.empty:
        return df
    sw = cfg.get("scoring") or {}
    m = _mode_cfg(cfg, mode)
    theme_boost = float(m.get("theme_weight") or 1.0)
    now = datetime.now(timezone.utc)

    rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        themes = _parse_semicolon_field(row.get("V2Themes"))
        orgs = _parse_semicolon_field(row.get("V2Organizations"))
        persons = _parse_semicolon_field(row.get("V2Persons"))
        locations = _parse_semicolon_field(row.get("V2Locations"))
        actors = [x for x in (str(row.get("Actor1Name") or ""), str(row.get("Actor2Name") or "")) if x.strip()]
        published = _sql_datetime(row)
        recency = 0.0
        if published:
            age_h = max(0.0, (now - published).total_seconds() / 3600.0)
            recency = max(0.0, 1.0 - min(age_h / max(lookback_hours, 1), 1.0))

        na = float(row.get("NumArticles") or 0)
        nm = float(row.get("NumMentions") or 0)
        tone = abs(float(row.get("AvgTone") or 0))
        gold = abs(float(row.get("GoldsteinScale") or 0))
        theme_hits = len(themes)

        score = (
            (na**0.5) * float(sw.get("articles_weight", 2.0))
            + (nm**0.5) * float(sw.get("mentions_weight", 2.5))
            + recency * float(sw.get("recency_weight", 3.0))
            + min(tone, 25) / 25.0 * float(sw.get("tone_weight", 1.0))
            + min(gold, 10) / 10.0 * float(sw.get("goldstein_weight", 1.5))
            + min(theme_hits, 8) / 8.0 * float(sw.get("theme_mode_weight", 1.0)) * theme_boost
        )
        domain = _infer_domain(themes, mode)
        rows.append(
            {
                **row.to_dict(),
                "themes_list": themes,
                "orgs_list": orgs,
                "persons_list": persons,
                "locations_list": locations,
                "actors_list": actors,
                "published_at": published.isoformat() if published else None,
                "domain_code": domain,
                "region_code": _infer_region(locations, actors + orgs),
                "title_guess": _title_from_row(row, themes, actors),
                "final_importance_score": round(score, 4),
            }
        )
    scored = pd.DataFrame(rows)
    return scored.sort_values("final_importance_score", ascending=False).reset_index(drop=True)


def _cluster_key(row: dict[str, Any], bucket_hours: int) -> str:
    title = re.sub(r"\s+", " ", str(row.get("title_guess") or "").lower())[:80]
    domain = str(row.get("domain_code") or "")
    themes = ",".join(sorted((row.get("themes_list") or [])[:3]))
    actors = ",".join(sorted((row.get("actors_list") or [])[:2]))
    published = row.get("published_at") or ""
    bucket = ""
    if published:
        try:
            dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
            bucket = str(int(dt.timestamp() // (bucket_hours * 3600)))
        except ValueError:
            bucket = published[:10]
    raw = f"{domain}|{themes}|{actors}|{title}|{bucket}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def cluster_events(df: pd.DataFrame, *, cfg: dict[str, Any]) -> list[dict[str, Any]]:
    if df.empty:
        return []
    bucket_h = int((cfg.get("clustering") or {}).get("time_bucket_hours") or 6)
    clusters: dict[str, dict[str, Any]] = {}

    for _, row in df.iterrows():
        r = row.to_dict()
        key = _cluster_key(r, bucket_h)
        url = str(r.get("SOURCEURL") or "").strip()
        if key not in clusters:
            clusters[key] = {
                "cluster_key": key,
                "title": r.get("title_guess") or "Sự kiện",
                "domain": r.get("domain_code") or "all",
                "region": r.get("region_code") or "global",
                "importance_score": float(r.get("final_importance_score") or 0),
                "tone": float(r.get("AvgTone") or 0),
                "actors": list(r.get("actors_list") or []),
                "organizations": list(r.get("orgs_list") or []),
                "locations": list(r.get("locations_list") or []),
                "themes": list(r.get("themes_list") or []),
                "summary_hint": _summary_hint(r),
                "urls": [],
                "published_at": r.get("published_at"),
                "_rows": 1,
            }
        c = clusters[key]
        if url and url not in c["urls"]:
            c["urls"].append(url)
        c["importance_score"] = max(c["importance_score"], float(r.get("final_importance_score") or 0))
        c["_rows"] += 1
        if r.get("published_at") and (not c.get("published_at") or r["published_at"] > c["published_at"]):
            c["published_at"] = r["published_at"]

    events: list[dict[str, Any]] = []
    for key, c in sorted(clusters.values(), key=lambda x: x["importance_score"], reverse=True):
        eid = f"evt_{key}"
        events.append(
            {
                "id": eid,
                "title": c["title"],
                "domain": c["domain"],
                "domain_label": DOMAIN_LABELS.get(c["domain"], c["domain"]),
                "region": c["region"],
                "importance_score": round(c["importance_score"], 4),
                "tone": round(c["tone"], 2),
                "actors": c["actors"][:8],
                "organizations": c["organizations"][:8],
                "locations": c["locations"][:8],
                "themes": c["themes"][:12],
                "summary_hint": c["summary_hint"],
                "urls": c["urls"][:10],
                "source_count": len(c["urls"]),
                "published_at": c.get("published_at"),
                "cluster_size": c["_rows"],
            }
        )
    return events


def _summary_hint(row: dict[str, Any]) -> str:
    parts: list[str] = []
    if row.get("actors_list"):
        parts.append("Tác nhân: " + ", ".join(row["actors_list"][:3]))
    if row.get("themes_list"):
        parts.append("Chủ đề: " + ", ".join(t.replace("_", " ") for t in row["themes_list"][:4]))
    tone = row.get("AvgTone")
    if tone is not None:
        parts.append(f"Sắc thái trung bình: {float(tone):.1f}")
    gs = row.get("GoldsteinScale")
    if gs is not None and float(gs) != 0:
        parts.append(f"Goldstein: {float(gs):.1f}")
    return ". ".join(parts)[:400] if parts else "Sự kiện từ GDELT (xem nguồn)."


def export_json(
    payload: dict[str, Any],
    output_path: Path,
) -> Path:
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_suffix(".tmp.json")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(output_path)
    LOG.info("Wrote %s (%s events)", output_path, len(payload.get("events") or []))
    return output_path


def _parse_doc_seendate(raw: str | None) -> datetime | None:
    if not raw:
        return None
    text = str(raw).strip()
    try:
        if "T" in text and text.endswith("Z"):
            return datetime.strptime(text, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        return datetime.strptime(text[:8], "%Y%m%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _infer_domain_from_text(blob: str, mode: str) -> str:
    return _infer_domain([blob.upper().replace(" ", "_")], mode)


def fetch_doc_articles(
    *,
    query: str,
    lookback_hours: int,
    maxrecords: int,
) -> list[dict[str, Any]]:
    timespan = f"{max(1, min(lookback_hours, 168))}h"
    params = {
        "query": query,
        "mode": "ArtList",
        "maxrecords": str(min(max(maxrecords, 1), 250)),
        "timespan": timespan,
        "format": "json",
        "sort": "DateDesc",
    }
    url = f"{DOC_API_BASE}?{urlencode(params)}"
    LOG.info("GDELT DOC API: %s records, timespan=%s", params["maxrecords"], timespan)
    with urlopen(url, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return list(data.get("articles") or [])


def articles_to_dataframe(articles: list[dict[str, Any]], *, mode: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for art in articles:
        url = str(art.get("url") or "").strip()
        if not url.startswith("http"):
            continue
        title = str(art.get("title") or "").strip() or url
        published = _parse_doc_seendate(art.get("seendate"))
        country = str(art.get("sourcecountry") or "").strip()
        domain = str(art.get("domain") or "").strip()
        blob = f"{title} {domain} {country}"
        rows.append(
            {
                "SOURCEURL": url,
                "title_guess": title[:200],
                "NumArticles": 1,
                "NumMentions": 1,
                "AvgTone": 0.0,
                "GoldsteinScale": 0.0,
                "V2Themes": "",
                "V2Organizations": "",
                "V2Persons": "",
                "V2Locations": country,
                "Actor1Name": "",
                "Actor2Name": "",
                "published_at": published.isoformat() if published else None,
                "domain_code": _infer_domain_from_text(blob, mode),
                "region_code": _infer_region([country], [country]),
                "themes_list": [],
                "orgs_list": [],
                "persons_list": [],
                "locations_list": [country] if country else [],
                "actors_list": [],
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).drop_duplicates(subset=["SOURCEURL"], keep="first").reset_index(drop=True)


def score_doc_articles(df: pd.DataFrame, *, cfg: dict[str, Any], mode: str, lookback_hours: int) -> pd.DataFrame:
    if df.empty:
        return df
    sw = cfg.get("scoring") or {}
    m = _mode_cfg(cfg, mode)
    theme_boost = float(m.get("theme_weight") or 1.0)
    now = datetime.now(timezone.utc)
    scores: list[float] = []
    for _, row in df.iterrows():
        published = None
        if row.get("published_at"):
            try:
                published = datetime.fromisoformat(str(row["published_at"]).replace("Z", "+00:00"))
            except ValueError:
                published = None
        recency = 0.0
        if published:
            age_h = max(0.0, (now - published).total_seconds() / 3600.0)
            recency = max(0.0, 1.0 - min(age_h / max(lookback_hours, 1), 1.0))
        domain_code = str(row.get("domain_code") or "")
        domain_match = 1.15 if mode != "all" and domain_code == mode else 1.0
        score = (
            recency * float(sw.get("recency_weight", 3.0)) * 2.0
            + float(sw.get("articles_weight", 2.0))
            + float(sw.get("mentions_weight", 2.5)) * 0.5
        ) * theme_boost * domain_match
        scores.append(round(score, 4))
    out = df.copy()
    out["final_importance_score"] = scores
    return out.sort_values("final_importance_score", ascending=False).reset_index(drop=True)


def cluster_doc_events(df: pd.DataFrame, *, cfg: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    if df.empty:
        return []
    bucket_h = int((cfg.get("clustering") or {}).get("time_bucket_hours") or 6)
    clusters: dict[str, dict[str, Any]] = {}
    for _, row in df.iterrows():
        r = row.to_dict()
        key = _cluster_key(r, bucket_h)
        url = str(r.get("SOURCEURL") or "").strip()
        if key not in clusters:
            clusters[key] = {
                "cluster_key": key,
                "title": r.get("title_guess") or "Sự kiện",
                "domain": r.get("domain_code") or "all",
                "region": r.get("region_code") or "global",
                "importance_score": float(r.get("final_importance_score") or 0),
                "tone": 0.0,
                "actors": [],
                "organizations": [],
                "locations": list(r.get("locations_list") or [])[:8],
                "themes": [],
                "summary_hint": "",
                "urls": [],
                "published_at": r.get("published_at"),
                "_rows": 1,
            }
        c = clusters[key]
        if url and url not in c["urls"]:
            c["urls"].append(url)
        c["importance_score"] = max(c["importance_score"], float(r.get("final_importance_score") or 0))
        loc = list(r.get("locations_list") or [])
        for x in loc:
            if x and x not in c["locations"]:
                c["locations"].append(x)
        if r.get("published_at") and (not c.get("published_at") or r["published_at"] > c["published_at"]):
            c["published_at"] = r["published_at"]
        if not c["summary_hint"] and c["locations"]:
            c["summary_hint"] = "Nguồn: " + ", ".join(c["locations"][:3])

    events: list[dict[str, Any]] = []
    for c in sorted(clusters.values(), key=lambda x: x["importance_score"], reverse=True)[:limit]:
        key = c["cluster_key"]
        events.append(
            {
                "id": f"evt_{key}",
                "title": c["title"],
                "domain": c["domain"],
                "domain_label": DOMAIN_LABELS.get(c["domain"], c["domain"]),
                "region": c["region"],
                "importance_score": round(c["importance_score"], 4),
                "tone": 0.0,
                "actors": c["actors"][:8],
                "organizations": c["organizations"][:8],
                "locations": c["locations"][:8],
                "themes": c["themes"][:12],
                "summary_hint": c["summary_hint"] or "Tin từ GDELT DOC (xem nguồn).",
                "urls": c["urls"][:10],
                "source_count": len(c["urls"]),
                "published_at": c.get("published_at"),
                "cluster_size": c["_rows"],
            }
        )
    return events


def run_doc_pipeline(
    cfg: dict[str, Any],
    *,
    mode: str,
    lookback_hours: int,
    limit: int,
    output: Path,
) -> int:
    query = DOC_MODE_QUERIES.get(mode)
    if not query:
        LOG.error("No DOC query for mode %s", mode)
        return 2
    try:
        articles = fetch_doc_articles(query=query, lookback_hours=lookback_hours, maxrecords=min(limit * 3, 250))
    except Exception as exc:
        LOG.error("GDELT DOC API failed: %s", exc)
        return 1
    if not articles:
        LOG.warning("DOC API returned 0 articles; keeping existing %s if present", output)
        return 0
    df = articles_to_dataframe(articles, mode=mode)
    scored = score_doc_articles(df, cfg=cfg, mode=mode, lookback_hours=lookback_hours)
    events = cluster_doc_events(scored, cfg=cfg, limit=limit)
    payload = build_payload(
        events,
        lookback_hours=lookback_hours,
        total_raw_rows=len(articles),
        mode=mode,
        query_meta={"source": "gdelt-doc-api", "query": query[:200]},
        pipeline="leon-gdelt-doc-api",
    )
    export_json(payload, output)
    return 0


def build_payload(
    events: list[dict[str, Any]],
    *,
    lookback_hours: int,
    total_raw_rows: int,
    mode: str,
    query_meta: dict[str, Any],
    pipeline: str = "leon-gdelt-bigquery",
) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pipeline": pipeline,
        "mode": mode,
        "lookback_hours": lookback_hours,
        "total_raw_rows": total_raw_rows,
        "total_events": len(events),
        "query_meta": query_meta,
        "events": events,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Leon GDELT World Pulse (BigQuery or DOC API)")
    p.add_argument(
        "--source",
        choices=("bigquery", "doc"),
        default="bigquery",
        help="bigquery=GCP BQ; doc=free GDELT DOC API (no credentials)",
    )
    p.add_argument("--config", type=Path, default=None, help="Path to gdelt_pipeline.yaml")
    p.add_argument(
        "--mode",
        default="all",
        help="Domain mode: all, finance, politics, conflict, tech, science, health, climate, crypto",
    )
    p.add_argument("--lookback-hours", type=int, default=None)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--dry-run", action="store_true", help="Estimate bytes only; no export")
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    try:
        cfg = load_config(args.config)
    except FileNotFoundError as exc:
        LOG.error("%s", exc)
        return 2

    lookback = args.lookback_hours or int(cfg.get("default_lookback_hours", 48))
    limit = args.limit or int(cfg.get("default_limit", 300))
    output = PROJECT_DIR / cfg["output_path"]

    LOG.info(
        "source=%s mode=%s lookback=%sh limit=%s output=%s",
        args.source,
        args.mode,
        lookback,
        limit,
        output,
    )

    if args.source == "doc":
        return run_doc_pipeline(cfg, mode=args.mode, lookback_hours=lookback, limit=limit, output=output)

    try:
        client = get_bigquery_client(cfg)
    except Exception as exc:
        LOG.error("BigQuery client failed: %s", exc)
        return 1

    sql, params = build_query(cfg, mode=args.mode, lookback_hours=lookback, limit=limit)

    try:
        df, qmeta = run_query(
            client, sql, params, cfg=cfg, lookback_hours=lookback, dry_run=args.dry_run
        )
    except GoogleCloudError:
        return 1

    if args.dry_run:
        return 0

    if df is None or df.empty:
        LOG.warning("No rows from BigQuery; keeping existing %s if present", output)
        return 0

    raw_n = len(df)
    cleaned = clean_dataframe(df)
    scored = score_events(cleaned, cfg=cfg, mode=args.mode, lookback_hours=lookback)
    events = cluster_events(scored, cfg=cfg)
    payload = build_payload(
        events,
        lookback_hours=lookback,
        total_raw_rows=raw_n,
        mode=args.mode,
        query_meta=qmeta,
    )

    try:
        export_json(payload, output)
    except OSError as exc:
        LOG.error("Export failed: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
