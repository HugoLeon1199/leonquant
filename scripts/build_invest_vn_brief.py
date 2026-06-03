#!/usr/bin/env python3
"""
Phân tích sâu kinh tế–đầu tư Việt Nam từ content.json (digest 48h).
Output: invest_vn_brief.json (+ web/) — dùng tab Chuyên mục kinh tế đầu tư (khối dưới).
Không đụng pipeline tin 48h / GDELT world.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import google.generativeai as genai

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTENT = ROOT / "content.json"
DEFAULT_OUT = ROOT / "invest_vn_brief.json"
WEB_OUT = ROOT / "web" / "invest_vn_brief.json"
SCHEMA_VERSION = "invest-vn-brief-v1"

VN_HOST_MARKERS = (
    ".vn",
    "baochinhphu.vn",
    "vneconomy.vn",
    "cafef.vn",
    "plo.vn",
    "genk.vn",
)

VN_SECTOR_CODES = frozenset({"finance", "politics", "tech", "lifestyle"})


def _load_env() -> None:
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8-sig").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        key = k.strip()
        if key and not os.environ.get(key):
            os.environ[key] = v.strip().strip('"').strip("'")


def _is_vn_url(url: str) -> bool:
    u = (url or "").strip().lower()
    if not u.startswith("http"):
        return False
    try:
        host = urlparse(u).netloc.replace("www.", "")
    except Exception:
        return False
    return any(m in host for m in VN_HOST_MARKERS)


def _parse_gemini_json(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        return {}
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, flags=re.DOTALL)
    if fence:
        raw = fence.group(1).strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start >= 0 and end > start:
        raw = raw[start : end + 1]
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _clip(s: str, n: int) -> str:
    t = re.sub(r"\s+", " ", (s or "").strip())
    return t if len(t) <= n else t[: n - 1].rstrip() + "…"


def build_input_pack(content: dict[str, Any]) -> dict[str, Any]:
    pack: dict[str, Any] = {
        "generated_at": content.get("generatedAt") or "",
        "vietnam_highlights": _clip(str(content.get("digestVietnamHighlights") or ""), 1200),
        "vietnam_bullets": [
            _clip(str(b), 400)
            for b in (content.get("digestVietnamBullets") or [])
            if str(b).strip()
        ][:12],
        "overview_bullets": [],
        "sector_snippets": [],
        "vn_articles": [],
    }
    mt = content.get("mainThesis") or {}
    if isinstance(mt, dict) and mt.get("thesis"):
        pack["overview_bullets"].append(_clip(str(mt["thesis"]), 500))

    for sec in ("digestExecutiveSummary", "digestInternationalHighlights"):
        t = _clip(str(content.get(sec) or ""), 400)
        if t:
            pack["overview_bullets"].append(t)
    pack["overview_bullets"] = pack["overview_bullets"][:4]

    for sec in content.get("digestSectors") or []:
        if not isinstance(sec, dict):
            continue
        code = str(sec.get("code") or "").strip().lower()
        if code not in VN_SECTOR_CODES:
            continue
        items_out = []
        for it in sec.get("items") or []:
            if not isinstance(it, dict):
                continue
            links = it.get("links") or []
            vn_links = [
                {
                    "url": str(lk.get("url") or "").strip(),
                    "title": _clip(str(lk.get("title") or it.get("headline") or ""), 120),
                    "source": str(lk.get("source") or lk.get("label") or "").strip(),
                }
                for lk in links
                if isinstance(lk, dict) and _is_vn_url(str(lk.get("url") or ""))
            ]
            if not vn_links:
                continue
            items_out.append(
                {
                    "headline": _clip(str(it.get("headline") or ""), 200),
                    "links": vn_links[:2],
                }
            )
        if items_out or _clip(str(sec.get("summary") or ""), 80):
            pack["sector_snippets"].append(
                {
                    "code": code,
                    "name": str(sec.get("name") or code),
                    "summary": _clip(str(sec.get("summary") or ""), 600),
                    "items": items_out[:8],
                }
            )

    seen_urls: set[str] = set()
    for art in content.get("articleLinkIndex") or []:
        if not isinstance(art, dict):
            continue
        u = str(art.get("url") or "").strip()
        if not _is_vn_url(u) or u in seen_urls:
            continue
        seen_urls.add(u)
        pack["vn_articles"].append(
            {
                "title": _clip(str(art.get("title") or ""), 160),
                "url": u,
                "source": str(art.get("source") or art.get("host") or "").strip(),
            }
        )
        if len(pack["vn_articles"]) >= 25:
            break

    return pack


def gemini_analyze_vn(pack: dict[str, Any]) -> dict[str, Any]:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("GEMINI_API_KEY missing — skip invest VN brief", file=sys.stderr)
        return {}
    genai.configure(api_key=api_key)
    model_name = (
        os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite").strip() or "gemini-3.1-flash-lite"
    )
    model = genai.GenerativeModel(model_name)

    pack_json = json.dumps(pack, ensure_ascii=False, indent=2)
    prompt = f"""
Bạn là biên tập chuyên mục kinh tế đầu tư Việt Nam của LeonQuant.

CHỈ dùng dữ liệu trong "input_pack" bên dưới (digest 48 giờ, nguồn trong nước). Không dùng kiến thức ngoài để bịa số liệu, ngày tháng, hay sự kiện không có trong pack.
Không khuyến nghị mua/bán/múc. Không nhắc AI, crawler, GDELT, pipeline, hệ thống.

