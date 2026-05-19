"""Fetch and parse robots.txt."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

from loguru import logger


@dataclass
class RobotsResult:
    robots_url: str
    robots_ok: bool
    robots_sitemaps: list[str]
    robots_disallow_detected: bool
    can_fetch_homepage: bool


_SITEMAP_RE = re.compile(r"^\s*Sitemap:\s*(.+)\s*$", re.I | re.M)


def check_robots(
    *,
    scheme: str,
    domain_with_host: str,
    homepage_url: str,
    user_agent: str,
    fetch_text: Callable[[str], tuple[int, str]],
) -> RobotsResult:
    """domain_with_host may include www; used as netloc for robots URL."""
    robots_url = urljoin(f"{scheme}://{domain_with_host}/", "robots.txt")
    sitemaps: list[str] = []
    disallow_detected = False
    can_fetch = True
    robots_ok = True

    try:
        status, text = fetch_text(robots_url)
        if status >= 400:
            return RobotsResult(
                robots_url=robots_url,
                robots_ok=True,
                robots_sitemaps=[],
                robots_disallow_detected=False,
                can_fetch_homepage=True,
            )

        for m in _SITEMAP_RE.finditer(text):
            sitemaps.append(m.group(1).strip())

        lower = text.lower()
        if "disallow:" in lower:
            for line in text.splitlines():
                ln = line.strip()
                if ln.lower().startswith("disallow:"):
                    path = ln.split(":", 1)[1].strip()
                    if path and path != "":
                        disallow_detected = True

        rp = RobotFileParser()
        rp.parse(text.splitlines())
        can_fetch = rp.can_fetch(user_agent, homepage_url)
        robots_ok = True
    except Exception as exc:  # noqa: BLE001
        logger.debug("robots fetch/parse failed for {}: {}", robots_url, exc)
        robots_ok = False

    return RobotsResult(
        robots_url=robots_url,
        robots_ok=robots_ok,
        robots_sitemaps=sitemaps,
        robots_disallow_detected=disallow_detected,
        can_fetch_homepage=can_fetch,
    )
