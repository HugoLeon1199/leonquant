#!/usr/bin/env python3
"""Quality gate: validate final_summary.json + content.json (Investment Strategy Brief)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from finalize_summary_gpt import MACRO_INTELLIGENCE_SUMMARY_KEYS, validate_final_summary

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_FINAL = PROJECT_DIR / "final_summary.json"
DEFAULT_CONTENT = PROJECT_DIR / "content.json"

_GLOBAL_KW_RE = re.compile(
    r"fed|mỹ|my\b|usd|dxy|lợi suất|loi suat|dầu|dau|lạm phát|lam phat|trung quốc|trung quoc|"
    r"thương mại|thuong mai|địa chính trị|dia chinh tri|toàn cầu|toan cau|euro|ecb|opec|brent|"
    r"thế giới|the gioi|global|china|oil|inflation|geopolit|imf",
    re.IGNORECASE,
)

PUBLIC_FORBIDDEN_RE = re.compile(
    r"\bAI\b|artificial intelligence|(?i)\bautomation\b|(?i)\bcrawler\b|(?i)\bcrawl\b|\bGPT\b|"
    r"\bGemini\b|(?i)\bmodel\b|(?i)\bpipeline\b|source quality|verified links|"
    r"không phải khuyến nghị đầu tư|(?i)\bdisclaimer\b",
    re.IGNORECASE,
)

_INCREASE_BAD_SUBSTR = re.compile(
    r"(giá )?dầu.*tăng mạnh|giá vàng.*tăng mạnh|leo thang|xấu đi|bán ròng mạnh|lạm phát cao hơn|"
    r"USD/VND tăng nhanh|thủng hỗ trợ|suy yếu đồng loạt|căng thẳng địa chính trị",
    re.IGNORECASE,
)

_REDUCE_GOOD_SUBSTR = re.compile(
    r"tăng trưởng ổn định|lạm phát thấp hơn|ngân hàng cải thiện|khối ngoại mua ròng|USD/VND ổn định|"
    r"thanh khoản cải thiện",
    re.IGNORECASE,
)

_CANONICAL_INVESTOR_STATES = (
    "Cầm nhiều tiền mặt",
    "Đang nắm cổ phiếu tốt",
    "Đang lãi ngắn hạn",
    "Đang dùng margin cao",
    "Muốn mua mới",
    "Đang kẹt cổ phiếu yếu",
)


def _strings_from_value(v: Any) -> list[str]:
    if isinstance(v, str):
        return [v]
    if isinstance(v, dict):
        acc: list[str] = []
        for vv in v.values():
            acc.extend(_strings_from_value(vv))
        return acc
    if isinstance(v, list):
        acc = []
        for item in v:
            acc.extend(_strings_from_value(item))
        return acc
    return []


def _collect_public_brief_text(c: dict[str, Any]) -> list[str]:
    keys = (
        "siteTitle",
        "sectionLabel",
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
    )
    out: list[str] = []
    for k in keys:
        if k in c:
            out.extend(_strings_from_value(c[k]))
    return out


def _allocation_semantic_errors(rows: Any) -> list[str]:
    e: list[str] = []
    if not isinstance(rows, list):
        return ["content.allocationGuide must be a list for semantic check"]
    for i, r in enumerate(rows):
        if not isinstance(r, dict):
            continue
        profile = str(r.get("profile", "") or "").lower()
        margin = str(r.get("margin", "") or "")
        if "thận trọng" in profile or "than trong" in profile:
            if re.search(r"\d\s*%", margin):
                e.append(
                    f"content.allocationGuide[{i}]: Thận trọng must not use numeric margin ({margin!r})",
                )
        if "cân bằng" in profile or "can bang" in profile:
            if re.search(r"20\s*%", margin, re.IGNORECASE):
                e.append(
                    f"content.allocationGuide[{i}]: Cân bằng must not use 20% margin ({margin!r})",
                )
    return e


def _validate_content_semantics(c: dict[str, Any]) -> list[str]:
    e: list[str] = []
    if any(PUBLIC_FORBIDDEN_RE.search(t) for t in _collect_public_brief_text(c)):
        e.append("content.json public brief contains forbidden wording (AI/automation/tooling/disclaimer).")

    e.extend(_allocation_semantic_errors(c.get("allocationGuide")))

    irs = c.get("increaseRiskSignals")
    if isinstance(irs, list):
        for i, row in enumerate(irs):
            if not isinstance(row, dict):
                continue
            sig = str(row.get("signal", "") or "")
            if _INCREASE_BAD_SUBSTR.search(sig):
                e.append(
                    f"content.increaseRiskSignals[{i}]: signal looks risk-off, not confirmation: {sig[:80]!r}",
                )

    rrs = c.get("reduceRiskSignals")
    if isinstance(rrs, list):
        for i, row in enumerate(rrs):
            if not isinstance(row, dict):
                continue
            sig = str(row.get("signal", "") or "")
            if _REDUCE_GOOD_SUBSTR.search(sig):
                e.append(
                    f"content.reduceRiskSignals[{i}]: signal looks risk-on, not warning: {sig[:80]!r}",
                )

    gmd = c.get("globalMacroDrivers")
    if isinstance(gmd, list):
        global_hits = 0
        for row in gmd:
            if not isinstance(row, dict):
                continue
            blob = f"{row.get('title', '')} {row.get('analysis', '')}"
            if _GLOBAL_KW_RE.search(blob):
                global_hits += 1
        if global_hits < 2:
            e.append(
                f"content.globalMacroDrivers: need at least 2 clearly global drivers "
                f"(Fed/USD/oil/inflation/China/trade/geopolitics); matched {global_hits}.",
            )

    qa = c.get("quickActions")
    if isinstance(qa, list):
        states_lower = {
            str(r.get("investorState", "") or "").strip().lower()
            for r in qa
            if isinstance(r, dict)
        }
        for canon in _CANONICAL_INVESTOR_STATES:
            if canon.lower() not in states_lower:
                e.append(
                    f"content.quickActions: missing investor state {canon!r} (expected six canonical labels).",
                )

    ft = str(c.get("finalTakeaway", "") or "").strip()
    if len(ft) > 520:
        e.append(f"content.finalTakeaway too long ({len(ft)} chars); keep concise (<=520).")

    return e


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
    if not isinstance(qa, list) or len(qa) < 6:
        err.append("content.quickActions must have at least 6 items")

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

    err.extend(_validate_content_semantics(c))

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
