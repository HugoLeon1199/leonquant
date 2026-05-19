"""Mark sources the current stack cannot crawl (blocked / profile failed).

NotToday-only failures are **not** skip-listed — the site is reachable; only the date filter rejected URLs.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from settings import CrawlRules

# Real transport / HTTP blocks only — not AccessControlDetected (often false positive).
BLOCK_ERROR_TYPES = frozenset(
    {
        "FetchError",
        "ConnectError",
        "ConnectTimeout",
        "ReadTimeout",
        "HttpError",
        "PlaywrightDisabled",
    }
)
DATE_FILTER_ERROR_TYPES = frozenset({"NotToday", "PublishedDateMissingLikelyToday"})


@dataclass(frozen=True)
class SourceSkipVerdict:
    source_id: str
    domain: str
    reason: str
    detail: str
    block_errors: int
    date_filter_errors: int
    articles_in_db: int


def _err_counts(raw: dict[str, int] | Counter[str]) -> Counter[str]:
    return Counter(raw) if raw else Counter()


def classify_source_skip(
    *,
    source_id: str,
    domain: str,
    status: str | None,
    best_strategy: str | None,
    error_counts: dict[str, int] | Counter[str],
    articles_in_db: int,
    rules: CrawlRules,
) -> SourceSkipVerdict | None:
    """Return a skip verdict, or None if future crawls should still be attempted."""
    dom = (domain or "").strip().lower().removeprefix("www.")
    strat = (best_strategy or "").strip()
    st = (status or "").strip()

    manual = {d.strip().lower().removeprefix("www.") for d in (rules.manual_skip_domains or []) if d}
    if dom and dom in manual:
        return SourceSkipVerdict(
            source_id=source_id,
            domain=dom,
            reason="manual_skip",
            detail="manual_skip_domains",
            block_errors=0,
            date_filter_errors=0,
            articles_in_db=int(articles_in_db),
        )

    if st == "review" or strat == "manual_review":
        return SourceSkipVerdict(
            source_id=source_id,
            domain=dom,
            reason="profile_failed",
            detail=strat or st or "manual_review",
            block_errors=0,
            date_filter_errors=0,
            articles_in_db=int(articles_in_db),
        )

    if int(articles_in_db) > 0:
        return None

    errs = _err_counts(error_counts)
    if not errs:
        return None

    date_n = sum(errs.get(k, 0) for k in DATE_FILTER_ERROR_TYPES)
    block_n = sum(errs.get(k, 0) for k in BLOCK_ERROR_TYPES)
    other_n = sum(v for k, v in errs.items() if k not in DATE_FILTER_ERROR_TYPES and k not in BLOCK_ERROR_TYPES)

    if date_n > 0 and block_n == 0:
        return None

    if block_n == 0:
        return None

    min_block = max(1, int(rules.uncrawlable_min_block_errors))

    if block_n < min_block:
        return None

    if date_n > block_n:
        return None

    if other_n > block_n and block_n < min_block * 2:
        return None

    top = ", ".join(f"{t}:{n}" for t, n in errs.most_common(4))
    return SourceSkipVerdict(
        source_id=source_id,
        domain=dom,
        reason="blocked",
        detail=top or f"block_errors={block_n}",
        block_errors=block_n,
        date_filter_errors=date_n,
        articles_in_db=0,
    )


def refresh_source_crawl_skip(
    db: Any,
    *,
    rules: CrawlRules,
    export_txt_path: Any | None = None,
) -> dict[str, int]:
    """Recompute ``source_crawl_skip`` from profiles + crawl_errors + articles."""
    stats = db.refresh_source_crawl_skip(rules=rules)
    if export_txt_path is not None:
        db.export_source_crawl_skip_txt(export_txt_path)
    return stats
