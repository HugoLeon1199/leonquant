"""Download homepage HTML and compute baseline readability signals."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from bs4 import BeautifulSoup
from loguru import logger
import trafilatura

from profiler.normalize import NormalizedSource
from settings import CrawlRules
from storage.raw_store import RawStore


@dataclass
class HTMLProbeResult:
    status_code: int
    html_title: str
    html_text_length: int
    html_link_count: int
    script_count: int
    html_extract_ok: bool
    sample_extracted_text_length: int
    raw_path: str
    raw_html: str


def run_html_probe(
    norm: NormalizedSource,
    homepage_url: str,
    rules: CrawlRules,
    fetch_text: Callable[[str], tuple[int, str]],
    raw_store: RawStore,
) -> HTMLProbeResult:
    status, html = fetch_text(homepage_url)
    if status >= 400:
        return HTMLProbeResult(
            status_code=status,
            html_title="",
            html_text_length=0,
            html_link_count=0,
            script_count=0,
            html_extract_ok=False,
            sample_extracted_text_length=0,
            raw_path="",
            raw_html="",
        )

    soup = BeautifulSoup(html, "lxml")
    title_el = soup.title
    html_title = title_el.get_text(strip=True) if title_el else ""

    visible_text = soup.get_text(separator="\n", strip=True)
    html_text_length = len(visible_text)

    links = soup.find_all("a", href=True)
    html_link_count = len(links)
    scripts = soup.find_all("script")
    script_count = len(scripts)

    extracted = None
    try:
        extracted = trafilatura.extract(html)
    except Exception as exc:  # noqa: BLE001
        logger.debug("trafilatura extract failed for {}: {}", homepage_url, exc)

    sample_len = len(extracted) if extracted else 0
    html_extract_ok = bool(extracted and sample_len >= rules.min_extract_text_length)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw_path = raw_store.save_html(norm.source_id, html.encode("utf-8"), ts)

    return HTMLProbeResult(
        status_code=status,
        html_title=html_title,
        html_text_length=html_text_length,
        html_link_count=html_link_count,
        script_count=script_count,
        html_extract_ok=html_extract_ok,
        sample_extracted_text_length=sample_len,
        raw_path=raw_path,
        raw_html=html,
    )
