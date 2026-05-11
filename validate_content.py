#!/usr/bin/env python3
"""Quality gate: validate final_summary.json + content.json (Investment Strategy Brief)."""

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
        "generatedAt",
        "publicationIntro",
        "mainThesis",
        "globalMacroDrivers",
        "vietnamTransmission",
        "quickActions",
        "allocationGuide",
        "sectorPriority",
        "increaseRiskSignals",
        "reduceRiskSignals",
        "scenarioPlan",
        "finalTakeaway",
        "allArticles",
    ):
        if key not in c:
            err.append(f"content.json missing key: {key}")

    pub = c.get("publicationIntro")
    if not isinstance(pub, dict):
        err.append("content.publicationIntro must be object")
    elif not str(pub.get("headline", "")).strip() or not str(pub.get("description", "")).strip():
        err.append("content.publicationIntro.headline/description must be non-empty")

    mt = c.get("mainThesis")
    if not isinstance(mt, dict):
        err.append("content.mainThesis must be object")
    else:
        for f in ("regime", "thesis", "actionConclusion"):
            if not str(mt.get(f, "")).strip():
                err.append(f"content.mainThesis.{f} must be non-empty")

    gmd = c.get("globalMacroDrivers")
    if not isinstance(gmd, list) or len(gmd) < 3:
        err.append("content.globalMacroDrivers must have at least 3 items")
    else:
        for i, row in enumerate(gmd):
            if not isinstance(row, dict):
                err.append(f"content.globalMacroDrivers[{i}] must be object")
                continue
            for f in ("title", "analysis", "vietnamImpact"):
                if not str(row.get(f, "")).strip():
                    err.append(f"content.globalMacroDrivers[{i}].{f} must be non-empty")

    qa = c.get("quickActions")
    if not isinstance(qa, list) or len(qa) < 4:
        err.append("content.quickActions must have at least 4 items")

    ag = c.get("allocationGuide")
    if not isinstance(ag, list) or len(ag) < 3:
        err.append("content.allocationGuide must have at least 3 items")

    sp = c.get("sectorPriority")
    if not isinstance(sp, list) or len(sp) < 6:
        err.append("content.sectorPriority must have at least 6 items")

    irs = c.get("increaseRiskSignals")
    if not isinstance(irs, list) or len(irs) < 4:
        err.append("content.increaseRiskSignals must have at least 4 items")

    rrs = c.get("reduceRiskSignals")
    if not isinstance(rrs, list) or len(rrs) < 4:
        err.append("content.reduceRiskSignals must have at least 4 items")

    vt = c.get("vietnamTransmission")
    if not isinstance(vt, dict):
        err.append("content.vietnamTransmission must be object")
    elif not str(vt.get("summary", "")).strip():
        err.append("content.vietnamTransmission.summary must be non-empty")

    scenario = c.get("scenarioPlan")
    if not isinstance(scenario, dict):
        err.append("content.scenarioPlan must be object")
    else:
        for case in ("baseCase", "bullCase", "bearCase"):
            sc = scenario.get(case)
            if not isinstance(sc, dict):
                err.append(f"content.scenarioPlan.{case} must be object")
            else:
                for f in ("title", "description", "action"):
                    if not str(sc.get(f, "")).strip():
                        err.append(f"content.scenarioPlan.{case}.{f} must be non-empty")

    if not str(c.get("finalTakeaway", "")).strip():
        err.append("content.finalTakeaway must be non-empty string")

    forbidden = (
        "sourceQuality",
        "disclaimer",
        "webVerification",
        "verifiedLinks",
        "sourcesScanned",
        "articlesSelected",
        "confidence",
    )
    for fk in forbidden:
        if fk in c:
            err.append(f"content.json must not expose public key: {fk}")

    return (len(err) == 0, err)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate final_summary.json + content.json structure.")
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
            f"Summary must only contain Investment Strategy Brief keys; remove: {sorted(extra)}",
            file=sys.stderr,
        )
        return 1
    print("OK: final_summary.json passes Investment Strategy Brief validation.")
    cpath = Path(args.content_input)
    cok, cerrs = _validate_content_json(cpath)
    if not cok:
        for e in cerrs:
            print(e, file=sys.stderr)
        return 1
    print("OK: content.json valid for public brief.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