Nhiệm vụ — hai lớp thời gian:
1) themes_48h: 3–5 chủ đề nói COM NHẤT trong 48 giờ qua tại Việt Nam (kinh tế, tài chính, điều hành, BĐS, FDI, ngân hàng, năng lượng, thị trường trong nước…).
   Mỗi chủ đề: title, why_hot (vì sao được quan tâm), developments (3–6 bullet diễn biến), investor_lens (ý nghĩa với nhà đầu tư VN, trung lập), links (chỉ url có trong pack).
2) now_watch: 2–4 mục đang chuyển biến GẦN ĐÂY / cần theo dõi tiếp (status: "đang diễn ra" hoặc "sắp có"), what_to_watch, links nếu có.

lead: 2–4 câu tổng quan bức tranh VN 48h.
gaps: một câu nếu thiếu dữ liệu; nếu đủ thì để chuỗi rỗng.

Trả về JSON (không markdown):
{{
  "lead": "...",
  "themes_48h": [
    {{
      "rank": 1,
      "title": "...",
      "why_hot": "...",
      "developments": ["..."],
      "investor_lens": "...",
      "links": [{{"url": "https://...", "title": "...", "source": "..."}}]
    }}
  ],
  "now_watch": [
    {{
      "title": "...",
      "status": "đang diễn ra",
      "what_to_watch": "...",
      "links": [{{"url": "...", "title": "...", "source": "..."}}]
    }}
  ],
  "gaps": ""
}}

input_pack:
{pack_json}
""".strip()

    try:
        response = model.generate_content(prompt)
        parsed = _parse_gemini_json(response.text or "")
        return parsed if parsed else {}
    except Exception as exc:
        print(f"Gemini invest VN brief failed: {exc}", file=sys.stderr)
        return {}


def normalize_brief(raw: dict[str, Any], pack: dict[str, Any]) -> dict[str, Any]:
    allowed_urls = set()
    for art in pack.get("vn_articles") or []:
        if isinstance(art, dict) and art.get("url"):
            allowed_urls.add(str(art["url"]))
    for sec in pack.get("sector_snippets") or []:
        for it in (sec.get("items") or []) if isinstance(sec, dict) else []:
            for lk in it.get("links") or []:
                if isinstance(lk, dict) and lk.get("url"):
                    allowed_urls.add(str(lk["url"]))

    def _norm_links(links: Any) -> list[dict[str, str]]:
        out: list[dict[str, str]] = []
        if not isinstance(links, list):
            return out
        for lk in links:
            if not isinstance(lk, dict):
                continue
            u = str(lk.get("url") or "").strip()
            if u and allowed_urls and u not in allowed_urls and not _is_vn_url(u):
                continue
            if not u.startswith("http"):
                continue
            out.append(
                {
                    "url": u,
                    "title": _clip(str(lk.get("title") or u), 160),
                    "source": _clip(str(lk.get("source") or ""), 80),
                }
            )
        return out[:4]

    themes = []
    for i, th in enumerate(raw.get("themes_48h") or []):
        if not isinstance(th, dict):
            continue
        title = _clip(str(th.get("title") or ""), 200)
        if not title:
            continue
        devs = [
            _clip(str(d), 350)
            for d in (th.get("developments") or [])
            if str(d).strip()
        ][:6]
        themes.append(
            {
                "rank": int(th.get("rank") or i + 1),
                "title": title,
                "why_hot": _clip(str(th.get("why_hot") or ""), 500),
                "developments": devs,
                "investor_lens": _clip(str(th.get("investor_lens") or ""), 500),
                "links": _norm_links(th.get("links")),
            }
        )
    themes.sort(key=lambda x: x["rank"])

    now_watch = []
    for nw in raw.get("now_watch") or []:
        if not isinstance(nw, dict):
            continue
        title = _clip(str(nw.get("title") or ""), 200)
        if not title:
            continue
        now_watch.append(
            {
                "title": title,
                "status": _clip(str(nw.get("status") or "đang diễn ra"), 40),
                "what_to_watch": _clip(str(nw.get("what_to_watch") or ""), 500),
                "links": _norm_links(nw.get("links")),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "channel": "invest_vn",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_digest_at": pack.get("generated_at") or "",
        "window_hours": 48,
        "lead": _clip(str(raw.get("lead") or ""), 800),
        "themes_48h": themes[:5],
        "now_watch": now_watch[:4],
        "gaps": _clip(str(raw.get("gaps") or ""), 300),
    }


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    _load_env()
    ap = argparse.ArgumentParser(description="Build invest VN brief from content.json")
    ap.add_argument("--content", type=Path, default=DEFAULT_CONTENT)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--skip-gemini", action="store_true", help="Only build empty shell from pack metadata")
    args = ap.parse_args()

    if not args.content.is_file():
        print(f"Missing {args.content}", file=sys.stderr)
        return 2

    content = json.loads(args.content.read_text(encoding="utf-8-sig"))
    pack = build_input_pack(content)

    if args.skip_gemini:
        raw = {}
    else:
        raw = gemini_analyze_vn(pack)

    brief = normalize_brief(raw, pack)
    if not brief.get("themes_48h") and not brief.get("lead"):
        brief["gaps"] = brief.get("gaps") or "Chưa tạo được phân tích VN (thiếu GEMINI hoặc dữ liệu)."

    atomic_write(args.output, brief)
    atomic_write(WEB_OUT, brief)
    print(f"Wrote {args.output} ({len(brief.get('themes_48h') or [])} themes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
