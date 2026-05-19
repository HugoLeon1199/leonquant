"""Normalize inbound URLs and derive stable source identifiers."""

from __future__ import annotations

import re
from urllib.parse import urlparse, urlunparse

from pydantic import BaseModel, Field


class NormalizedSource(BaseModel):
    input_url: str
    normalized_url: str
    domain: str  # canonical without www
    scheme: str = "https"
    homepage_url: str = ""
    source_id: str = ""
    aliases: list[str] = Field(default_factory=list)


_SAFE_SOURCE_ID = re.compile(r"[^a-z0-9]+")


def generate_source_id(domain: str) -> str:
    d = domain.lower().strip(".")
    if d.startswith("www."):
        d = d[4:]
    d = d.replace(".", "_")
    d = _SAFE_SOURCE_ID.sub("_", d).strip("_")
    return d or "unknown_source"


def normalize_url(url: str) -> NormalizedSource:
    raw = url.strip()
    if not raw or raw.startswith("#"):
        raise ValueError("empty or commented")

    parsed = urlparse(raw)
    if not parsed.scheme:
        raw = "https://" + raw
        parsed = urlparse(raw)

    scheme = (parsed.scheme or "https").lower()
    netloc = (parsed.netloc or "").lower()

    if not netloc and parsed.path:
        parts = parsed.path.split("/", 1)
        netloc = parts[0].lower()
        rest = "/" + parts[1] if len(parts) > 1 else "/"
        parsed = urlparse(f"{scheme}://{netloc}{rest}")

    netloc = (parsed.netloc or "").lower()
    canonical_domain = netloc[4:] if netloc.startswith("www.") else netloc

    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    homepage_url = urlunparse((scheme, netloc, "/" if path in ("", "/") else path, "", "", ""))
    normalized_url = urlunparse((scheme, netloc, path if path else "/", "", "", ""))

    sid = generate_source_id(canonical_domain)

    return NormalizedSource(
        input_url=url.strip(),
        normalized_url=normalized_url,
        domain=canonical_domain,
        scheme=scheme,
        homepage_url=homepage_url,
        source_id=sid,
    )


def dedupe_sources(norm_items: list[NormalizedSource]) -> list[NormalizedSource]:
    """Keep first per canonical domain; attach aliases."""
    seen: dict[str, NormalizedSource] = {}
    order: list[str] = []
    for item in norm_items:
        key = item.domain
        if key not in seen:
            seen[key] = item.model_copy(deep=True)
            order.append(key)
        else:
            alias_url = item.input_url
            if alias_url not in seen[key].aliases and alias_url != seen[key].input_url:
                seen[key].aliases.append(alias_url)
    return [seen[k] for k in order]
