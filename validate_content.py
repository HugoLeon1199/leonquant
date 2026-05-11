#!/usr/bin/env python3
"""Quality gate: validate final_summary.json (Macro Intelligence schema)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from finalize_summary_gpt import MACRO_INTELLIGENCE_SUMMARY_KEYS, validate_final_summary

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_FINAL = PROJECT_DIR / "final_summary.json"
DEFAULT_CONTENT = PROJECT_DIR / "content.json"


def _validate_content_json(path: Path) -> tuple[bool, list[str]]:
    err: list[str] = []
    if not path.exists():
        return False, [f"Missing content file: {path}"]
    try:
        c = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return False, [f"content.json: {e}"]
    if not isinstance(c, dict):
        return False, ["content.json: root must be object"]
    for key in (
        "siteTitle",
        "sectionLabel",
        "title",
        "date",
        "generatedAt",
        "marketRegime",
        "dailyThesis",
        "topMacroDrivers",
        "scenarioMap",
        "marketSnapshot",
        "allArticles",
    ):
        if key not in c:
            err.append(f"content.json missing key: {key}")
    ms = c.get("marketSnapshot")
    if ms is not None and not isinstance(ms, dict):
        err.append("content.marketSnapshot must be object")
    return (len(err) == 0, err)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate final_summary.json structure.")
    parser.add_argument("--final-input", default=str(DEFAULT_FINAL))
    parser.add_argument("--content-input", default=str(DEFAULT_CONTENT), help="Optional content.json checks")
    args = parser.parse_args()
    path = Path(args.final_input)
    if not path.exists():
        print(f"Missing file: {path}", file=sys.stderr)
        return 1
    payload = json.loads(path.read_text(encoding="utf-8"))
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        print("Invalid final_summary: 'summary' must be an object", file=sys.stderr)
        return 1
    ok, errors = validate_final_summary(summary)
    if not ok:
        for e in errors:
            print(e, file=sys.stderr)
        return 1
    extra = set(summary.keys()) - MACRO_INTELLIGENCE_SUMMARY_KEYS
    if extra:
        print(
            f"Summary must only contain Macro Intelligence keys; remove: {sorted(extra)}",
            file=sys.stderr,
        )
        return 1
    legacy_deny = ("key_points", "brief_stories", "asset_impact_table")
    bad = [k for k in legacy_deny if k in summary and summary[k]]
    if bad:
        print(f"Legacy schema keys must be empty or absent: {bad}", file=sys.stderr)
        return 1
    print("OK: final_summary.json passes Macro Intelligence validation.")
    cpath = Path(args.content_input)
    cok, cerrs = _validate_content_json(cpath)
    if not cok:
        for e in cerrs:
            print(e, file=sys.stderr)
        return 1
    print("OK: content.json keys look valid for Macro Intelligence UI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
