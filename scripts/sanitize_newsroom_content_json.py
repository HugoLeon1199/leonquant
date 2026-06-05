#!/usr/bin/env python3
"""Re-filter newsroom links + soften copy on published content.json (no Gemini)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.newsroom_copy import soften_editor_note, soften_newsroom_text  # noqa: E402
from scripts.newsroom_source_match import filter_urls_for_story  # noqa: E402
from summarize_news_gemini import DigestUrlIndex  # noqa: E402


def _norm(s: str) -> str:
    return " ".join(str(s or "").strip().lower().split())


def _articles_from_content(data: dict[str, Any]) -> list[dict[str, Any]]:
    arts = data.get("allArticles")
    if isinstance(arts, list) and arts:
        return [a for a in arts if isinstance(a, dict)]
    idx = data.get("articleLinkIndex")
    if isinstance(idx, list):
        return [
            {
                "url": str(x.get("url") or ""),
                "title": str(x.get("title") or ""),
                "source": str(x.get("source") or ""),
            }
            for x in idx
            if isinstance(x, dict) and str(x.get("url") or "").strip()
        ]
    return []


def _link_label(host: str, source: str) -> str:
    from build_website_content import _link_display_label, _url_hostname

    h = host or _url_hostname(str(source or ""))
    return _link_display_label(h, source)


def _filter_story_links(
    links: list[dict[str, Any]],
    *,
    headline: str,
    context: str,
    index: DigestUrlIndex,
    by_url: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    urls = [str(lk.get("url") or "").strip() for lk in links if str(lk.get("url") or "").strip()]
    valid = filter_urls_for_story(urls, headline, index, context=context)
    out: list[dict[str, Any]] = []
    hl_norm = _norm(headline)
    for u in valid:
        art = by_url.get(u) or {}
        art_title = str(art.get("title") or "").strip()
        host = ""
        try:
            from urllib.parse import urlparse

            host = urlparse(u).hostname or ""
            host = host.replace("www.", "")
        except Exception:
            pass
        title = art_title
        if not title or _norm(title) == hl_norm:
            title = art_title or host or u
        src = str(art.get("source") or "").strip()
        out.append(
            {
                "url": u,
                "title": title,
                "host": host,
                "source": src,
                "label": _link_label(host, src),
            }
        )
    return out


def sanitize_newsroom_public_content(data: dict[str, Any]) -> dict[str, Any]:
    if data.get("briefMode") != "newsroom-brief":
        return data

    articles = _articles_from_content(data)
    index = DigestUrlIndex(articles)
    by_url = {str(a.get("url") or "").strip(): a for a in articles if str(a.get("url") or "").strip()}

    out = dict(data)
    note = soften_editor_note(str(out.get("editorNote") or out.get("editor_note") or ""))
    out["editorNote"] = note
    pub = out.get("publicationIntro")
    if isinstance(pub, dict) and pub.get("description"):
        pub = dict(pub)
        pub["description"] = soften_editor_note(str(pub.get("description") or ""))
        out["publicationIntro"] = pub

    fp_out: list[dict[str, Any]] = []
    for row in out.get("frontPage") or []:
        if not isinstance(row, dict):
            continue
        item = dict(row)
        title = soften_newsroom_text(str(item.get("title") or "").strip())
        if title:
            item["title"] = title
        for key in ("oneSentence", "whyItMatters", "watchNext"):
            if item.get(key):
                item[key] = soften_newsroom_text(str(item[key]))
        ctx = str(item.get("oneSentence") or "")
        links = item.get("links") if isinstance(item.get("links"), list) else []
        item["links"] = _filter_story_links(
            links, headline=title, context=ctx, index=index, by_url=by_url
        )
        fp_out.append(item)
    out["frontPage"] = fp_out

    sectors_out: list[dict[str, Any]] = []
    for sec in out.get("sectorDeepBriefs") or []:
        if not isinstance(sec, dict):
            continue
        sec2 = dict(sec)
        if sec2.get("sectorThesis"):
            sec2["sectorThesis"] = soften_newsroom_text(str(sec2["sectorThesis"]))
        dossiers: list[dict[str, Any]] = []
        for d in sec2.get("storyDossiers") or []:
            if not isinstance(d, dict):
                continue
            card = dict(d)
            st = soften_newsroom_text(str(card.get("title") or "").strip())
            if st:
                card["title"] = st
            for key in ("summary", "whyItMatters"):
                if card.get(key):
                    card[key] = soften_newsroom_text(str(card[key]))
            ctx = str(card.get("summary") or "")
            links = card.get("links") if isinstance(card.get("links"), list) else []
            card["links"] = _filter_story_links(
                links, headline=st, context=ctx, index=index, by_url=by_url
            )
            if card["links"]:
                dossiers.append(card)
        sec2["storyDossiers"] = dossiers
        sub_out: list[dict[str, Any]] = []
        for sb in sec2.get("subsectorBriefs") or []:
            if not isinstance(sb, dict):
                continue
            sb2 = dict(sb)
            sb_links = sb2.get("links") if isinstance(sb2.get("links"), list) else []
            sb2["links"] = _filter_story_links(
                sb_links,
                headline=str(sb2.get("name") or ""),
                context=str(sb2.get("overview") or ""),
                index=index,
                by_url=by_url,
            )
            if sb2["links"]:
                sub_out.append(sb2)
        sec2["subsectorBriefs"] = sub_out
        sectors_out.append(sec2)
    out["sectorDeepBriefs"] = sectors_out

    desk_out: list[dict[str, Any]] = []
    for grp in out.get("sourceDesk") or []:
        if not isinstance(grp, dict):
            continue
        g2 = dict(grp)
        theme = str(g2.get("theme") or g2.get("topic") or "").strip()
        links = g2.get("links") if isinstance(g2.get("links"), list) else []
        if theme and links:
            g2["links"] = _filter_story_links(
                links, headline=theme, context=theme, index=index, by_url=by_url
            )
        if g2.get("links"):
            desk_out.append(g2)
    out["sourceDesk"] = desk_out

    return out


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "content.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    cleaned = sanitize_newsroom_public_content(data)
    path.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: sanitized {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
