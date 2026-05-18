#!/usr/bin/env python3
"""Split config/sources_seed.txt into config/tiers/*.txt + tiers_manifest.json (domain → tier_id)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "config" / "sources_seed.txt"
OUT_DIR = ROOT / "config" / "tiers"
MANIFEST = ROOT / "config" / "tiers_manifest.json"

SEP_RE = re.compile(r"^#\s*=+\s*$")


def slug_header(comment_line: str) -> str:
    s = comment_line.lstrip("#").strip().lower()
    buf: list[str] = []
    for ch in s:
        if ch.isalnum():
            buf.append(ch)
        elif ch in " /.-":
            buf.append("_")
    slug = "".join(buf).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "tier"


def domain_from_url(line: str) -> str:
    s = line.strip()
    if not s.startswith("http"):
        s = "https://" + s
    netloc = urlparse(s).netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


def main() -> None:
    if not SEED.is_file():
        raise SystemExit(f"missing {SEED}")

    lines = SEED.read_text(encoding="utf-8").splitlines()
    tiers: list[tuple[str, str, list[str]]] = []  # id, title, urls
    pending_title: str | None = None
    pending_id: str | None = None
    pending_urls: list[str] = []

    def flush() -> None:
        nonlocal pending_title, pending_id, pending_urls
        if pending_id and pending_urls:
            tiers.append((pending_id, pending_title or pending_id, pending_urls[:]))
            pending_title = None
            pending_id = None
            pending_urls = []

    phase = "seek_sep"
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if phase == "seek_sep":
            if line.startswith("#") and SEP_RE.match(line):
                phase = "in_block"
            continue
        if line.startswith("#") and SEP_RE.match(line):
            flush()
            continue
        if line.startswith("#"):
            flush()
            pending_title = line.lstrip("#").strip()
            pending_id = slug_header(line)
            continue
        if pending_id and (line.startswith("http") or "://" in line or "." in line):
            pending_urls.append(line)

    flush()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, str] = {}
    for i, (tid, title, urls) in enumerate(tiers, start=1):
        fname = f"{i:02d}_{tid}.txt"
        body_lines = [
            f"# tier_id={tid}",
            f"# {title}",
            "#",
        ]
        body_lines.extend(urls)
        (OUT_DIR / fname).write_text("\n".join(body_lines) + "\n", encoding="utf-8")
        for u in urls:
            dom = domain_from_url(u)
            if dom:
                manifest[dom] = tid

    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(tiers)} tier files under {OUT_DIR} and {MANIFEST}")


if __name__ == "__main__":
    main()
