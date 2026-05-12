#!/usr/bin/env python3
"""Quality gate: validate final_summary.json + content.json (Global Market Strategy Brief v2)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from build_website_content import _LIST_MINS
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

_LOCAL_ONLY_MACRO_RE = re.compile(
    r"(?i)\b("
    r"cao tốc|long thành|sân bay long|tái cấu trúc ngân hàng|vietcombank|\bacb\b|\bbidv\b|\bssi\b|"
    r"vingroup|hoà phát|hòa phát|dự án bot|đường sắt đô thị|"
    r"cục dự trữ|nghị quyết.*?nội địa.*?chỉ"
    r")\b",
)

PUBLIC_FORBIDDEN_RE = re.compile(
    r"\bAI\b|artificial intelligence|(?i)\bautomation\b|(?i)\bcrawler\b|(?i)\bcrawl\b|\bGPT\b|"
    r"\bGemini\b|(?i)\bmodel\b|(?i)\bpipeline\b|source quality|verified links|"
    r"không phải khuyến nghị đầu tư|(?i)\bdisclaimer\b",
    re.IGNORECASE,
)

_INCREASE_BAD_SUBSTR = re.compile(
    r"lạm phát.*(cao hơn|tăng)|dầu.*(tăng sốc|tăng mạnh)|(?i)\busd\b.*tăng mạnh|"
    r"lợi suất.*tăng nhanh|loi suat.*tang nhanh|bán ròng mạnh|ban rong manh|"
    r"suy yếu đồng loạt|căng thẳng leo thang|gián đoạn.*chuỗi cung|supply shock|"
    r"địa chính trị.*leo thang|rủi ro địa chính",
    re.IGNORECASE,
)

_REDUCE_GOOD_SUBSTR = re.compile(
    r"(?i)usd\s+suy yếu|lợi suất.*hạ nhiệt|loi suat.*ha nhiet|thanh khoản.*cải thiện|"
    r"độ rộng.*cải thiện|khối ngoại mua ròng|dầu ổn định|tang truong on dinh|tăng trưởng ổn định",
    re.IGNORECASE,
)

_CANONICAL_INVESTOR_STATES = (
    "Cầm nhiều tiền mặt",
    "Đang nắm tài sản khỏe",
    "Đang lãi ngắn hạn",
    "Đang dùng margin / đòn bẩy",
    "Muốn mua mới",
    "Đang kẹt tài sản yếu",
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
        "whatChanged",
        "marketRegimeScore",
        "globalMacroDrivers",
        "intermarketMap",
        "transmissionChains",
        "quickActions",
        "allocationGuide",
        "priorityAndAvoid",
        "increaseRiskSignals",
        "reduceRiskSignals",
        "intradayPlaybook",
        "scenarioPlan",
        "viewChangeTriggers",
        "finalDecision",
    )
    out: list[str] = []
    for k in keys:
        if k in c:
            out.extend(_strings_from_value(c[k]))
    return out


def _collect_article_text(c: dict[str, Any]) -> list[str]:
    arts = c.get("allArticles")
    if not isinstance(arts, list):
        return []
    texts: list[str] = []
    for a in arts:
        if not isinstance(a, dict):
            continue
        for k in ("title", "summary", "category", "source"):
            texts.append(str(a.get(k, "") or ""))
    return texts


def _allocation_semantic_errors(rows: Any) -> list[str]:
    e: list[str] = []
    if not isinstance(rows, list):
        return ["content.allocationGuide must be a list for semantic check"]
    for i, r in enumerate(rows):
        if not isinstance(r, dict):
            continue
        profile = str(r.get("profile", "") or "").lower()
        lev = str(r.get("leverage", "") or r.get("margin", "") or "").lower()
        if "thận trọng" in profile or "than trong" in profile:
            if re.search(r"\b(cao|đầy|chủ động margin|margin cao|đòn bẩy cao)\b", lev) and "không" not in lev:
                if "rất thấp" not in lev:
                    e.append(
                        f"content.allocationGuide[{i}]: Thận trọng must not imply high leverage ({lev!r})",
                    )
        if "cân bằng" in profile or "can bang" in profile:
            if re.search(r"đòn bẩy cao|margin cao|\b70\s*%", lev):
                e.append(
                    f"content.allocationGuide[{i}]: Cân bằng must not use high leverage ({lev!r})",
                )
    return e


def _global_driver_local_errors(rows: Any) -> list[str]:
    e: list[str] = []
    if not isinstance(rows, list):
        return e
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        blob = f"{row.get('title', '')} {row.get('analysis', '')}"
        if _LOCAL_ONLY_MACRO_RE.search(blob) and not _GLOBAL_KW_RE.search(blob):
            e.append(
                f"content.globalMacroDrivers[{i}]: looks local-only (not global macro); move Vietnam specifics elsewhere.",
            )
    return e


def _quick_actions_repetition_errors(qa: Any) -> list[str]:
    if not isinstance(qa, list) or len(qa) < 4:
        return []
    actions = [
        str(r.get("action", "") or "").strip()
        for r in qa
        if isinstance(r, dict) and str(r.get("action", "") or "").strip()
    ]
    if len(actions) >= 4 and len(set(actions)) <= 2:
        return ["content.quickActions: actions are too repetitive across investor states."]
    return []


def _validate_content_semantics(c: dict[str, Any]) -> list[str]:
    e: list[str] = []
    brief_text = _collect_public_brief_text(c)
    if any(PUBLIC_FORBIDDEN_RE.search(t) for t in brief_text):
        e.append("content.json public brief contains forbidden wording (AI/automation/tooling/disclaimer).")

    art_text = _collect_article_text(c)
    if any(PUBLIC_FORBIDDEN_RE.search(t) for t in art_text):
        e.append("content.json allArticles contains forbidden wording for public site.")

    e.extend(_allocation_semantic_errors(c.get("allocationGuide")))
    e.extend(_global_driver_local_errors(c.get("globalMacroDrivers")))
    e.extend(_quick_actions_repetition_errors(c.get("quickActions")))

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

    fd = str(c.get("finalDecision", "") or "").strip()
    if len(fd) > 520:
        e.append(f"content.finalDecision too long ({len(fd)} chars); keep concise (<=520).")

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

    if str(c.get("schemaVersion", "") or "").strip() != "global-market-strategy-brief-v2":
        err.append("content.json schemaVersion must be global-market-strategy-brief-v2")

    for key in (
        "siteTitle",
        "sectionLabel",
        "generatedAt",
        "schemaVersion",
        "publicationIntro",
        "mainThesis",
        "whatChanged",
        "marketRegimeScore",
        "globalMacroDrivers",
        "intermarketMap",
        "transmissionChains",
        "quickActions",
        "allocationGuide",
        "priorityAndAvoid",
        "increaseRiskSignals",
        "reduceRiskSignals",
        "intradayPlaybook",
        "scenarioPlan",
        "viewChangeTriggers",
        "finalDecision",
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

    wc = c.get("whatChanged")
    if not isinstance(wc, list) or len(wc) < _LIST_MINS["what_changed"]:
        err.append(f"content.whatChanged must have at least {_LIST_MINS['what_changed']} items")
    else:
        for i, row in enumerate(wc):
            if not isinstance(row, dict):
                err.append(f"content.whatChanged[{i}] must be object")
                continue
            for f in ("variable", "change", "meaning"):
                if not str(row.get(f, "")).strip():
                    err.append(f"content.whatChanged[{i}].{f} must be non-empty")

    mrs = c.get("marketRegimeScore")
    if not isinstance(mrs, dict):
        err.append("content.marketRegimeScore must be object")
    else:
        items = mrs.get("items")
        if not isinstance(items, list) or len(items) < 4:
            err.append("content.marketRegimeScore.items must have at least 4 axes")
        if mrs.get("totalScore") is None:
            err.append("content.marketRegimeScore.totalScore must be present")
        if not str(mrs.get("regime", "")).strip():
            err.append("content.marketRegimeScore.regime must be non-empty")
        if not str(mrs.get("interpretation", "")).strip():
            err.append("content.marketRegimeScore.interpretation must be non-empty")

    gmd = c.get("globalMacroDrivers")
    if not isinstance(gmd, list) or len(gmd) < _LIST_MINS["global_macro_drivers"]:
        err.append(f"content.globalMacroDrivers must have at least {_LIST_MINS['global_macro_drivers']} items")
    else:
        for i, row in enumerate(gmd):
            if not isinstance(row, dict):
                err.append(f"content.globalMacroDrivers[{i}] must be object")
                continue
            impact = str(row.get("marketImpact", "") or row.get("vietnamImpact", "") or "").strip()
            for f in ("title", "analysis"):
                if not str(row.get(f, "")).strip():
                    err.append(f"content.globalMacroDrivers[{i}].{f} must be non-empty")
            if not impact:
                err.append(f"content.globalMacroDrivers[{i}].marketImpact must be non-empty")

    im = c.get("intermarketMap")
    if not isinstance(im, list) or len(im) < _LIST_MINS["intermarket_map"]:
        err.append(f"content.intermarketMap must have at least {_LIST_MINS['intermarket_map']} items")
    else:
        for i, row in enumerate(im):
            if not isinstance(row, dict):
                err.append(f"content.intermarketMap[{i}] must be object")
                continue
            for f in ("asset", "state", "action"):
                if not str(row.get(f, "")).strip():
                    err.append(f"content.intermarketMap[{i}].{f} must be non-empty")

    tc = c.get("transmissionChains")
    if not isinstance(tc, list) or len([x for x in tc if isinstance(x, str) and x.strip()]) < _LIST_MINS[
        "transmission_chains"
    ]:
        err.append(f"content.transmissionChains must have at least {_LIST_MINS['transmission_chains']} strings")

    qa = c.get("quickActions")
    if not isinstance(qa, list) or len(qa) < _LIST_MINS["quick_actions"]:
        err.append(f"content.quickActions must have at least {_LIST_MINS['quick_actions']} items")

    ag = c.get("allocationGuide")
    if not isinstance(ag, list) or len(ag) < _LIST_MINS["allocation_guide"]:
        err.append(f"content.allocationGuide must have at least {_LIST_MINS['allocation_guide']} items")
    else:
        for i, row in enumerate(ag):
            if not isinstance(row, dict):
                err.append(f"content.allocationGuide[{i}] must be object")
                continue
            lev = str(row.get("leverage", "") or row.get("margin", "") or "").strip()
            for f in ("profile", "stocks", "cash", "goldDefense", "cryptoHighRisk"):
                if not str(row.get(f, "") or "").strip():
                    err.append(f"content.allocationGuide[{i}].{f} must be non-empty")
            if not lev:
                err.append(f"content.allocationGuide[{i}].leverage must be non-empty")

    pa = c.get("priorityAndAvoid")
    if not isinstance(pa, dict):
        err.append("content.priorityAndAvoid must be object")
    else:
        pr = pa.get("prioritize")
        av = pa.get("avoidOrBeCareful")
        if not isinstance(pr, list) or len(pr) < 5:
            err.append("content.priorityAndAvoid.prioritize must have at least 5 items")
        if not isinstance(av, list) or len(av) < 5:
            err.append("content.priorityAndAvoid.avoidOrBeCareful must have at least 5 items")

    irs = c.get("increaseRiskSignals")
    if not isinstance(irs, list) or len(irs) < _LIST_MINS["increase_risk_signals"]:
        err.append(f"content.increaseRiskSignals must have at least {_LIST_MINS['increase_risk_signals']} items")

    rrs = c.get("reduceRiskSignals")
    if not isinstance(rrs, list) or len(rrs) < _LIST_MINS["reduce_risk_signals"]:
        err.append(f"content.reduceRiskSignals must have at least {_LIST_MINS['reduce_risk_signals']} items")

    ipb = c.get("intradayPlaybook")
    if not isinstance(ipb, list) or len(ipb) < _LIST_MINS["intraday_playbook"]:
        err.append(f"content.intradayPlaybook must have at least {_LIST_MINS['intraday_playbook']} items")

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

    vct = c.get("viewChangeTriggers")
    if not isinstance(vct, dict):
        err.append("content.viewChangeTriggers must be object")
    else:
        mp = vct.get("morePositiveIf")
        mn = vct.get("moreNegativeIf")
        if not isinstance(mp, list) or len([x for x in mp if isinstance(x, str) and x.strip()]) < 4:
            err.append("content.viewChangeTriggers.morePositiveIf must have at least 4 strings")
        if not isinstance(mn, list) or len([x for x in mn if isinstance(x, str) and x.strip()]) < 4:
            err.append("content.viewChangeTriggers.moreNegativeIf must have at least 4 strings")

    if not str(c.get("finalDecision", "")).strip():
        err.append("content.finalDecision must be non-empty string")

    forbidden = (
        "sourceQuality",
        "disclaimer",
        "webVerification",
        "verifiedLinks",
        "sourcesScanned",
        "articlesSelected",
        "confidence",
        "vietnamTransmission",
        "sectorPriority",
        "finalTakeaway",
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
            f"Summary must only contain Global Market Strategy Brief v2 keys; remove: {sorted(extra)}",
            file=sys.stderr,
        )
        return 1
    print("OK: final_summary.json passes Global Market Strategy Brief v2 validation.")
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
