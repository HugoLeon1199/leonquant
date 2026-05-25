"""Persist Scrapy items into DuckDB (articles + crawl_errors)."""

from __future__ import annotations

import logging
from pathlib import Path

import scrapy
from itemadapter import ItemAdapter

from extraction.article_extractor import compute_quality_score
from scrapy_engine.extract_helpers import access_control_triplet, extract_with_trafilatura
from scrapy_engine.items import ArticleItem
from settings import CrawlRules, load_crawl_rules
from storage.db import WebIntelDB, new_id, utc_now
from storage.raw_store import RawStore
from utils.today_filter import (
    is_datetime_in_range,
    is_url_likely_recent_calendar_days,
    parse_any_datetime,
    resolve_calendar_date,
    target_recent_calendar_days_range,
)

logger = logging.getLogger(__name__)


class WebIntelArticlePipeline:
    """Never raises from ``process_item``; records failures to ``crawl_errors``."""

    def __init__(self, db_path: Path, crawl_rules_path: Path, raw_root: Path, summary: object) -> None:
        self.db_path = Path(db_path)
        self.crawl_rules_path = Path(crawl_rules_path)
        self.raw_root = Path(raw_root)
        self.summary = summary
        self.db: WebIntelDB | None = None
        self.rules: CrawlRules | None = None
        self.raw_store: RawStore | None = None
        self.seen_hashes: set[str] = set()

    @classmethod
    def from_crawler(cls, crawler: scrapy.crawler.Crawler) -> WebIntelArticlePipeline:
        return cls(
            db_path=Path(crawler.settings["WEB_INTEL_DB_PATH"]),
            crawl_rules_path=Path(crawler.settings["WEB_INTEL_CRAWL_RULES_PATH"]),
            raw_root=Path(crawler.settings["WEB_INTEL_RAW_ROOT"]),
            summary=crawler.settings["WEB_INTEL_SUMMARY"],
        )

    def open_spider(self, spider: scrapy.Spider) -> None:
        self.db = WebIntelDB(self.db_path)
        self.rules = load_crawl_rules(self.crawl_rules_path)
        self.raw_store = RawStore(self.raw_root)
        self.seen_hashes = self.db.fetch_distinct_content_hashes()

    def close_spider(self, spider: scrapy.Spider) -> None:
        if self.db:
            self.db.close()
            self.db = None

    def _bump_pipeline_items(self) -> None:
        sm = self.summary
        if sm is None:
            return
        with sm.lock:
            sm.pipeline_items += 1

    def _bump_articles(self) -> None:
        sm = self.summary
        if sm is None:
            return
        with sm.lock:
            sm.articles_inserted += 1

    def _bump_errors(self) -> None:
        sm = self.summary
        if sm is None:
            return
        with sm.lock:
            sm.errors_logged += 1

    def _bump_duplicates(self) -> None:
        sm = self.summary
        if sm is None:
            return
        with sm.lock:
            sm.duplicates_skipped += 1

    def _log_error(
        self,
        *,
        source_id: str,
        url: str,
        error_type: str,
        error_message: str,
        stage: str = "scrapy_pipeline",
        frontier_status: str = "failed",
    ) -> None:
        if not self.db:
            return
        try:
            self.db.insert_crawl_error(
                {
                    "id": new_id(),
                    "source_id": source_id,
                    "url": url,
                    "stage": stage,
                    "error_type": error_type,
                    "error_message": error_message[:2000],
                    "created_at": utc_now(),
                }
            )
            if url:
                if frontier_status == "skipped":
                    self.db.mark_frontier_skipped(
                        url=url,
                        reason_type=error_type,
                        reason_message=error_message,
                    )
                else:
                    self.db.mark_frontier_failed(
                        url=url,
                        error_type=error_type,
                        error_message=error_message,
                    )
            self._bump_errors()
        except Exception as exc:  # noqa: BLE001
            logger.exception("crawl_errors insert failed: %s", exc)

    def process_item(self, item: ArticleItem, spider: scrapy.Spider) -> ArticleItem:
        self._bump_pipeline_items()
        assert self.db is not None and self.rules is not None and self.raw_store is not None

        adapter = ItemAdapter(item)
        source_id = adapter.get("source_id") or ""
        url = adapter.get("url") or ""
        strategy = adapter.get("crawl_strategy_used") or ""
        source_active = bool(adapter.get("source_active", True))
        err_type = adapter.get("error_type")
        err_msg = adapter.get("error_message")

        if url:
            self.db.upsert_frontier_url(
                source_id=source_id,
                url=url,
                strategy=strategy,
                status="crawling",
            )

        status = adapter.get("response_status")
        if status is not None and int(status) >= 400:
            self._log_error(
                source_id=source_id,
                url=url,
                error_type="HttpError",
                error_message=f"status={status}",
            )
            adapter.pop("html_body", None)
            return item

        if err_type:
            self._log_error(
                source_id=source_id,
                url=url,
                error_type=str(err_type),
                error_message=str(err_msg or ""),
                stage="scrapy_fetch",
                frontier_status="skipped" if str(err_type) == "NonHtmlSkipped" else "failed",
            )
            adapter.pop("html_body", None)
            return item

        html = adapter.get("html_body")
        if not html:
            self._log_error(
                source_id=source_id,
                url=url,
                error_type="MissingBody",
                error_message="no html_body on item",
            )
            return item

        if isinstance(html, bytes):
            try:
                html_text = html.decode("utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                html_text = ""
        else:
            html_text = str(html)

        min_len = int(spider.settings.get("WEB_INTEL_MIN_ARTICLE_LENGTH", self.rules.min_article_content_length))

        extracted = extract_with_trafilatura(html_text)
        content_hash = extracted.content_hash
        content_length = extracted.content_length

        paywall, login, captcha = access_control_triplet(
            html_text,
            self.rules.paywall_keywords,
            self.rules.login_keywords,
            self.rules.captcha_keywords,
            extracted_plain=extracted.content or "",
            content_length=content_length,
            min_article_content_length=min_len,
        )
        access_relaxed_keep = (
            self.rules.keep_extract_despite_access_signal_if_meets_min_length
            and not captcha
            and content_length >= min_len
            and (paywall or login)
        )
        if (paywall or login or captcha) and not access_relaxed_keep:
            self._log_error(
                source_id=source_id,
                url=url,
                error_type="AccessControlDetected",
                error_message=f"paywall={paywall} login={login} captcha={captcha}",
                frontier_status="skipped",
            )
            adapter.pop("html_body", None)
            return item

        raw_path = ""
        try:
            raw_path = self.raw_store.save_html(source_id, html_text.encode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            logger.debug("raw_store.save_html failed {}: {}", url, exc)
        if content_length < min_len:
            self._log_error(
                source_id=source_id,
                url=url,
                error_type="ShortContent",
                error_message=f"length={content_length} min={min_len}",
            )
            adapter.pop("html_body", None)
            return item

        today_only = bool(spider.settings.getbool("WEB_INTEL_TODAY_ONLY", False))

        if content_hash and content_hash in self.seen_hashes:
            if today_only and self.db is not None:
                self.db.touch_article_extracted_by_hash(content_hash)
            self._bump_duplicates()
            self.db.mark_frontier_skipped(
                url=url,
                reason_type="DuplicateContent",
                reason_message="content_hash already exists",
            )
            adapter.pop("html_body", None)
            return item
        if today_only:
            target_date_str = spider.settings.get("WEB_INTEL_TARGET_DATE") or "today"
            timezone_name = spider.settings.get("WEB_INTEL_TIMEZONE") or "Asia/Ho_Chi_Minh"
            recent_n = max(1, int(spider.settings.getint("WEB_INTEL_RECENT_CALENDAR_DAYS", 2)))
            start_utc, end_utc = target_recent_calendar_days_range(target_date_str, timezone_name, recent_n)
            target_d = resolve_calendar_date(target_date_str, timezone_name)

            cand_raw = adapter.get("candidate_published_at")
            cand_pub = parse_any_datetime(str(cand_raw)) if cand_raw else None
            extracted_pub = (
                parse_any_datetime(str(extracted.published_at)) if extracted.published_at else None
            )
            resolved_pub = cand_pub if cand_pub is not None else extracted_pub

            likely = is_url_likely_recent_calendar_days(url, target_d, recent_n)

            if cand_pub is not None and is_datetime_in_range(cand_pub, start_utc, end_utc):
                pass
            elif resolved_pub is not None and is_datetime_in_range(resolved_pub, start_utc, end_utc):
                pass
            elif likely:
                pass
            elif self.rules.today_allow_undated_uncertain_urls and (
                cand_raw is None
                or str(adapter.get("discovery_source") or "") == "rss_homepage"
            ):
                pass
            elif resolved_pub is not None and not is_datetime_in_range(resolved_pub, start_utc, end_utc):
                self._log_error(
                    source_id=source_id,
                    url=url,
                    error_type="NotToday",
                    error_message="published_at outside recent calendar window",
                    frontier_status="skipped",
                )
                adapter.pop("html_body", None)
                return item
            else:
                if not self.rules.today_allow_undated_uncertain_urls:
                    self._log_error(
                        source_id=source_id,
                        url=url,
                        error_type="NotToday",
                        error_message="no trustworthy recent-day signal (date/path)",
                        frontier_status="skipped",
                    )
                    adapter.pop("html_body", None)
                    return item

        score = compute_quality_score(
            title=extracted.title,
            content_length=content_length,
            published_at=extracted.published_at,
            source_active=source_active,
            content_hash=content_hash,
            url=url,
            strategy=strategy,
            raw_path=raw_path,
            extract_ok=True,
            paywall_triplet=(paywall, login, captcha),
            existing_hashes=self.seen_hashes,
        )

        row = {
            "id": new_id(),
            "source_id": source_id,
            "url": url,
            "title": extracted.title,
            "published_at": extracted.published_at,
            "content": extracted.content,
            "content_length": content_length,
            "content_hash": content_hash,
            "language": extracted.language,
            "crawl_strategy_used": strategy,
            "raw_path": raw_path,
            "extracted_at": utc_now(),
            "quality_score": score,
        }

        try:
            self.db.insert_article(row)
            self.db.mark_frontier_crawled(url=url, content_hash=content_hash)
            self.seen_hashes.add(content_hash)
            self._bump_articles()
        except Exception as exc:  # noqa: BLE001
            logger.exception("insert_article failed %s: %s", url, exc)
            self._log_error(
                source_id=source_id,
                url=url,
                error_type="DbInsertError",
                error_message=str(exc),
            )

        adapter.pop("html_body", None)
        return item
