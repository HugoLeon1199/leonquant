#!/usr/bin/env python3
"""Validate content.json for public multisector digest (48h news)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_CONTENT = PROJECT_DIR / "content.json"


def _norm_text(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _duplicateish(*values: Any) -> bool:
    seen: set[str] = set()
    texts = [_norm_text(v) for v in values if _norm_text(v)]
    for text in texts:
        if text in seen:
            return True
        seen.add(text)
    if len(texts) < 2:
        return False
    for i, left in enumerate(texts):
        for right in texts[i + 1 :]:
            short, long = (left, right) if len(left) <= len(right) else (right, left)
            if len(short) >= 24 and short in long:
                return True
    return False


def _validate_digest_content(c: dict[str, Any]) -> list[str]:
    err: list[str] = []
    mode = c.get("briefMode")
    if mode not in ("multisector-digest", "newsroom-brief"):
        err.append('content.json: briefMode must be "multisector-digest" or "newsroom-brief"')
    if mode == "newsroom-brief":
        eb = c.get("executiveBriefing") if isinstance(c.get("executiveBriefing"), dict) else {}
        eb_content = str(eb.get("content") or "").strip()
        eb_sections = eb.get("sections") if isinstance(eb.get("sections"), dict) else {}
        has_overview = bool(eb_content) or any(
            str(v).strip() for v in eb_sections.values() if v is not None
        )
        if not has_overview and not str(c.get("editorNote") or "").strip():
            err.append("content.json: executiveBriefing or editorNote required for newsroom-brief")
        if not isinstance(eb.get("links"), list) or not eb.get("links"):
            err.append("content.json: executiveBriefing.links must contain at least 1 source for newsroom-brief")
        fp = c.get("frontPage")
        if not isinstance(fp, list) or len(fp) < 1:
            err.append("content.json: frontPage must be non-empty for newsroom-brief")
        else:
            expected_rank = 1
            for i, row in enumerate(fp):
                if not isinstance(row, dict):
                    err.append(f"frontPage[{i}]: must be object")
                    continue
                if int(row.get("rank") or 0) != expected_rank:
                    err.append(f"frontPage[{i}]: rank must be continuous starting at 1")
                expected_rank += 1
                if not isinstance(row.get("links"), list) or not row.get("links"):
                    err.append(f"frontPage[{i}]: links must contain at least 1 source")
                if _duplicateish(
                    row.get("title"),
                    row.get("oneSentence"),
                    row.get("whyItMatters"),
                    row.get("watchNext"),
                ):
                    err.append(f"frontPage[{i}]: title/summary/why/watch have duplicate phrasing")
        sdb = c.get("sectorDeepBriefs")
        if not isinstance(sdb, list) or len(sdb) < 4:
            err.append("content.json: sectorDeepBriefs must have 4 sectors for newsroom-brief")
        else:
            for i, sec in enumerate(sdb[:4]):
                if not isinstance(sec, dict):
                    err.append(f"sectorDeepBriefs[{i}]: must be object")
                    continue
                thesis = str(sec.get("sectorThesis") or "").strip()
                links = sec.get("links") or []
                dossiers = sec.get("storyDossiers") or []
                if not thesis and not links and not dossiers:
                    err.append(f"sectorDeepBriefs[{i}]: need sectorThesis or links")
                for j, dossier in enumerate(dossiers):
                    if not isinstance(dossier, dict):
                        err.append(f"sectorDeepBriefs[{i}].storyDossiers[{j}]: must be object")
                        continue
                    if not isinstance(dossier.get("links"), list) or not dossier.get("links"):
                        err.append(f"sectorDeepBriefs[{i}].storyDossiers[{j}]: links required")
                    devs = dossier.get("mainDevelopments")
                    if not isinstance(devs, list) or len([x for x in devs if str(x).strip()]) < 2:
                        err.append(f"sectorDeepBriefs[{i}].storyDossiers[{j}]: need at least 2 mainDevelopments")
                    if _duplicateish(dossier.get("whyItMatters"), " ".join(dossier.get("watchNext") or [])):
                        err.append(f"sectorDeepBriefs[{i}].storyDossiers[{j}]: whyItMatters duplicates watchNext")
        if not str((c.get("mainThesis") or {}).get("thesis") or "").strip():
            err.append("content.json: mainThesis.thesis required")
        articles = c.get("articleLinkIndex")
        if articles is not None and not isinstance(articles, list):
            err.append("content.json: articleLinkIndex must be list")
        return err
    if not str(c.get("generatedAt") or "").strip():
        err.append("content.json: missing generatedAt")
    sectors = c.get("digestSectors")
    if not isinstance(sectors, list) or len(sectors) < 4:
        err.append("content.json: digestSectors must have 4 sectors (finance, tech, news, trends)")
    else:
        for i, s in enumerate(sectors[:12]):
            if not isinstance(s, dict):
                err.append(f"digestSectors[{i}]: must be object")
                continue
            if not str(s.get("name") or "").strip():
                err.append(f"digestSectors[{i}]: missing name")
    mt = c.get("mainThesis")
    if not isinstance(mt, dict) or not str(mt.get("thesis") or "").strip():
        err.append("content.json: mainThesis.thesis required")
    articles = c.get("articleLinkIndex")
    if articles is not None and not isinstance(articles, list):
        err.append("content.json: articleLinkIndex must be list")
    return err


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate content.json for digest web.")
    parser.add_argument("--content-input", default=str(DEFAULT_CONTENT))
    parser.add_argument(
        "--content-only",
        action="store_true",
        help="Alias for digest-only validation (default behavior).",
    )
    args = parser.parse_args()
    _ = args.content_only

    path = Path(args.content_input)
    if not path.is_file():
        print(f"Missing file: {path}", file=sys.stderr)
        return 1
    try:
        c = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        return 1
    if not isinstance(c, dict):
        print("content.json must be an object", file=sys.stderr)
        return 1

    errs = _validate_digest_content(c)
    if errs:
        for e in errs:
            print(e, file=sys.stderr)
        return 1
    n = len(c.get("digestSectors") or [])
    mode = c.get("briefMode", "multisector-digest")
    print(f"OK: content.json valid ({n} sector(s), mode={mode}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
