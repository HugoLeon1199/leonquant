"""Optional Playwright rendering — disabled unless explicitly enabled."""

from __future__ import annotations

from loguru import logger


def fetch_rendered_html(url: str) -> str | None:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # noqa: BLE001
        logger.error("playwright import failed: {}", exc)
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=60_000)
            content = page.content()
            browser.close()
            return content
    except Exception as exc:  # noqa: BLE001
        logger.error("playwright fetch failed for {}: {}", url, exc)
        return None
