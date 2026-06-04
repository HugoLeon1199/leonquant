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


_DEFAULT_EDITOR_NOTE = (
    "48 giờ qua cho thấy ba trục tin nổi bật: rủi ro Trung Đông tiếp tục chi phối "
    "dầu và vàng; nhóm công nghệ lớn vẫn là tâm điểm của câu chuyện AI; còn Việt Nam "
    "tập trung vào lạm phát, pháp lý bất động sản và chính sách năng lượng. "
    "Bản tin này gom các nguồn liên quan thành từng hồ sơ để người đọc thấy rõ "
    "diễn biến, tác động và biến số cần theo dõi tiếp."
)


def soften_editor_note(note: str) -> str:
    raw = str(note or "").strip()
    if not raw:
        return _DEFAULT_EDITOR_NOTE
    s = soften_newsroom_text(raw)
    if re.search(
        r"leonquant ghi nhận|dịch chuyển mạnh|48 giờ qua.{0,40}48 giờ qua|"
        r"xu hướng thị trường gần đây từ các tài sản rủi ro",
        s,
        re.I,
    ):
        return _DEFAULT_EDITOR_NOTE
    return s
