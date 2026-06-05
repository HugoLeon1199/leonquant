#!/usr/bin/env python3
"""Tone down newsroom copy — less hype, more cautious Vietnamese."""

from __future__ import annotations

import re

_HEADLINE_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"^dòng vốn dịch chuyển từ crypto sang cổ phiếu ai\.?$",
            re.I,
        ),
        "Tài sản rủi ro phân hóa khi Bitcoin suy yếu còn nhóm AI vẫn hút chú ý",
    ),
]

_SOFTEN_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"dòng vốn dịch chuyển mạnh mẽ", re.I), "dòng chú ý thị trường nghiêng"),
    (re.compile(r"dịch chuyển mạnh mẽ của dòng vốn toàn cầu", re.I), "xu hướng thị trường gần đây"),
    (re.compile(r"dòng vốn dịch chuyển", re.I), "xu hướng tài sản"),
    (re.compile(r"dòng vốn toàn cầu", re.I), "dòng chú ý thị trường"),
    (re.compile(r"LeonQuant ghi nhận sự", re.I), "48 giờ qua cho thấy"),
    (re.compile(r"ghi nhận sự dịch chuyển mạnh mẽ", re.I), "cho thấy"),
    (re.compile(r"\btoàn cầu\b(?=.*(?:dòng|vốn|dịch chuyển))", re.I), "thị trường"),
]

_FILLER_SENTENCE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"[^.!?…\n]*\bđể người đọc\b[^.!?…\n]*[.!?…]", re.I),
    re.compile(r"[^.!?…\n]*\bbản tin này gom\b[^.!?…\n]*[.!?…]", re.I),
    re.compile(r"[^.!?…\n]*\bngười đọc cần theo dõi\b[^.!?…\n]*[.!?…]", re.I),
    re.compile(r"[^.!?…\n]*\bbiến số cần theo dõi\b[^.!?…\n]*[.!?…]", re.I),
    re.compile(r"[^.!?…\n]*\bthành từng hồ sơ\b[^.!?…\n]*[.!?…]", re.I),
    re.compile(r"[^.!?…\n]*\bphân tích sự phân hóa của dòng vốn\b[^.!?…\n]*[.!?…]", re.I),
]


def strip_newsroom_filler(text: str) -> str:
    s = str(text or "").strip()
    if not s:
        return s
    for pat in _FILLER_SENTENCE_PATTERNS:
        s = pat.sub("", s)
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"  +", " ", s)
    return s.strip()


def soften_newsroom_text(text: str) -> str:
    s = str(text or "").strip()
    if not s:
        return s
    for pat, repl in _HEADLINE_REPLACEMENTS:
        if pat.match(s):
            return repl
    for pat, repl in _SOFTEN_PATTERNS:
        s = pat.sub(repl, s)
    return s


def soften_prose(text: str) -> str:
    """Long-form digest copy: chỉ bỏ câu meta, không làm mỏng giọng văn."""
    return strip_newsroom_filler(str(text or "").strip())


def soften_editor_note(note: str) -> str:
    raw = str(note or "").strip()
    if not raw:
        return ""
    return soften_prose(raw)


def soften_headline(text: str) -> str:
    return soften_newsroom_text(str(text or "").strip())
