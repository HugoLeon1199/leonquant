"""Sitemap discovery with gzip support."""

from __future__ import annotations

import gzip
import io
import xml.etree.ElementTree as ET
from collections import deque
from collections.abc import Callable
from urllib.parse import urljoin, urlparse

from loguru import logger

from profiler.normalize import NormalizedSource
from settings import CrawlRules


def _local(tag: str) -> str:
    return tag.split("}")[-1] if tag.startswith("{") else tag


def _collect_urls_from_root(root: ET.Element) -> tuple[bool, list[str], bool]:
    tag = _local(root.tag)
    urls: list[str] = []
    if tag == "urlset":
        for url_el in root:
            if _local(url_el.tag) != "url":
                continue
            for child in url_el:
                if _local(child.tag) == "loc" and (child.text or "").strip():
                    urls.append(child.text.strip())
        return True, urls, False
    if tag == "sitemapindex":
        for sm_el in root:
            if _local(sm_el.tag) != "sitemap":
                continue
            for child in sm_el:
                if _local(child.tag) == "loc" and (child.text or "").strip():
                    urls.append(child.text.strip())
                    break
        return True, urls, True
    body_preview = ET.tostring(root, encoding="unicode").lower()
    if "<urlset" in body_preview or "<sitemapindex" in body_preview:
        return True, urls, False
    return False, urls, False


def _maybe_decompress(url: str, body: bytes) -> bytes:
    if url.endswith(".gz") or ".xml.gz" in url.lower():
        try:
            return gzip.decompress(body)
        except OSError:
            try:
                with gzip.GzipFile(fileobj=io.BytesIO(body)) as gz:
                    return gz.read()
            except Exception:
                return body
    if len(body) > 2 and body[:2] == b"\x1f\x8b":
        try:
            return gzip.decompress(body)
        except OSError:
            return body
    return body


def parse_sitemap_bytes(body: bytes, url: str) -> tuple[bool, list[str], bool]:
    raw = _maybe_decompress(url, body)
    lower = raw.decode("utf-8", errors="replace").lower()
    if "<urlset" not in lower and "<sitemapindex" not in lower:
        return False, [], False
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return False, [], False
    ok, urls, is_index = _collect_urls_from_root(root)
    if not ok:
        return False, [], False
    if is_index:
        return len(urls) > 0, urls, True
    return len(urls) > 0, urls, False


def discover_sitemap_urls(
    norm: NormalizedSource,
    rules: CrawlRules,
    robots_sitemaps: list[str],
    fetch_bytes: Callable[[str], tuple[int, bytes]],
) -> tuple[list[str], int]:
    parsed = urlparse(norm.homepage_url or norm.normalized_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    seeds: list[str] = []
    seen_seed: set[str] = set()

    def add_seed(u: str) -> None:
        u = u.strip()
        if u and u not in seen_seed:
            seen_seed.add(u)
            seeds.append(u)

    for sm in robots_sitemaps:
        add_seed(sm)

    for path in rules.sitemap_candidate_paths:
        add_seed(urljoin(origin + "/", path.lstrip("/")))

    validated: list[str] = []
    validated_set: set[str] = set()
    queue: deque[str] = deque(seeds)
    parsed_count = 0

    while queue and parsed_count < rules.max_sitemaps_to_parse_in_profiler:
        cand = queue.popleft()
        try:
            status, body = fetch_bytes(cand)
            if status >= 400 or not body:
                continue
            ok, locs, is_index = parse_sitemap_bytes(body, cand)
            if not ok:
                continue
            if cand not in validated_set:
                validated_set.add(cand)
                validated.append(cand)
            parsed_count += 1

            if is_index:
                for child in locs:
                    if parsed_count >= rules.max_sitemaps_to_parse_in_profiler:
                        break
                    if child in validated_set:
                        continue
                    try:
                        st2, body2 = fetch_bytes(child)
                        if st2 >= 400 or not body2:
                            continue
                        ok2, article_locs, _ = parse_sitemap_bytes(body2, child)
                        if not ok2:
                            continue
                        if child not in validated_set:
                            validated_set.add(child)
                            validated.append(child)
                        parsed_count += 1
                        _ = article_locs  # validated urlset has article urls; profiler only needs sitemap URLs list
                    except Exception as exc:  # noqa: BLE001
                        logger.debug("child sitemap failed {}: {}", child, exc)
        except Exception as exc:  # noqa: BLE001
            logger.debug("sitemap candidate failed {}: {}", cand, exc)

    return validated, len(validated)
