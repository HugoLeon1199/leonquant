"""DuckDB persistence."""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

from utils.hashing import sha256_text
from utils.today_filter import (
    is_datetime_in_range,
    is_url_likely_recent_calendar_days,
    parse_any_datetime,
    resolve_calendar_date,
    target_date_range,
    target_recent_calendar_days_range,
)


DDL = """
CREATE TABLE IF NOT EXISTS source_profiles (
  source_id TEXT PRIMARY KEY,
  input_url TEXT,
  normalized_url TEXT,
  domain TEXT,
  scheme TEXT,
  homepage_url TEXT,
  robots_url TEXT,
  robots_ok BOOLEAN,
  robots_sitemaps TEXT,
  robots_disallow_detected BOOLEAN,
  robots_can_fetch_homepage BOOLEAN,
  has_known_api BOOLEAN,
  known_api_adapter TEXT,
  known_api_endpoint_hint TEXT,
  has_rss BOOLEAN,
  rss_urls TEXT,
  rss_valid_count INTEGER,
  has_sitemap BOOLEAN,
  sitemap_urls TEXT,
  sitemap_url_count INTEGER,
  html_status_code INTEGER,
  html_title TEXT,
  html_text_length INTEGER,
  html_link_count INTEGER,
  html_extract_ok BOOLEAN,
  sample_extracted_text_length INTEGER,
  js_required BOOLEAN,
  paywall_detected BOOLEAN,
  captcha_detected BOOLEAN,
  login_detected BOOLEAN,
  best_strategy TEXT,
  tos_risk TEXT,
  status TEXT,
  error_message TEXT,
  profiled_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS discovered_urls (
  id TEXT PRIMARY KEY,
  source_id TEXT,
  url TEXT,
  discovery_method TEXT,
  title TEXT,
  published_at TEXT,
  raw_metadata TEXT,
  discovered_at TIMESTAMP,
  url_hash TEXT
);

CREATE TABLE IF NOT EXISTS articles (
  id TEXT PRIMARY KEY,
  source_id TEXT,
  url TEXT,
  title TEXT,
  published_at TEXT,
  content TEXT,
  content_length INTEGER,
  content_hash TEXT,
  language TEXT,
  crawl_strategy_used TEXT,
  raw_path TEXT,
  extracted_at TIMESTAMP,
  quality_score DOUBLE
);

CREATE TABLE IF NOT EXISTS crawl_errors (
  id TEXT PRIMARY KEY,
  source_id TEXT,
  url TEXT,
  stage TEXT,
  error_type TEXT,
  error_message TEXT,
  created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS crawl_runs (
  run_id TEXT PRIMARY KEY,
  started_at TIMESTAMP,
  ended_at TIMESTAMP,
  status TEXT,
  input_path TEXT,
  strategy TEXT,
  limit_sources INTEGER,
  max_articles_per_source INTEGER,
  force_refresh BOOLEAN,
  config_json TEXT,
  total_sources INTEGER,
  total_discovered_urls INTEGER,
  total_articles INTEGER,
  total_errors INTEGER,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS crawl_frontier (
  url_hash TEXT PRIMARY KEY,
  source_id TEXT,
  url TEXT,
  strategy TEXT,
  status TEXT,
  priority INTEGER,
  retry_count INTEGER,
  last_error_type TEXT,
  last_error_message TEXT,
  first_seen_at TIMESTAMP,
  last_seen_at TIMESTAMP,
  last_crawled_at TIMESTAMP,
  next_crawl_at TIMESTAMP,
  content_hash TEXT
);

CREATE TABLE IF NOT EXISTS source_health (
  source_id TEXT PRIMARY KEY,
  total_urls_seen INTEGER,
  total_articles_inserted INTEGER,
  total_errors INTEGER,
  last_success_at TIMESTAMP,
  last_error_at TIMESTAMP,
  last_error_type TEXT,
  success_rate DOUBLE,
  updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS source_crawl_skip (
  source_id TEXT PRIMARY KEY,
  domain TEXT,
  input_url TEXT,
  reason TEXT NOT NULL,
  detail TEXT,
  block_errors INTEGER,
  date_filter_errors INTEGER,
  articles_in_db INTEGER,
  decided_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS api_records (
  id TEXT PRIMARY KEY,
  api_name TEXT NOT NULL,
  source_id TEXT,
  record_type TEXT,
  title TEXT,
  url TEXT NOT NULL,
  published_at TEXT,
  updated_at TEXT,
  summary TEXT,
  content TEXT,
  language TEXT,
  domain TEXT,
  country TEXT,
  authors_json TEXT,
  raw_metadata TEXT,
  discovery_method TEXT,
  content_hash TEXT,
  collected_at TIMESTAMP,
  target_calendar_date TEXT,
  timezone_name TEXT
);

CREATE TABLE IF NOT EXISTS gdelt_doc_hits (
  id TEXT PRIMARY KEY,
  target_calendar_date TEXT NOT NULL,
  timezone_name TEXT NOT NULL,
  url TEXT NOT NULL,
  title TEXT,
  seendate TEXT,
  domain TEXT,
  api_query TEXT,
  window_start_utc TIMESTAMP,
  window_end_utc TIMESTAMP,
  fetched_at TIMESTAMP,
  article_id TEXT,
  extract_error TEXT
);
"""


