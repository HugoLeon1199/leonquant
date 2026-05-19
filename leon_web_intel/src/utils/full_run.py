"""Resolve CLI limits: 0 means \"no artificial cap\" for full production runs."""

from __future__ import annotations

# Upper bound per source to avoid runaway queues while treating 0 as unlimited intent.
FULL_RUN_URL_CAP_PER_SOURCE = 2_000_000


def resolve_max_urls_per_source(n: int) -> int:
    return FULL_RUN_URL_CAP_PER_SOURCE if n <= 0 else n


def profile_limit_arg(n: int | None) -> int | None:
    """None or <=0 → profile all sources (no --limit slice)."""
    if n is None:
        return None
    return None if n <= 0 else n
