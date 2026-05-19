"""Disk-backed HTTP response cache."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from settings import CrawlRules
from utils.hashing import sha256_text
from utils.rate_limit import DomainRateLimiter


@dataclass
class CacheEntry:
    status_code: int
    headers: dict[str, str]
    body: bytes
    cached_at: float

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "status_code": self.status_code,
            "headers": self.headers,
            "body_b64": None,
            "body_hex": self.body.hex(),
            "cached_at": self.cached_at,
        }

    @staticmethod
    def from_json_dict(d: dict[str, Any]) -> "CacheEntry":
        body = bytes.fromhex(d["body_hex"])
        return CacheEntry(
            status_code=int(d["status_code"]),
            headers=dict(d["headers"]),
            body=body,
            cached_at=float(d["cached_at"]),
        )


class HttpCache:
    def __init__(self, cache_dir: Path, *, enabled: bool, ttl_seconds: float | None = None) -> None:
        self.cache_dir = cache_dir
        self.enabled = enabled
        self.ttl_seconds = ttl_seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _path(self, url: str) -> Path:
        return self.cache_dir / f"{sha256_text(url)}.json"

    def get(self, url: str) -> CacheEntry | None:
        if not self.enabled:
            return None
        path = self._path(url)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            entry = CacheEntry.from_json_dict(data)
            if self.ttl_seconds is not None:
                if time.time() - entry.cached_at > self.ttl_seconds:
                    return None
            return entry
        except Exception as exc:  # noqa: BLE001
            logger.debug("cache read failed for {}: {}", url, exc)
            return None

    def set(self, url: str, entry: CacheEntry) -> None:
        if not self.enabled:
            return
        path = self._path(url)
        with self._lock:
            path.write_text(json.dumps(entry.to_json_dict()), encoding="utf-8")


class CachedHttpClient:
    """httpx sync client with retries, per-domain delay, optional disk cache."""

    def __init__(
        self,
        rules: CrawlRules,
        *,
        cache_dir: Path,
        profile_cache_days: int,
    ) -> None:
        self.rules = rules
        self.cache = HttpCache(
            cache_dir,
            enabled=rules.http_cache_enabled,
            ttl_seconds=profile_cache_days * 86400,
        )
        self.rate_limiter = DomainRateLimiter(rules.default_delay_seconds)
        self._client = httpx.Client(
            headers={"User-Agent": rules.user_agent},
            follow_redirects=True,
            timeout=httpx.Timeout(rules.request_timeout_seconds),
        )
        self._lock = threading.Lock()

    def close(self) -> None:
        self._client.close()

    def _fetch_uncached(self, url: str) -> CacheEntry:
        parsed = httpx.URL(url)
        host = parsed.host or ""
        self.rate_limiter.wait(host)

        @retry(
            stop=stop_after_attempt(max(1, self.rules.max_retries + 1)),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=6),
            reraise=True,
        )
        def _do() -> httpx.Response:
            return self._client.get(url)

        resp = _do()
        headers = {k.lower(): v for k, v in resp.headers.items()}
        entry = CacheEntry(
            status_code=resp.status_code,
            headers={k: headers[k] for k in sorted(headers.keys())},
            body=resp.content,
            cached_at=time.time(),
        )
        return entry

    def get(self, url: str) -> CacheEntry:
        """Return cached entry or fetch. Network + retries run outside the mutex so
        profiler/scraper threads are not serialized on unrelated URLs."""
        with self._lock:
            cached = self.cache.get(url)
            if cached:
                return cached

        entry = self._fetch_uncached(url)

        with self._lock:
            cached = self.cache.get(url)
            if cached:
                return cached
            self.cache.set(url, entry)
        return entry

    def get_text(self, url: str, encoding: str = "utf-8") -> tuple[int, str]:
        entry = self.get(url)
        text = entry.body.decode(encoding, errors="replace")
        return entry.status_code, text
