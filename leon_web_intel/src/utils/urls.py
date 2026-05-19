"""URL helpers."""

from __future__ import annotations

from urllib.parse import urlparse, urlunparse


def strip_www(host: str) -> str:
    h = host.lower()
    if h.startswith("www."):
        return h[4:]
    return h


def origin_from_parts(scheme: str, netloc: str, path: str = "/") -> str:
    if not path:
        path = "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return urlunparse((scheme.lower(), netloc.lower(), path, "", "", ""))


def join_origin_and_path(origin_netloc: str, scheme: str, suffix_path: str) -> str:
    """suffix_path starts with /"""
    path = suffix_path
    if not path.startswith("/"):
        path = "/" + path
    return urlunparse((scheme.lower(), origin_netloc.lower(), path, "", "", ""))