class WebIntelDB:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.conn = duckdb.connect(str(db_path))
        self.conn.execute(DDL)
        self._run_migrations()

    def _safe_add_column(self, table: str, column: str, definition: str) -> None:
        try:
            cols = {
                row[1]
                for row in self.conn.execute(f"PRAGMA table_info('{table}')").fetchall()
            }
            if column in cols:
                return
            self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        except Exception:
            # DuckDB leaves the transaction aborted if ALTER fails.
            try:
                self.conn.execute("ROLLBACK")
            except Exception:
                pass

    def _run_migrations(self) -> None:
        """Add robots_can_fetch_homepage for DBs created before this column existed."""
        self._safe_add_column("source_profiles", "robots_can_fetch_homepage", "BOOLEAN DEFAULT TRUE")
        self._safe_add_column("discovered_urls", "url_hash", "TEXT")

    def close(self) -> None:
        with self._lock:
            self.conn.close()

    def upsert_source_profile(self, row: dict[str, Any]) -> None:
        with self._lock:
            sid = row["source_id"]
            self.conn.execute("DELETE FROM source_profiles WHERE source_id = ?", [sid])
            cols = ", ".join(row.keys())
            placeholders = ", ".join(["?" for _ in row])
            sql = f"INSERT INTO source_profiles ({cols}) VALUES ({placeholders})"
            self.conn.execute(sql, list(row.values()))

    def get_profile(self, source_id: str) -> dict[str, Any] | None:
        with self._lock:
            df = self.conn.execute(
                "SELECT * FROM source_profiles WHERE source_id = ?",
                [source_id],
            ).fetchdf()
            if df.empty:
                return None
            return df.iloc[0].to_dict()

    def fetch_all_profiles(self) -> list[dict[str, Any]]:
        with self._lock:
            df = self.conn.execute("SELECT * FROM source_profiles ORDER BY source_id").fetchdf()
            return df.to_dict("records")

    def insert_discovered_url(self, row: dict[str, Any]) -> None:
        with self._lock:
            if row.get("url") and not row.get("url_hash"):
                row = {**row, "url_hash": sha256_text(str(row["url"]))}
            cols = ", ".join(row.keys())
            placeholders = ", ".join(["?" for _ in row])
            sql = f"INSERT OR REPLACE INTO discovered_urls ({cols}) VALUES ({placeholders})"
            self.conn.execute(sql, list(row.values()))

    def insert_article(self, row: dict[str, Any]) -> None:
        with self._lock:
            cols = ", ".join(row.keys())
            placeholders = ", ".join(["?" for _ in row])
            sql = f"INSERT OR REPLACE INTO articles ({cols}) VALUES ({placeholders})"
            self.conn.execute(sql, list(row.values()))

    def touch_article_extracted_by_hash(self, content_hash: str) -> int:
        """Refresh extracted_at for duplicate re-crawls (warm cache / today-only)."""
        if not content_hash:
            return 0
        with self._lock:
            cur = self.conn.execute(
                "UPDATE articles SET extracted_at = ? WHERE content_hash = ?",
                [utc_now(), content_hash],
            )
            return int(cur.rowcount or 0)

    def insert_crawl_error(self, row: dict[str, Any]) -> None:
        with self._lock:
            cols = ", ".join(row.keys())
            placeholders = ", ".join(["?" for _ in row])
            sql = f"INSERT INTO crawl_errors ({cols}) VALUES ({placeholders})"
            self.conn.execute(sql, list(row.values()))

    def fetch_distinct_content_hashes(self) -> set[str]:
        with self._lock:
            try:
                res = self.conn.execute(
                    "SELECT DISTINCT content_hash FROM articles WHERE content_hash IS NOT NULL AND content_hash <> ''"
                ).fetchall()
                return {r[0] for r in res}
            except Exception:
                return set()

    def create_crawl_run(
        self,
        *,
        run_id: str,
        input_path: str,
        strategy: str,
        limit_sources: int | None,
        max_articles_per_source: int | None,
        force_refresh: bool,
        config_json: str = "",
        notes: str = "",
    ) -> None:
        with self._lock:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO crawl_runs (
                  run_id, started_at, ended_at, status, input_path, strategy,
                  limit_sources, max_articles_per_source, force_refresh, config_json,
                  total_sources, total_discovered_urls, total_articles, total_errors, notes
                ) VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 0, ?)
                """,
                [
                    run_id,
                    utc_now(),
                    "running",
                    input_path,
                    strategy,
                    limit_sources,
                    max_articles_per_source,
                    force_refresh,
                    config_json,
                    notes,
                ],
            )

    def finish_crawl_run(self, *, run_id: str, status: str, notes: str = "") -> None:
        stats = self.get_crawl_summary_stats()
        with self._lock:
            self.conn.execute(
                """
                UPDATE crawl_runs
                SET ended_at = ?,
                    status = ?,
                    total_sources = ?,
                    total_discovered_urls = ?,
                    total_articles = ?,
                    total_errors = ?,
                    notes = CASE WHEN ? <> '' THEN ? ELSE notes END
                WHERE run_id = ?
                """,
                [
                    utc_now(),
                    status,
                    stats["total_sources"],
                    stats["total_discovered_urls"],
                    stats["total_articles"],
                    stats["total_errors"],
                    notes,
                    notes,
                    run_id,
                ],
            )

    def upsert_frontier_url(
        self,
        *,
        source_id: str,
        url: str,
        strategy: str,
        status: str = "pending",
        priority: int = 100,
        next_crawl_at: datetime | None = None,
        content_hash: str | None = None,
    ) -> str:
        url_hash = sha256_text(url)
        now = utc_now()
        with self._lock:
            existing = self.conn.execute(
                "SELECT retry_count, first_seen_at FROM crawl_frontier WHERE url_hash = ?",
                [url_hash],
            ).fetchone()
            if existing:
                self.conn.execute(
                    """
                    UPDATE crawl_frontier
                    SET source_id = ?,
                        url = ?,
                        strategy = ?,
                        status = ?,
                        priority = ?,
                        last_seen_at = ?,
                        next_crawl_at = COALESCE(?, next_crawl_at),
                        content_hash = COALESCE(?, content_hash)
                    WHERE url_hash = ?
                    """,
                    [source_id, url, strategy, status, priority, now, next_crawl_at, content_hash, url_hash],
                )
            else:
                self.conn.execute(
                    """
                    INSERT INTO crawl_frontier (
                      url_hash, source_id, url, strategy, status, priority, retry_count,
                      last_error_type, last_error_message, first_seen_at, last_seen_at,
                      last_crawled_at, next_crawl_at, content_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, 0, NULL, NULL, ?, ?, NULL, ?, ?)
                    """,
                    [url_hash, source_id, url, strategy, status, priority, now, now, next_crawl_at, content_hash],
                )
        return url_hash

    def mark_frontier_crawled(self, *, url: str, content_hash: str | None = None) -> None:
        url_hash = sha256_text(url)
        with self._lock:
            self.conn.execute(
                """
                UPDATE crawl_frontier
                SET status = 'crawled',
                    last_crawled_at = ?,
                    last_seen_at = ?,
                    last_error_type = NULL,
                    last_error_message = NULL,
                    content_hash = COALESCE(?, content_hash)
                WHERE url_hash = ?
                """,
                [utc_now(), utc_now(), content_hash, url_hash],
            )

    def mark_frontier_failed(
        self,
        *,
        url: str,
        error_type: str,
        error_message: str,
        status: str = "failed",
    ) -> None:
        url_hash = sha256_text(url)
        with self._lock:
            self.conn.execute(
                """
                UPDATE crawl_frontier
                SET status = ?,
                    retry_count = COALESCE(retry_count, 0) + 1,
                    last_error_type = ?,
                    last_error_message = ?,
                    last_seen_at = ?,
                    next_crawl_at = NULL
                WHERE url_hash = ?
                """,
                [status, error_type, error_message[:2000], utc_now(), url_hash],
            )

    def mark_frontier_skipped(self, *, url: str, reason_type: str, reason_message: str = "") -> None:
        self.mark_frontier_failed(
            url=url,
            error_type=reason_type,
            error_message=reason_message,
            status="skipped",
        )

    def fetch_frontier_summary(self) -> dict[str, int]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT status, COUNT(*) FROM crawl_frontier GROUP BY status"
            ).fetchall()
            out = {"pending": 0, "crawling": 0, "crawled": 0, "failed": 0, "skipped": 0}
            for status, count in rows:
                out[str(status or "pending")] = int(count or 0)
            return out

    def update_source_health_from_current_db(self) -> None:
        with self._lock:
            source_rows = self.conn.execute(
                """
                SELECT source_id FROM source_profiles
                UNION
                SELECT source_id FROM articles WHERE source_id IS NOT NULL AND source_id <> ''
                UNION
                SELECT source_id FROM crawl_errors WHERE source_id IS NOT NULL AND source_id <> ''
                UNION
                SELECT source_id FROM crawl_frontier WHERE source_id IS NOT NULL AND source_id <> ''
                """
            ).fetchall()
            now = utc_now()
            for (source_id,) in source_rows:
                total_urls_seen = self.conn.execute(
                    """
                    SELECT COUNT(DISTINCT url) FROM (
                      SELECT url FROM crawl_frontier WHERE source_id = ?
                      UNION
                      SELECT url FROM discovered_urls WHERE source_id = ?
                    )
                    """,
                    [source_id, source_id],
                ).fetchone()[0]
                total_articles = self.conn.execute(
                    "SELECT COUNT(*) FROM articles WHERE source_id = ?",
                    [source_id],
                ).fetchone()[0]
                total_errors = self.conn.execute(
                    "SELECT COUNT(*) FROM crawl_errors WHERE source_id = ?",
                    [source_id],
                ).fetchone()[0]
                last_success_at = self.conn.execute(
                    "SELECT MAX(extracted_at) FROM articles WHERE source_id = ?",
                    [source_id],
                ).fetchone()[0]
                last_error_at = self.conn.execute(
                    "SELECT MAX(created_at) FROM crawl_errors WHERE source_id = ?",
                    [source_id],
                ).fetchone()[0]
                last_error_type_row = self.conn.execute(
                    """
                    SELECT error_type FROM crawl_errors
                    WHERE source_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    [source_id],
                ).fetchone()
                denom = int(total_articles or 0) + int(total_errors or 0)
                success_rate = float(total_articles or 0) / denom if denom else 0.0
                self.conn.execute(
                    """
                    INSERT OR REPLACE INTO source_health (
                      source_id, total_urls_seen, total_articles_inserted, total_errors,
                      last_success_at, last_error_at, last_error_type, success_rate, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        source_id,
                        int(total_urls_seen or 0),
                        int(total_articles or 0),
                        int(total_errors or 0),
                        last_success_at,
                        last_error_at,
                        last_error_type_row[0] if last_error_type_row else None,
                        success_rate,
                        now,
                    ],
                )

    def fetch_crawl_skip_source_ids(self) -> frozenset[str]:
        with self._lock:
            rows = self.conn.execute("SELECT source_id FROM source_crawl_skip").fetchall()
        return frozenset(str(r[0]) for r in rows if r and r[0])

    def refresh_source_crawl_skip(self, *, rules: Any) -> dict[str, int]:
        from crawlability.source_skip import classify_source_skip

        with self._lock:
            profiles = self.conn.execute(
                "SELECT source_id, domain, input_url, status, best_strategy FROM source_profiles"
            ).fetchall()
            err_rows = self.conn.execute(
                "SELECT source_id, error_type, COUNT(*) FROM crawl_errors GROUP BY 1, 2"
            ).fetchall()
            art_rows = self.conn.execute(
                "SELECT source_id, COUNT(*) FROM articles GROUP BY 1"
            ).fetchall()

        err_by_sid: dict[str, dict[str, int]] = {}
        for sid, et, n in err_rows:
            if not sid:
                continue
            err_by_sid.setdefault(str(sid), {})[str(et)] = int(n)

        art_by_sid = {str(sid): int(n) for sid, n in art_rows if sid}

        skip_rows: list[dict[str, Any]] = []
        for sid, domain, input_url, status, best_strategy in profiles:
            sid_s = str(sid)
            verdict = classify_source_skip(
                source_id=sid_s,
                domain=str(domain or ""),
                status=str(status) if status is not None else None,
                best_strategy=str(best_strategy) if best_strategy is not None else None,
                error_counts=err_by_sid.get(sid_s, {}),
                articles_in_db=art_by_sid.get(sid_s, 0),
                rules=rules,
            )
            if verdict is None:
                continue
            skip_rows.append(
                {
                    "source_id": verdict.source_id,
                    "domain": verdict.domain,
                    "input_url": str(input_url or ""),
                    "reason": verdict.reason,
                    "detail": verdict.detail,
                    "block_errors": verdict.block_errors,
                    "date_filter_errors": verdict.date_filter_errors,
                    "articles_in_db": verdict.articles_in_db,
                    "decided_at": utc_now(),
                }
            )

        with self._lock:
            self.conn.execute("DELETE FROM source_crawl_skip")
            for row in skip_rows:
                cols = ", ".join(row.keys())
                placeholders = ", ".join(["?" for _ in row])
                self.conn.execute(
                    f"INSERT INTO source_crawl_skip ({cols}) VALUES ({placeholders})",
                    list(row.values()),
                )

        return {
            "profiles_total": len(profiles),
            "skip_listed": len(skip_rows),
            "still_crawlable": len(profiles) - len(skip_rows),
        }

    def export_source_crawl_skip_txt(self, out_path: Path) -> int:
        with self._lock:
            rows = self.conn.execute(
                """
                SELECT domain, input_url, reason, detail, block_errors, date_filter_errors, source_id
                FROM source_crawl_skip
                ORDER BY reason, domain
                """
            ).fetchall()

        lines = [
            "# Nguon KHONG crawl duoc voi stack hien tai (HTTP/SSL/profile — khong tin AccessControl heuristic).",
            "# KHONG gom nguon chi loi NotToday (co the crawl, chi sai ngay).",
            "# Tu dong cap nhat sau run_intel_full_daily; xoa dong de thu lai mot nguon.",
            "",
        ]
        for domain, input_url, reason, detail, block_n, date_n, sid in rows:
            dom = str(domain or "").strip()
            url = str(input_url or "").strip() or (f"https://{dom}" if dom else "")
            lines.append(
                f"# reason={reason} source_id={sid} block_errors={block_n} "
                f"date_filter_errors={date_n} detail={detail}"
            )
            if url:
                lines.append(url)
            lines.append("")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        return len(rows)

    def _export_query_csv(self, sql: str, out_path: Path) -> None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df = self.conn.execute(sql).fetchdf()
        df.to_csv(out_path, index=False)

    def export_articles_csv(self, out_path: Path) -> None:
        with self._lock:
            self._export_query_csv("SELECT * FROM articles ORDER BY extracted_at, id", out_path)

    def export_articles_metadata_csv(self, out_path: Path) -> None:
        with self._lock:
            self._export_query_csv(
                """
                SELECT id, source_id, url, title, published_at, content_length, content_hash,
                       language, crawl_strategy_used, raw_path, extracted_at, quality_score
                FROM articles ORDER BY extracted_at, id
                """,
                out_path,
            )

    def export_articles_parquet(self, out_path: Path) -> None:
        with self._lock:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            df = self.conn.execute("SELECT * FROM articles ORDER BY extracted_at, id").fetchdf()
            df.to_parquet(out_path, index=False)

    def export_crawl_errors_csv(self, out_path: Path) -> None:
        with self._lock:
            self._export_query_csv("SELECT * FROM crawl_errors ORDER BY created_at, id", out_path)

    def export_discovered_urls_csv(self, out_path: Path) -> None:
        with self._lock:
            self._export_query_csv("SELECT * FROM discovered_urls ORDER BY discovered_at, id", out_path)

    def export_crawl_frontier_csv(self, out_path: Path) -> None:
        with self._lock:
            self._export_query_csv("SELECT * FROM crawl_frontier ORDER BY last_seen_at, url_hash", out_path)

    def export_source_health_csv(self, out_path: Path) -> None:
        with self._lock:
            self._export_query_csv("SELECT * FROM source_health ORDER BY source_id", out_path)

    def get_crawl_summary_stats(self) -> dict[str, Any]:
        with self._lock:
            scalar_queries = {
                "total_sources": "SELECT COUNT(*) FROM source_profiles",
                "total_discovered_urls": "SELECT COUNT(*) FROM discovered_urls",
                "total_articles": "SELECT COUNT(*) FROM articles",
                "total_errors": "SELECT COUNT(*) FROM crawl_errors",
                "avg_quality_score": "SELECT AVG(quality_score) FROM articles",
            }
            stats: dict[str, Any] = {}
            for key, sql in scalar_queries.items():
                val = self.conn.execute(sql).fetchone()[0]
                if key == "avg_quality_score":
                    stats[key] = float(val) if val is not None else 0.0
                else:
                    stats[key] = int(val or 0)

            frontier = self.fetch_frontier_summary()
            stats["total_frontier_pending"] = frontier.get("pending", 0)
            stats["total_frontier_crawled"] = frontier.get("crawled", 0)
            stats["total_frontier_failed"] = frontier.get("failed", 0)
            stats["total_frontier_skipped"] = frontier.get("skipped", 0)

            stats["articles_by_strategy"] = {
                str(k or "unknown"): int(v or 0)
                for k, v in self.conn.execute(
                    "SELECT crawl_strategy_used, COUNT(*) FROM articles GROUP BY crawl_strategy_used ORDER BY COUNT(*) DESC"
                ).fetchall()
            }
            stats["errors_by_type"] = {
                str(k or "unknown"): int(v or 0)
                for k, v in self.conn.execute(
                    "SELECT error_type, COUNT(*) FROM crawl_errors GROUP BY error_type ORDER BY COUNT(*) DESC"
                ).fetchall()
            }
            stats["top_sources_by_articles"] = [
                {"source_id": str(source_id), "count": int(count or 0)}
                for source_id, count in self.conn.execute(
                    """
                    SELECT source_id, COUNT(*) AS n
                    FROM articles
                    GROUP BY source_id
                    ORDER BY n DESC, source_id
                    LIMIT 10
                    """
                ).fetchall()
            ]
            stats["top_sources_by_errors"] = [
                {"source_id": str(source_id), "count": int(count or 0)}
                for source_id, count in self.conn.execute(
                    """
                    SELECT source_id, COUNT(*) AS n
                    FROM crawl_errors
                    GROUP BY source_id
                    ORDER BY n DESC, source_id
                    LIMIT 10
                    """
                ).fetchall()
            ]
            min_len, avg_len, max_len = self.conn.execute(
                "SELECT MIN(content_length), AVG(content_length), MAX(content_length) FROM articles"
            ).fetchone()
            stats["content_length"] = {
                "min": int(min_len or 0),
                "avg": float(avg_len) if avg_len is not None else 0.0,
                "max": int(max_len or 0),
            }
            return stats

    def export_source_profiles_csv(self, out_path: Path) -> None:
        with self._lock:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            df = self.conn.execute("SELECT * FROM source_profiles ORDER BY source_id").fetchdf()
            df.to_csv(out_path, index=False)

    def export_source_profiles_parquet(self, out_path: Path) -> None:
        with self._lock:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            df = self.conn.execute("SELECT * FROM source_profiles ORDER BY source_id").fetchdf()
            df.to_parquet(out_path, index=False)

    def export_review_sources_csv(self, out_path: Path) -> None:
        with self._lock:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            sql = """
            SELECT * FROM source_profiles
            WHERE best_strategy IN ('manual_review','metadata_only')
               OR captcha_detected = TRUE
               OR login_detected = TRUE
               OR paywall_detected = TRUE
               OR html_status_code >= 400
               OR error_message IS NOT NULL
            ORDER BY source_id
            """
            df = self.conn.execute(sql).fetchdf()
            df.to_csv(out_path, index=False)

    def export_review_sources_strict_csv(self, out_path: Path) -> None:
        """Actionable review only: profile failed, 4xx, or hard errors — not paywall heuristics alone."""
        with self._lock:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            sql = """
            SELECT * FROM source_profiles
            WHERE best_strategy IN ('manual_review', 'metadata_only')
               OR html_status_code >= 400
               OR error_message IS NOT NULL
            ORDER BY source_id
            """
            df = self.conn.execute(sql).fetchdf()
            df.to_csv(out_path, index=False)

    def fetch_today_articles(
        self,
        *,
        target_date_str: str | None,
        timezone_name: str,
        recent_calendar_days: int = 2,
    ) -> list[dict[str, Any]]:
        """Articles whose publication falls in the recent local calendar window ending on target date.

        Articles with a parseable ``published_at`` outside the window are excluded even if
        re-crawled inside it. Missing/unparseable publish dates may match on ``extracted_at``.
        """
        n = max(1, int(recent_calendar_days))
        start_utc, end_utc = target_recent_calendar_days_range(target_date_str, timezone_name, n)
        target_d = resolve_calendar_date(target_date_str, timezone_name)
        with self._lock:
            df = self.conn.execute("SELECT * FROM articles ORDER BY extracted_at, id").fetchdf()
        rows = df.to_dict("records")
        out: list[dict[str, Any]] = []
        for row in rows:
            url = str(row.get("url") or "")
            pub_raw = row.get("published_at")
            pub_dt = parse_any_datetime(str(pub_raw)) if pub_raw is not None else None
            ext = row.get("extracted_at")
            ext_dt: datetime | None = None
            if ext is not None:
                try:
                    ext_dt = ext.to_pydatetime() if hasattr(ext, "to_pydatetime") else datetime.fromisoformat(str(ext))
                    if ext_dt.tzinfo is None:
                        ext_dt = ext_dt.replace(tzinfo=timezone.utc)
                    ext_dt = ext_dt.astimezone(timezone.utc)
                except (ValueError, TypeError):
                    ext_dt = None

            if pub_dt and is_datetime_in_range(pub_dt, start_utc, end_utc):
                out.append(row)
                continue
            if pub_raw is None or str(pub_raw).strip() == "":
                if ext_dt and is_datetime_in_range(ext_dt, start_utc, end_utc):
                    if is_url_likely_recent_calendar_days(url, target_d, n) or int(
                        row.get("content_length") or 0
                    ) >= 200:
                        out.append(row)
                continue
            if pub_dt and not is_datetime_in_range(pub_dt, start_utc, end_utc):
                continue
            # Unparseable published_at: treat like missing
            if ext_dt and is_datetime_in_range(ext_dt, start_utc, end_utc):
                if is_url_likely_recent_calendar_days(url, target_d, n) or int(row.get("content_length") or 0) >= 200:
                    out.append(row)
        return out

    def prune_stale_intel_data(
        self,
        *,
        target_date_str: str | None,
        timezone_name: str,
        recent_calendar_days: int = 2,
    ) -> dict[str, int]:
        """Keep only articles in the recent export window; trim old crawl noise and VACUUM."""
        n = max(1, int(recent_calendar_days))
        start_utc, _end_utc = target_recent_calendar_days_range(target_date_str, timezone_name, n)
        keep_rows = self.fetch_today_articles(
            target_date_str=target_date_str,
            timezone_name=timezone_name,
            recent_calendar_days=n,
        )
        keep_ids = [str(r["id"]) for r in keep_rows if r.get("id")]

        with self._lock:
            before_articles = int(self.conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0])
            if keep_ids:
                placeholders = ",".join("?" * len(keep_ids))
                self.conn.execute(
                    f"DELETE FROM articles WHERE id NOT IN ({placeholders})",
                    keep_ids,
                )
            else:
                # Never wipe the whole table when the export window is empty (CI safety).
                pass
            after_articles = int(self.conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0])

            before_errors = int(self.conn.execute("SELECT COUNT(*) FROM crawl_errors").fetchone()[0])
            self.conn.execute("DELETE FROM crawl_errors WHERE created_at < ?", [start_utc])
            after_errors = int(self.conn.execute("SELECT COUNT(*) FROM crawl_errors").fetchone()[0])

            before_discovered = int(self.conn.execute("SELECT COUNT(*) FROM discovered_urls").fetchone()[0])
            self.conn.execute("DELETE FROM discovered_urls WHERE discovered_at < ?", [start_utc])
            after_discovered = int(self.conn.execute("SELECT COUNT(*) FROM discovered_urls").fetchone()[0])

        try:
            with self._lock:
                self.conn.execute("VACUUM")
        except duckdb.Error:
            pass

        return {
            "articles_before": before_articles,
            "articles_after": after_articles,
            "articles_removed": before_articles - after_articles,
            "crawl_errors_removed": before_errors - after_errors,
            "discovered_urls_removed": before_discovered - after_discovered,
            "keep_articles": len(keep_ids),
        }

    def clear_crawl_article_data(self) -> dict[str, int]:
        """Drop crawl output tables; keep source_profiles (and source_crawl_skip)."""
        tables = (
            "articles",
            "discovered_urls",
            "crawl_errors",
            "crawl_runs",
            "crawl_frontier",
            "source_health",
            "api_records",
            "gdelt_doc_hits",
        )
        counts: dict[str, int] = {}
        with self._lock:
            for table in tables:
                try:
                    before = int(self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                except duckdb.Error:
                    before = 0
                try:
                    self.conn.execute(f"DELETE FROM {table}")
                except duckdb.Error:
                    pass
                counts[table] = before
            profiles = int(self.conn.execute("SELECT COUNT(*) FROM source_profiles").fetchone()[0])
        try:
            with self._lock:
                self.conn.execute("VACUUM")
        except duckdb.Error:
            pass
        counts["source_profiles_kept"] = profiles
        return counts

    def fetch_all_articles(self) -> list[dict[str, Any]]:
        """All rows in articles (any publication day)."""
        with self._lock:
            df = self.conn.execute("SELECT * FROM articles ORDER BY extracted_at, id").fetchdf()
        return df.to_dict("records")

    def get_today_summary_stats(
        self,
        *,
        target_date_str: str | None,
        timezone_name: str,
        recent_calendar_days: int = 2,
    ) -> dict[str, Any]:
        n = max(1, int(recent_calendar_days))
        start_utc, end_utc = target_recent_calendar_days_range(target_date_str, timezone_name, n)
        articles = self.fetch_today_articles(
            target_date_str=target_date_str, timezone_name=timezone_name, recent_calendar_days=n
        )
        with self._lock:
            err_df = self.conn.execute(
                """
                SELECT error_type, COUNT(*) AS n
                FROM crawl_errors
                WHERE created_at >= ? AND created_at < ?
                GROUP BY error_type
                ORDER BY n DESC
                """,
                [start_utc, end_utc],
            ).fetchdf()
            frontier_skip = self.conn.execute(
                """
                SELECT COUNT(*) FROM crawl_frontier
                WHERE status = 'skipped'
                  AND last_error_type = 'NotToday'
                  AND last_seen_at >= ? AND last_seen_at < ?
                """,
                [start_utc, end_utc],
            ).fetchone()[0]
            access_n = self.conn.execute(
                """
                SELECT COUNT(*) FROM crawl_errors
                WHERE error_type = 'AccessControlDetected'
                  AND created_at >= ? AND created_at < ?
                """,
                [start_utc, end_utc],
            ).fetchone()[0]
            not_today_err = self.conn.execute(
                """
                SELECT COUNT(*) FROM crawl_errors
                WHERE error_type = 'NotToday'
                  AND created_at >= ? AND created_at < ?
                """,
                [start_utc, end_utc],
            ).fetchone()[0]
            distinct_article_sources = self.conn.execute(
                """
                SELECT COUNT(DISTINCT source_id)
                FROM articles
                WHERE extracted_at >= ? AND extracted_at < ?
                """,
                [start_utc, end_utc],
            ).fetchone()[0]
        by_type: dict[str, int] = {}
        if not err_df.empty:
            by_type = {str(r["error_type"]): int(r["n"]) for _, r in err_df.iterrows()}
        strat_counts: dict[str, int] = {}
        for r in articles:
            k = str(r.get("crawl_strategy_used") or "unknown")
            strat_counts[k] = strat_counts.get(k, 0) + 1
        top_sources: dict[str, int] = {}
        for r in articles:
            sid = str(r.get("source_id") or "")
            top_sources[sid] = top_sources.get(sid, 0) + 1
        top_sources_rows = sorted(top_sources.items(), key=lambda x: (-x[1], x[0]))[:10]
        return {
            "target_date": str(resolve_calendar_date(target_date_str, timezone_name)),
            "timezone": timezone_name,
            "window_start_utc": start_utc,
            "window_end_utc": end_utc,
            "today_article_count": len(articles),
            "today_articles": articles,
            "errors_by_type_window": by_type,
            "total_errors_window": int(sum(by_type.values())),
            "not_today_skipped_frontier": int(frontier_skip or 0),
            "not_today_errors": int(not_today_err or 0),
            "access_control_window": int(access_n or 0),
            "articles_by_strategy": strat_counts,
            "top_sources_today": [{"source_id": a, "count": b} for a, b in top_sources_rows],
            "distinct_article_sources_today": int(distinct_article_sources or 0),
        }

    def source_intake_snapshot(
        self,
        *,
        target_date_str: str | None,
        timezone_name: str,
        recent_calendar_days: int = 2,
    ) -> dict[str, Any]:
        """Per-source counts for the calendar day window: discovered URLs vs extracted articles vs frontier."""
        n = max(1, int(recent_calendar_days))
        start_utc, end_utc = target_recent_calendar_days_range(target_date_str, timezone_name, n)
        cal = str(resolve_calendar_date(target_date_str, timezone_name))

        def _df_counts(sql: str) -> dict[str, int]:
            with self._lock:
                df = self.conn.execute(sql, [start_utc, end_utc]).fetchdf()
            if df.empty:
                return {}
            out: dict[str, int] = {}
            for _, r in df.iterrows():
                raw_sid = r["source_id"]
                sid = str(raw_sid).strip() if raw_sid is not None else ""
                if not sid:
                    sid = "(unknown)"
                out[sid] = int(r["n"])
            return out

        discovered_sql = """
            SELECT source_id, COUNT(*) AS n
            FROM discovered_urls
            WHERE discovered_at >= ? AND discovered_at < ?
            GROUP BY source_id
        """
        articles_sql = """
            SELECT source_id, COUNT(*) AS n
            FROM articles
            WHERE extracted_at >= ? AND extracted_at < ?
            GROUP BY source_id
        """
        pending_sql = """
            SELECT source_id, COUNT(*) AS n
            FROM crawl_frontier
            WHERE status IN ('pending', 'crawling')
              AND last_seen_at >= ? AND last_seen_at < ?
            GROUP BY source_id
        """
        failed_sql = """
            SELECT source_id, COUNT(*) AS n
            FROM crawl_frontier
            WHERE status = 'failed'
              AND last_seen_at >= ? AND last_seen_at < ?
            GROUP BY source_id
        """

        disc = _df_counts(discovered_sql)
        arts = _df_counts(articles_sql)
        pend = _df_counts(pending_sql)
        fail = _df_counts(failed_sql)

        all_ids = sorted(set(disc) | set(arts) | set(pend) | set(fail))
        rows: list[dict[str, Any]] = []
        for sid in all_ids:
            d_n = int(disc.get(sid, 0))
            a_n = int(arts.get(sid, 0))
            rows.append(
                {
                    "source_id": sid,
                    "discovered_today": d_n,
                    "articles_extracted_today": a_n,
                    "remaining_estimate": max(0, d_n - a_n),
                    "frontier_pending_today": int(pend.get(sid, 0)),
                    "frontier_failed_today": int(fail.get(sid, 0)),
                }
            )
        rows.sort(key=lambda r: (-r["articles_extracted_today"], -r["discovered_today"], r["source_id"]))

        with self._lock:
            prof_total = int(self.conn.execute("SELECT COUNT(*) FROM source_profiles").fetchone()[0] or 0)

        return {
            "target_calendar_date": cal,
            "timezone_name": timezone_name,
            "window_start_utc": start_utc,
            "window_end_utc": end_utc,
            "profiled_sources_total": prof_total,
            "rows": rows,
            "totals": {
                "discovered_today": int(sum(disc.values())),
                "articles_extracted_today": int(sum(arts.values())),
                "remaining_estimate": max(0, int(sum(disc.values())) - int(sum(arts.values()))),
                "frontier_pending_today": int(sum(pend.values())),
                "frontier_failed_today": int(sum(fail.values())),
            },
        }

    def export_today_articles_csv(
        self, out_path: Path, *, target_date_str: str | None, timezone_name: str, recent_calendar_days: int = 2
    ) -> None:
        import pandas as pd

        rows = self.fetch_today_articles(
            target_date_str=target_date_str, timezone_name=timezone_name, recent_calendar_days=recent_calendar_days
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_csv(out_path, index=False)

    def export_today_articles_metadata_csv(
        self, out_path: Path, *, target_date_str: str | None, timezone_name: str, recent_calendar_days: int = 2
    ) -> None:
        import pandas as pd

        cols = [
            "source_id",
            "title",
            "published_at",
            "url",
            "content_length",
            "quality_score",
            "crawl_strategy_used",
        ]
        rows = self.fetch_today_articles(
            target_date_str=target_date_str, timezone_name=timezone_name, recent_calendar_days=recent_calendar_days
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(rows)
        if df.empty:
            pd.DataFrame(columns=cols).to_csv(out_path, index=False)
            return
        df = df.reindex(columns=cols)
        df.to_csv(out_path, index=False)

    def export_today_articles_parquet(
        self, out_path: Path, *, target_date_str: str | None, timezone_name: str, recent_calendar_days: int = 2
    ) -> None:
        import pandas as pd

        rows = self.fetch_today_articles(
            target_date_str=target_date_str, timezone_name=timezone_name, recent_calendar_days=recent_calendar_days
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_parquet(out_path, index=False)

    def export_today_errors_csv(
        self, out_path: Path, *, target_date_str: str | None, timezone_name: str, recent_calendar_days: int = 2
    ) -> None:
        n = max(1, int(recent_calendar_days))
        start_utc, end_utc = target_recent_calendar_days_range(target_date_str, timezone_name, n)
        with self._lock:
            df = self.conn.execute(
                """
                SELECT * FROM crawl_errors
                WHERE created_at >= ? AND created_at < ?
                ORDER BY created_at, id
                """,
                [start_utc, end_utc],
            ).fetchdf()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)

    def export_today_frontier_csv(
        self, out_path: Path, *, target_date_str: str | None, timezone_name: str, recent_calendar_days: int = 2
    ) -> None:
        n = max(1, int(recent_calendar_days))
        start_utc, end_utc = target_recent_calendar_days_range(target_date_str, timezone_name, n)
        with self._lock:
            df = self.conn.execute(
                """
                SELECT * FROM crawl_frontier
                WHERE last_seen_at >= ? AND last_seen_at < ?
                ORDER BY last_seen_at, url_hash
                """,
                [start_utc, end_utc],
            ).fetchdf()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)

    def export_today_source_health_csv(
        self, out_path: Path, *, target_date_str: str | None, timezone_name: str, recent_calendar_days: int = 2
    ) -> None:
        n = max(1, int(recent_calendar_days))
        start_utc, end_utc = target_recent_calendar_days_range(target_date_str, timezone_name, n)
        with self._lock:
            df = self.conn.execute(
                """
                SELECT sh.*
                FROM source_health sh
                WHERE sh.source_id IN (
                  SELECT DISTINCT source_id FROM articles
                  WHERE extracted_at >= ? AND extracted_at < ?
                  UNION
                  SELECT DISTINCT source_id FROM crawl_errors
                  WHERE created_at >= ? AND created_at < ?
                  UNION
                  SELECT DISTINCT source_id FROM crawl_frontier
                  WHERE last_seen_at >= ? AND last_seen_at < ?
                )
                ORDER BY sh.source_id
                """,
                [start_utc, end_utc, start_utc, end_utc, start_utc, end_utc],
            ).fetchdf()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)

    def delete_gdelt_doc_hits_for_day(self, *, target_calendar_date: str, timezone_name: str) -> None:
        with self._lock:
            self.conn.execute(
                "DELETE FROM gdelt_doc_hits WHERE target_calendar_date = ? AND timezone_name = ?",
                [target_calendar_date, timezone_name],
            )

    def insert_gdelt_doc_hit(self, row: dict[str, Any]) -> None:
        with self._lock:
            cols = ", ".join(row.keys())
            placeholders = ", ".join(["?" for _ in row])
            sql = f"INSERT INTO gdelt_doc_hits ({cols}) VALUES ({placeholders})"
            self.conn.execute(sql, list(row.values()))

    def update_gdelt_doc_hit_extract(
        self,
        hit_id: str,
        *,
        article_id: str | None,
        extract_error: str | None,
    ) -> None:
        with self._lock:
            self.conn.execute(
                "UPDATE gdelt_doc_hits SET article_id = ?, extract_error = ? WHERE id = ?",
                [article_id, extract_error, hit_id],
            )

    def count_gdelt_doc_hits(self, *, target_calendar_date: str, timezone_name: str) -> int:
        with self._lock:
            row = self.conn.execute(
                """
                SELECT COUNT(*) FROM gdelt_doc_hits
                WHERE target_calendar_date = ? AND timezone_name = ?
                """,
                [target_calendar_date, timezone_name],
            ).fetchone()
            return int(row[0] or 0)

    def count_gdelt_extracted_in_window(self, *, target_date_str: str | None, timezone_name: str) -> int:
        start_utc, end_utc = target_date_range(target_date_str, timezone_name)
        with self._lock:
            row = self.conn.execute(
                """
                SELECT COUNT(*) FROM articles
                WHERE crawl_strategy_used = 'gdelt_then_article_extract'
                  AND extracted_at >= ? AND extracted_at < ?
                """,
                [start_utc, end_utc],
            ).fetchone()
            return int(row[0] or 0)

    def export_gdelt_doc_hits_csv(self, out_path: Path, *, target_calendar_date: str, timezone_name: str) -> None:
        with self._lock:
            df = self.conn.execute(
                """
                SELECT url, title, seendate, domain, api_query, window_start_utc, window_end_utc,
                       fetched_at, article_id, extract_error
                FROM gdelt_doc_hits
                WHERE target_calendar_date = ? AND timezone_name = ?
                ORDER BY seendate, url
                """,
                [target_calendar_date, timezone_name],
            ).fetchdf()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)

    def gdelt_day_extract_stats(self, *, target_calendar_date: str, timezone_name: str) -> dict[str, int]:
        with self._lock:
            ok = self.conn.execute(
                """
                SELECT COUNT(*) FROM gdelt_doc_hits
                WHERE target_calendar_date = ? AND timezone_name = ? AND article_id IS NOT NULL
                """,
                [target_calendar_date, timezone_name],
            ).fetchone()[0]
            bad = self.conn.execute(
                """
                SELECT COUNT(*) FROM gdelt_doc_hits
                WHERE target_calendar_date = ? AND timezone_name = ? AND extract_error IS NOT NULL
                """,
                [target_calendar_date, timezone_name],
            ).fetchone()[0]
        return {"extracted_linked": int(ok or 0), "extract_errors_logged": int(bad or 0)}

    def delete_api_records_for_calendar_day(self, *, target_calendar_date: str, timezone_name: str) -> None:
        with self._lock:
            self.conn.execute(
                "DELETE FROM api_records WHERE target_calendar_date = ? AND timezone_name = ?",
                [target_calendar_date, timezone_name],
            )

    def upsert_api_record(self, row: dict[str, Any]) -> None:
        with self._lock:
            cols = ", ".join(row.keys())
            placeholders = ", ".join(["?" for _ in row])
            sql = f"INSERT OR REPLACE INTO api_records ({cols}) VALUES ({placeholders})"
            self.conn.execute(sql, list(row.values()))

    def insert_api_record(self, row: dict[str, Any]) -> None:
        self.upsert_api_record(row)

    def fetch_today_api_records(self, *, target_date_str: str | None, timezone_name: str) -> list[dict[str, Any]]:
        target_cal = str(resolve_calendar_date(target_date_str, timezone_name))
        with self._lock:
            df = self.conn.execute(
                """
                SELECT *
                FROM api_records
                WHERE target_calendar_date = ? AND timezone_name = ?
                ORDER BY api_name, url
                """,
                [target_cal, timezone_name],
            ).fetchdf()
        if df.empty:
            return []
        return df.to_dict("records")

    def fetch_today_api_headlines(
        self, *, target_date_str: str | None, timezone_name: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        target_cal = str(resolve_calendar_date(target_date_str, timezone_name))
        with self._lock:
            df = self.conn.execute(
                """
                SELECT api_name, title, url, published_at
                FROM api_records
                WHERE target_calendar_date = ? AND timezone_name = ?
                ORDER BY collected_at DESC
                LIMIT ?
                """,
                [target_cal, timezone_name, limit],
            ).fetchdf()
        if df.empty:
            return []
        return df.to_dict("records")

    def export_today_api_records_jsonl(self, out_path: Path, *, target_date_str: str | None, timezone_name: str) -> None:
        rows = self.fetch_today_api_records(target_date_str=target_date_str, timezone_name=timezone_name)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    def get_api_summary_stats(self, *, target_date_str: str | None, timezone_name: str) -> dict[str, Any]:
        by_adapter = self.count_api_records_by_adapter(target_date_str=target_date_str, timezone_name=timezone_name)
        total = int(sum(by_adapter.values()))
        return {
            "records_by_adapter": by_adapter,
            "total_api_records_window": total,
            "api_extracted_fulltext": self.count_api_extracted_articles(
                target_date_str=target_date_str, timezone_name=timezone_name
            ),
            "api_hub_errors_by_adapter": self.api_hub_errors_by_adapter(
                target_date_str=target_date_str, timezone_name=timezone_name
            ),
        }

    def count_api_records_by_adapter(
        self, *, target_date_str: str | None, timezone_name: str
    ) -> dict[str, int]:
        target_cal = str(resolve_calendar_date(target_date_str, timezone_name))
        with self._lock:
            df = self.conn.execute(
                """
                SELECT api_name, COUNT(*) AS n
                FROM api_records
                WHERE target_calendar_date = ? AND timezone_name = ?
                GROUP BY api_name
                ORDER BY api_name
                """,
                [target_cal, timezone_name],
            ).fetchdf()
        if df.empty:
            return {}
        return {str(r["api_name"]): int(r["n"]) for _, r in df.iterrows()}

    def count_api_extracted_articles(self, *, target_date_str: str | None, timezone_name: str) -> int:
        start_utc, end_utc = target_date_range(target_date_str, timezone_name)
        with self._lock:
            row = self.conn.execute(
                """
                SELECT COUNT(*) FROM articles
                WHERE crawl_strategy_used = 'api_trafilatura_extract'
                  AND extracted_at >= ? AND extracted_at < ?
                """,
                [start_utc, end_utc],
            ).fetchone()
            return int(row[0] or 0)

    def count_articles_with_body_in_window(self, *, target_date_str: str | None, timezone_name: str) -> int:
        start_utc, end_utc = target_date_range(target_date_str, timezone_name)
        with self._lock:
            row = self.conn.execute(
                """
                SELECT COUNT(*) FROM articles
                WHERE extracted_at >= ? AND extracted_at < ?
                  AND content IS NOT NULL AND LENGTH(TRIM(content)) > 200
                """,
                [start_utc, end_utc],
            ).fetchone()
            return int(row[0] or 0)

    def count_errors_by_type_window(self, *, target_date_str: str | None, timezone_name: str) -> dict[str, int]:
        start_utc, end_utc = target_date_range(target_date_str, timezone_name)
        with self._lock:
            df = self.conn.execute(
                """
                SELECT error_type, COUNT(*) AS n
                FROM crawl_errors
                WHERE created_at >= ? AND created_at < ?
                GROUP BY error_type
                """,
                [start_utc, end_utc],
            ).fetchdf()
        if df.empty:
            return {}
        return {str(r["error_type"]): int(r["n"]) for _, r in df.iterrows()}

    def api_hub_errors_by_adapter(self, *, target_date_str: str | None, timezone_name: str) -> dict[str, int]:
        start_utc, end_utc = target_date_range(target_date_str, timezone_name)
        with self._lock:
            df = self.conn.execute(
                """
                SELECT stage, COUNT(*) AS n
                FROM crawl_errors
                WHERE created_at >= ? AND created_at < ?
                  AND stage LIKE 'api_hub:%'
                GROUP BY stage
                ORDER BY stage
                """,
                [start_utc, end_utc],
            ).fetchdf()
        out: dict[str, int] = {}
        if df.empty:
            return out
        for _, r in df.iterrows():
            st = str(r["stage"])
            adapter = st.split(":", 1)[-1] if ":" in st else st
            out[adapter] = int(r["n"])
        return out

    def export_today_api_metadata_csv(self, out_path: Path, *, target_date_str: str | None, timezone_name: str) -> None:
        target_cal = str(resolve_calendar_date(target_date_str, timezone_name))
        with self._lock:
            df = self.conn.execute(
                """
                SELECT api_name, source_id, record_type, title, url, published_at, updated_at,
                       language, domain, country, authors_json, discovery_method, content_hash, collected_at
                FROM api_records
                WHERE target_calendar_date = ? AND timezone_name = ?
                ORDER BY api_name, url
                """,
                [target_cal, timezone_name],
            ).fetchdf()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)

    def export_today_ai_input_jsonl(self, out_path: Path, *, target_date_str: str | None, timezone_name: str) -> None:
        """Full-text merge for local AI pipelines (do not commit if policy forbids)."""

        start_utc, end_utc = target_date_range(target_date_str, timezone_name)
        target_cal = str(resolve_calendar_date(target_date_str, timezone_name))
        out_path.parent.mkdir(parents=True, exist_ok=True)
        rows_out: list[dict[str, Any]] = []
        with self._lock:
            art_df = self.conn.execute(
                """
                SELECT id, source_id, title, url, published_at, language, content, content_length,
                       quality_score, crawl_strategy_used
                FROM articles
                WHERE extracted_at >= ? AND extracted_at < ?
                """,
                [start_utc, end_utc],
            ).fetchdf()
            api_df = self.conn.execute(
                """
                SELECT id, api_name, source_id, record_type, title, url, published_at, language,
                       content, summary, content_hash
                FROM api_records
                WHERE target_calendar_date = ? AND timezone_name = ?
                """,
                [target_cal, timezone_name],
            ).fetchdf()
        for _, r in art_df.iterrows():
            content = r.get("content")
            clen = int(r.get("content_length") or 0) if r.get("content_length") is not None else len(str(content or ""))
            rows_out.append(
                {
                    "id": str(r["id"]),
                    "source_type": "scrapy",
                    "api_name": "",
                    "source_id": str(r.get("source_id") or ""),
                    "title": str(r.get("title") or ""),
                    "url": str(r.get("url") or ""),
                    "published_at": str(r.get("published_at") or ""),
                    "language": str(r.get("language") or ""),
                    "content": content,
                    "summary": None,
                    "content_length": clen,
                    "quality_score": float(r["quality_score"]) if r.get("quality_score") is not None else None,
                    "crawl_strategy_used": str(r.get("crawl_strategy_used") or ""),
                    "record_type": "article",
                    "content_hash": None,
                }
            )
        for _, r in api_df.iterrows():
            summ = r.get("summary")
            body = r.get("content")
            text = body if isinstance(body, str) and body.strip() else summ
            rows_out.append(
                {
                    "id": str(r["id"]),
                    "source_type": "api",
                    "api_name": str(r.get("api_name") or ""),
                    "source_id": str(r.get("source_id") or ""),
                    "title": str(r.get("title") or ""),
                    "url": str(r.get("url") or ""),
                    "published_at": str(r.get("published_at") or ""),
                    "language": str(r.get("language") or ""),
                    "content": text,
                    "summary": str(summ) if summ else None,
                    "content_length": len(str(text or "")),
                    "quality_score": None,
                    "crawl_strategy_used": "api_record",
                    "record_type": str(r.get("record_type") or ""),
                    "content_hash": str(r.get("content_hash") or ""),
                }
            )
        with out_path.open("w", encoding="utf-8") as fh:
            for obj in rows_out:
                fh.write(json.dumps(obj, ensure_ascii=False, default=str) + "\n")


def new_id() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
