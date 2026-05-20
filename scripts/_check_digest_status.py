#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "news_for_ai.json",
    "gemini_digest_outline.json",
    "gemini_digest_partials.json",
    "gemini_digest_summary.json",
    "enriched_news.json",
    "gemini_summary.json",
]

for name in FILES:
    p = ROOT / name
    if not p.is_file():
        print(f"{name}: MISSING")
        continue
    mb = p.stat().st_size / 1024 / 1024
    line = f"{name}: {mb:.2f} MB"
    if name == "news_for_ai.json":
        d = json.loads(p.read_text(encoding="utf-8"))
        line += f" | articles={d.get('count')} window={d.get('window')}"
    elif name == "gemini_digest_outline.json":
        d = json.loads(p.read_text(encoding="utf-8"))
        o = d.get("outline") or {}
        line += f" | themes={len(o.get('dominant_themes') or [])}"
    elif name == "gemini_digest_partials.json":
        d = json.loads(p.read_text(encoding="utf-8"))
        line += f" | partials={len(d.get('partials') or [])}"
    elif name == "gemini_digest_summary.json":
        d = json.loads(p.read_text(encoding="utf-8"))
        s = d.get("summary") or {}
        line += f" | keys={list(s.keys())[:5]}"
    print(line)
