"""Persist raw crawl payloads under data/raw."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from utils.hashing import sha256_bytes


class RawStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        (root / "html").mkdir(parents=True, exist_ok=True)
        (root / "rss").mkdir(parents=True, exist_ok=True)
        (root / "sitemap").mkdir(parents=True, exist_ok=True)

    def save_html(self, source_id: str, body: bytes, timestamp: str | None = None) -> str:
        ts = timestamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        h = sha256_bytes(body)[:16]
        path = self.root / "html" / f"{source_id}_{h}_{ts}.html"
        path.write_bytes(body)
        return str(path)

    def save_rss(self, source_id: str, body: bytes) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        h = sha256_bytes(body)[:16]
        path = self.root / "rss" / f"{source_id}_{h}_{ts}.xml"
        path.write_bytes(body)
        return str(path)

    def save_sitemap(self, source_id: str, body: bytes, ext: str = "xml") -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        h = sha256_bytes(body)[:16]
        path = self.root / "sitemap" / f"{source_id}_{h}_{ts}.{ext}"
        path.write_bytes(body)
        return str(path)
