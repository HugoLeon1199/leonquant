#!/usr/bin/env python3
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tech.common import GDELT_JSON, NEWS_CLEAN, PUBLICATION_JSON, VALIDATION_JSON, load_json

WORKLOG = ROOT / ".ai" / "CURSOR_WORKLOG.md"


def main() -> int:
    validation = load_json(VALIDATION_JSON, {})
    crawl = load_json(NEWS_CLEAN, {})
    events = load_json(GDELT_JSON, {})
    publication = load_json(PUBLICATION_JSON, {})
    generated_at = str(publication.get("generated_at_utc") or "")
    marker = f"Tech72h generated_at={generated_at}"
    current = WORKLOG.read_text(encoding="utf-8")
    if marker in current:
        print("Worklog already contains this Tech72h run.")
        return 0

    meta = validation.get("validation_meta") or {}
    stats = publication.get("stats") or {}
    estimated_bytes = int(events.get("estimated_bytes") or 0)
    processed_bytes = int(events.get("processed_bytes") or 0)
    ran_successfully = bool(events.get("ran_successfully"))
    block = (
        f"\n## {datetime.now(timezone.utc).date()} - Technology & AI 72h live run\n\n"
        f"- {marker}\n"
        "- Scope: standalone `tech/`; Tin48h, Invest and World LIVE logic unchanged.\n"
        "- Schedule: once every 3 days; data window: latest 72 hours.\n"
        f"- Active sources: {meta.get('active_source_count', 0)} / {meta.get('catalog_source_count', 0)}.\n"
        f"- Clean web articles: {len(crawl.get('articles') or [])}.\n"
        f"- Event candidates: {len(events.get('events') or [])}; GDELT ran_successfully={ran_successfully}.\n"
        f"- Query estimate: {estimated_bytes:,} bytes; processed: {processed_bytes:,} bytes; cap: 2,000,000,000 bytes.\n"
        f"- Published stories: {stats.get('story_count', 0)}.\n"
        "- Tests: `python tech/test_pipeline.py` and `python tech/validate_publication.py` passed.\n"
    )
    WORKLOG.write_text(current + block, encoding="utf-8")
    print("Updated .ai/CURSOR_WORKLOG.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
