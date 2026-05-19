"""Lightweight HTML metadata helpers."""

from __future__ import annotations

from bs4 import BeautifulSoup


def extract_meta_description(html: str) -> str | None:
    soup = BeautifulSoup(html, "lxml")
    tag = soup.find("meta", attrs={"name": "description"})
    if tag and tag.get("content"):
        return str(tag["content"]).strip()
    og = soup.find("meta", attrs={"property": "og:description"})
    if og and og.get("content"):
        return str(og["content"]).strip()
    return None
