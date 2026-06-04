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


def _validate_digest_content(c: dict[str, Any]) -> list[str]:
    err: list[str] = []
    mode = c.get("briefMode")
    if mode not in ("multisector-digest", "newsroom-brief"):
        err.append('content.json: briefMode must be "multisector-digest" or "newsroom-brief"')
    if mode == "newsroom-brief":
        if not str(c.get("editorNote") or "").strip():
            err.append("content.json: editorNote required for newsroom-brief")
        fp = c.get("frontPage")
        if not isinstance(fp, list) or len(fp) < 1:
            err.append("content.json: frontPage must be non-empty for newsroom-brief")
        sdb = c.get("sectorDeepBriefs")
        if not isinstance(sdb, list) or len(sdb) < 4:
            err.append("content.json: sectorDeepBriefs must have 4 sectors for newsroom-brief")
        else:
            for i, sec in enumerate(sdb[:4]):
                if not isinstance(sec, dict):
                    err.append(f"sectorDeepBriefs[{i}]: must be object")
                    continue
                dossiers = sec.get("storyDossiers") or []
                if not dossiers:
                    err.append(f"sectorDeepBriefs[{i}]: need storyDossiers")
                for j, d in enumerate(dossiers[:3]):
                    if isinstance(d, dict) and not str(d.get("whyItMatters") or "").strip():
                        err.append(f"sectorDeepBriefs[{i}].storyDossiers[{j}]: missing whyItMatters")
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
